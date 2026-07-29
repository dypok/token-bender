import os
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Header, Form
from app.models.schemas import (
    BatchFolderRequest, ProjectionRequest,
    ProjectionResponse, BatchResultItem, BatchUploadResponse,
    Classification, EconomicSummary,
)
from app.services.tokenizer import count_tokens
from app.services.translator import translate
from app.services.classifier import classify

router = APIRouter()

COST_PER_MILLION = 2.5
REVIEWS_PER_DAY_BENCHMARK = 10000


@router.post("/api/batch/upload", response_model=BatchUploadResponse)
async def batch_upload(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
    engine: str = Form("ollama"),
    deepl_api_key: str = Header(default=""),
):
    df = pd.read_excel(file.file)
    text_col = _detect_text_column(df)
    results = []
    total_original_tokens = 0
    for text in df[text_col]:
        text_str = str(text) if pd.notna(text) else ""
        if not text_str.strip():
            continue
        orig_tokens = count_tokens(text_str)
        total_original_tokens += orig_tokens
        if optent_tokens:
            translated, _ = await translate(text_str, engine, deepl_api_key=deepl_api_key)
            text_for_llm = translated
            tokens = count_tokens(translated)
        else:
            text_for_llm = text_str
            tokens = orig_tokens
        class_result, _ = await classify(text_for_llm, engine, deepl_api_key)
        results.append(BatchResultItem(
            review=text_str,
            tokens=tokens,
            classification=Classification(**class_result),
        ))
    summary = _build_summary(results, total_original_tokens)
    return BatchUploadResponse(results=results, economic_summary=summary)


@router.post("/api/batch/folder", response_model=BatchUploadResponse)
async def batch_folder(req: BatchFolderRequest, deepl_api_key: str = Header(default="")):
    folder = req.folder_path
    if not os.path.isdir(folder):
        return BatchUploadResponse(results=[], economic_summary=_empty_summary())

    all_dfs = []
    for fname in os.listdir(folder):
        if fname.endswith(".xlsx"):
            df = pd.read_excel(os.path.join(folder, fname))
            all_dfs.append(df)

    if not all_dfs:
        return BatchUploadResponse(results=[], economic_summary=_empty_summary())
    df = pd.concat(all_dfs, ignore_index=True)
    text_col = _detect_text_column(df)
    results = []
    total_original_tokens = 0
    for text in df[text_col]:
        text_str = str(text) if pd.notna(text) else ""
        if not text_str.strip():
            continue
        orig_tokens = count_tokens(text_str)
        total_original_tokens += orig_tokens
        if req.optent_tokens:
            translated, _ = await translate(text_str, req.engine, deepl_api_key=deepl_api_key)
            text_for_llm = translated
            tokens = count_tokens(translated)
        else:
            text_for_llm = text_str
            tokens = orig_tokens
        class_result, _ = await classify(text_for_llm, req.engine, deepl_api_key)
        results.append(BatchResultItem(
            review=text_str,
            tokens=tokens,
            classification=Classification(**class_result),
        ))
    summary = _build_summary(results, total_original_tokens)
    return BatchUploadResponse(results=results, economic_summary=summary)


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


def _build_summary(results: list[BatchResultItem], total_original_tokens: int) -> EconomicSummary:
    total = len(results)
    if total == 0:
        return _empty_summary()
    total_tokens = sum(r.tokens for r in results)
    avg = round(total_tokens / total, 1)
    
    avg_original = total_original_tokens / total
    avg_optimized = total_tokens / total
    avg_diff = max(0.0, avg_original - avg_optimized)
    
    daily_10k = avg_optimized * REVIEWS_PER_DAY_BENCHMARK
    monthly_10k = daily_10k * 30
    
    daily_savings_tokens = avg_diff * REVIEWS_PER_DAY_BENCHMARK
    monthly_savings_tokens = daily_savings_tokens * 30
    savings = round((monthly_savings_tokens / 1_000_000) * COST_PER_MILLION, 2)
    
    return EconomicSummary(
        total_reviews=total,
        total_tokens_processed=total_tokens,
        projected_daily_tokens_10k=round(daily_10k),
        projected_monthly_tokens_10k=round(monthly_10k),
        projected_monthly_savings_usd_10k=savings,
        avg_tokens_per_review=avg,
    )


def _empty_summary() -> EconomicSummary:
    return EconomicSummary(
        total_reviews=0,
        total_tokens_processed=0,
        projected_daily_tokens_10k=0,
        projected_monthly_tokens_10k=0,
        projected_monthly_savings_usd_10k=0.0,
        avg_tokens_per_review=0.0,
    )


def _detect_text_column(df: pd.DataFrame) -> str:
    for col in df.columns:
        low = col.lower().replace("ñ", "n")
        if any(k in low for k in ["review", "reseña", "rese", "text", "feedback", "coment"]):
            return col
    return df.columns[0]
