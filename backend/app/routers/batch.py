import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Header, Form
from app.models.schemas import (
    BatchFolderRequest, ProjectionRequest,
    ProjectionResponse, BatchResultItem, BatchUploadResponse,
    Classification, EconomicSummary, COST_PER_MILLION_TOKENS,
)
from app.services.tokenizer import count_tokens
from app.services.translator import translate
from app.services.classifier import classify, classify_combined

router = APIRouter()
REVIEWS_10K = 10000


@router.post("/api/batch/upload", response_model=BatchUploadResponse)
async def batch_upload(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
    engine: str = Form("ollama"),
    deepl_api_key: str = Header(default=""),
):
    df = _read_file(file)
    text_col = _detect_text_column(df)
    results = []
    for t in df[text_col]:
        text_str = str(t) if pd.notna(t) else ""
        if not text_str.strip():
            results.append(_empty_item())
            continue
        item = await _process_review(text_str, engine, deepl_api_key, optent_tokens)
        results.append(item)
    summary = _build_summary(results)
    return BatchUploadResponse(results=results, economic_summary=summary)


@router.post("/api/batch/folder", response_model=BatchUploadResponse)
async def batch_folder(req: BatchFolderRequest, deepl_api_key: str = Header(default="")):
    folder = req.folder_path
    if not os.path.isdir(folder):
        return BatchUploadResponse(results=[], economic_summary=_empty_summary())

    all_dfs = []
    for fname in os.listdir(folder):
        if fname.endswith((".xlsx", ".csv")):
            path = os.path.join(folder, fname)
            if fname.endswith(".csv"):
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            all_dfs.append(df)

    if not all_dfs:
        return BatchUploadResponse(results=[], economic_summary=_empty_summary())

    df = pd.concat(all_dfs, ignore_index=True)
    text_col = _detect_text_column(df)
    results = []
    for t in df[text_col]:
        text_str = str(t) if pd.notna(t) else ""
        if not text_str.strip():
            results.append(_empty_item())
            continue
        item = await _process_review(text_str, req.engine, deepl_api_key, req.optent_tokens)
        results.append(item)
    summary = _build_summary(results)
    return BatchUploadResponse(results=results, economic_summary=summary)


async def _process_review(text: str, engine: str, deepl_api_key: str, optent_tokens: bool) -> BatchResultItem:
    orig_tokens = count_tokens(text)

    translated = None
    class_result = None

    if engine == "ollama" and optent_tokens:
        combined = await classify_combined(text)
        if combined and combined.get("translation") and combined.get("error_type") and combined.get("component"):
            translated = combined["translation"]
            class_result = {"error_type": combined["error_type"], "component": combined["component"]}

    if translated is None:
        translated, _ = await translate(text, engine, deepl_api_key=deepl_api_key)
        text_for_llm = translated if optent_tokens else text
        cr, _ = await classify(text_for_llm, engine, deepl_api_key)
        class_result = cr

    en_tokens = count_tokens(translated)
    return _make_item(text, translated, orig_tokens, en_tokens, class_result)


@router.post("/api/analyze/projection", response_model=ProjectionResponse)
def projection(req: ProjectionRequest):
    diff_per_review = req.tokens_original - req.tokens_translated
    daily_diff = diff_per_review * req.reviews_per_day
    monthly_diff = daily_diff * req.days
    savings = (monthly_diff / 1_000_000) * req.cost_per_million_tokens_usd
    return ProjectionResponse(
        daily_token_diff=daily_diff,
        monthly_token_diff=monthly_diff,
        monthly_savings_usd=round(savings, 2),
    )


def _empty_item() -> BatchResultItem:
    return BatchResultItem(
        review="",
        tokens_original=0,
        text_en="",
        tokens_en=0,
        cost_original_usd=0.0,
        cost_en_usd=0.0,
        best_lang="",
        justification="",
        classification=None,
    )


def _make_item(text_es: str, text_en: str, tok_es: int, tok_en: int, class_result: dict | None) -> BatchResultItem:
    cost_es = round((tok_es / 1_000_000) * COST_PER_MILLION_TOKENS, 6)
    cost_en = round((tok_en / 1_000_000) * COST_PER_MILLION_TOKENS, 6)
    diff = tok_en - tok_es

    if diff < 0:
        best = "en"
        just = f"Inglés tiene {abs(diff)} tokens menos que español (${abs(round(cost_en - cost_es, 6))} más barato)"
    elif diff > 0:
        best = "es"
        just = f"Español tiene {diff} tokens menos que inglés (${abs(round(cost_es - cost_en, 6))} más barato)"
    else:
        best = "igual"
        just = "Ambos idiomas tienen el mismo costo de tokens"

    classification = None
    if class_result and class_result.get("error_type") and class_result.get("component"):
        classification = Classification(**class_result)

    return BatchResultItem(
        review=text_es,
        tokens_original=tok_es,
        text_en=text_en,
        tokens_en=tok_en,
        cost_original_usd=cost_es,
        cost_en_usd=cost_en,
        best_lang=best,
        justification=just,
        classification=classification,
    )


def _build_summary(results: list[BatchResultItem]) -> EconomicSummary:
    total = len(results)
    if total == 0:
        return _empty_summary()

    sum_orig = sum(r.tokens_original for r in results)
    sum_en = sum(r.tokens_en for r in results)
    avg_orig = round(sum_orig / total, 1)
    avg_en = round(sum_en / total, 1)

    daily_orig = (avg_orig / 1_000_000) * COST_PER_MILLION_TOKENS * REVIEWS_10K
    daily_en = (avg_en / 1_000_000) * COST_PER_MILLION_TOKENS * REVIEWS_10K
    daily_savings = daily_orig - daily_en

    en_better = sum(1 for r in results if r.best_lang == "en")
    es_better = sum(1 for r in results if r.best_lang == "es")
    best_global = "en" if en_better >= es_better else "es"

    return EconomicSummary(
        total_reviews=total,
        total_tokens_original=sum_orig,
        total_tokens_en=sum_en,
        avg_tokens_original=avg_orig,
        avg_tokens_en=avg_en,
        daily_cost_original_10k=round(daily_orig, 2),
        daily_cost_en_10k=round(daily_en, 2),
        daily_savings_10k=round(max(0, daily_savings), 2),
        weekly_savings_10k=round(max(0, daily_savings * 7), 2),
        monthly_savings_10k=round(max(0, daily_savings * 30), 2),
        best_global_lang=best_global,
    )


def _empty_summary() -> EconomicSummary:
    return EconomicSummary(
        total_reviews=0,
        total_tokens_original=0,
        total_tokens_en=0,
        avg_tokens_original=0.0,
        avg_tokens_en=0.0,
        daily_cost_original_10k=0.0,
        daily_cost_en_10k=0.0,
        daily_savings_10k=0.0,
        weekly_savings_10k=0.0,
        monthly_savings_10k=0.0,
        best_global_lang="es",
    )


def _read_file(file: UploadFile) -> pd.DataFrame:
    filename = file.filename or ""
    if filename.endswith(".csv"):
        return pd.read_csv(file.file)
    return pd.read_excel(file.file)


def _detect_text_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        low = col.lower().replace("ñ", "n")
        if any(k in low for k in ["review", "reseña", "rese", "text", "feedback", "coment"]):
            return col
    return df.columns[0]
