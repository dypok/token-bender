import os
import asyncio
import json
import pandas as pd
from fastapi import APIRouter, UploadFile, File, Header, Form, HTTPException
from pydantic import BaseModel
from app.models.schemas import (
    BatchFolderRequest, ProjectionRequest,
    ProjectionResponse, BatchResultItem, BatchUploadResponse,
    Classification, EconomicSummary, COST_PER_MILLION_TOKENS,
)
from app.services.tokenizer import count_tokens
from app.services.translator import translate
from app.services.classifier import classify, classify_combined
from app.services.argos_translate import batch_translate as argos_batch
from app.batch_tasks import create_task, add_log, get_logs, set_result, get_result, is_done

router = APIRouter()
REVIEWS_10K = 10000
GROUP_CONCURRENCY = 5


class ProgressResponse(BaseModel):
    logs: list[str]
    done: bool
    result: BatchUploadResponse | None = None


@router.post("/api/batch/upload", response_model=BatchUploadResponse)
async def batch_upload(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
    engine: str = Form("ollama"),
    deepl_api_key: str = Header(default=""),
):
    df = _read_file(file)
    text_col = _detect_text_column(df)

    if engine == "argos" and text_col is not None:
        return await _process_with_argos(df, text_col, optent_tokens)

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

    if req.engine == "argos" and text_col is not None:
        return await _process_with_argos(df, text_col, req.optent_tokens)

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


async def _process_with_argos(df: pd.DataFrame, text_col: str, optent_tokens: bool) -> BatchUploadResponse:
    prod_col = _detect_product_column(df)

    if prod_col and optent_tokens:
        groups = df.groupby(prod_col)
        group_tasks = []
        for prod_name, group_df in groups:
            texts = [str(t) if pd.notna(t) else "" for t in group_df[text_col]]
            texts = [t.strip() for t in texts if t.strip()]
            if texts:
                group_tasks.append(_process_group(texts, prod_name))
        group_concurrency = min(GROUP_CONCURRENCY, len(group_tasks))
        sem = asyncio.Semaphore(group_concurrency)

        async def run_group(task):
            async with sem:
                return await task

        nested = await asyncio.gather(*[run_group(t) for t in group_tasks])
        results = [item for batch_list in nested for item in batch_list]
    else:
        texts = [str(t) if pd.notna(t) else "" for t in df[text_col]]
        texts = [t.strip() for t in texts if t.strip()]
        results = await _process_flat_batch(texts)

    summary = _build_summary(results)
    return BatchUploadResponse(results=results, economic_summary=summary)


@router.post("/api/batch/start")
async def batch_start(
    file: UploadFile = File(...),
    optent_tokens: bool = Form(True),
    engine: str = Form("ollama"),
    deepl_api_key: str = Header(default=""),
):
    task_id = create_task()
    asyncio.create_task(_run_batch_background(task_id, file, optent_tokens, engine, deepl_api_key))
    return {"task_id": task_id}


@router.get("/api/batch/progress/{task_id}", response_model=ProgressResponse)
async def batch_progress(task_id: str):
    result = get_result(task_id)
    return ProgressResponse(
        logs=get_logs(task_id),
        done=is_done(task_id),
        result=result,
    )


async def _run_batch_background(task_id: str, file: UploadFile, optent_tokens: bool, engine: str, deepl_api_key: str):
    add_log(task_id, f"Iniciando procesamiento batch (engine={engine})...")
    add_log(task_id, f"Leyendo archivo: {file.filename}")
    try:
        df = _read_file(file)
        text_col = _detect_text_column(df)
        add_log(task_id, f"Archivo cargado: {len(df)} filas, columna texto: '{text_col}'")

        if engine == "argos" and text_col is not None:
            prod_col = _detect_product_column(df)
            if prod_col:
                add_log(task_id, f"Columna producto detectada: '{prod_col}' - agrupando...")
                groups = df.groupby(prod_col)
                add_log(task_id, f"Total grupos: {len(groups)}")

                group_tasks = []
                for prod_name, group_df in groups:
                    texts = [str(t) if pd.notna(t) else "" for t in group_df[text_col]]
                    texts = [t.strip() for t in texts if t.strip()]
                    if texts:
                        group_tasks.append((str(prod_name), texts))
                        add_log(task_id, f"  Grupo '{prod_name}': {len(texts)} reseñas")

                sem = asyncio.Semaphore(min(GROUP_CONCURRENCY, len(group_tasks)))
                all_results = []

                async def run_group(name: str, texts: list[str]):
                    async with sem:
                        add_log(task_id, f"  → Procesando grupo '{name}' ({len(texts)} reseñas)...")
                        uniques = list(dict.fromkeys(texts))
                        add_log(task_id, f"    Textos únicos: {len(uniques)} (dedup ahorra {len(texts) - len(uniques)})")
                        add_log(task_id, f"    Traduciendo {len(uniques)} textos con Argos...")
                        translations = await asyncio.to_thread(argos_batch, uniques, "es", "en")
                        add_log(task_id, f"    Traducción completada.")
                        seen = dict(zip(uniques, translations))
                        items = []
                        for t in texts:
                            translated = seen[t]
                            orig_tokens = count_tokens(t)
                            en_tokens = count_tokens(translated)
                            class_result, _ = await classify(t, "google", "")
                            items.append(_make_item(t, translated, orig_tokens, en_tokens, class_result))
                        add_log(task_id, f"  ✓ Grupo '{name}' completado ({len(items)} reseñas)")
                        return items

                nested = await asyncio.gather(*[run_group(n, ts) for n, ts in group_tasks])
                results = [item for batch_list in nested for item in batch_list]
            else:
                add_log(task_id, "Sin columna producto - procesamiento plano...")
                results = await _process_flat_batch_logged(task_id, df, text_col)
        else:
            add_log(task_id, f"Procesando {len(df)} reseñas secuencialmente...")
            results = []
            for i, t in enumerate(df[text_col]):
                text_str = str(t) if pd.notna(t) else ""
                if not text_str.strip():
                    results.append(_empty_item())
                    continue
                if i % 10 == 0:
                    add_log(task_id, f"  Procesando reseña {i + 1}/{len(df)}...")
                item = await _process_review(text_str, engine, deepl_api_key, optent_tokens)
                results.append(item)
            add_log(task_id, f"Procesamiento completado.")

        summary = _build_summary(results)
        result = BatchUploadResponse(results=results, economic_summary=summary)
        add_log(task_id, f"Resumen: {summary.total_reviews} reseñas, ahorro mensual estimado: ${summary.monthly_savings_10k}")
        add_log(task_id, "Proceso completado.")
        set_result(task_id, result)
    except Exception as e:
        add_log(task_id, f"ERROR: {e}")
        set_result(task_id, None)


async def _process_flat_batch_logged(task_id: str, df, text_col) -> list[BatchResultItem]:
    texts = [str(t) if pd.notna(t) else "" for t in df[text_col]]
    texts = [t.strip() for t in texts if t.strip()]
    uniques = list(dict.fromkeys(texts))
    add_log(task_id, f"Textos únicos: {len(uniques)} de {len(texts)} total (dedup {len(texts) - len(uniques)})")
    add_log(task_id, f"Traduciendo {len(uniques)} textos con Argos...")
    translations = await asyncio.to_thread(argos_batch, uniques, "es", "en")
    add_log(task_id, f"Traducción completada.")
    seen = dict(zip(uniques, translations))
    results = []
    for i, t in enumerate(texts):
        translated = seen[t]
        orig_tokens = count_tokens(t)
        en_tokens = count_tokens(translated)
        class_result, _ = await classify(t, "google", "")
        results.append(_make_item(t, translated, orig_tokens, en_tokens, class_result))
    return results


async def _process_group(texts: list[str], prod_name: str) -> list[BatchResultItem]:
    seen: dict[str, str] = {}
    unique_texts: list[str] = []
    for t in texts:
        if t not in seen:
            seen[t] = ""
            unique_texts.append(t)

    translations = await asyncio.to_thread(argos_batch, unique_texts, "es", "en")
    for t, trans in zip(unique_texts, translations):
        seen[t] = trans

    results = []
    for t in texts:
        translated = seen[t]
        orig_tokens = count_tokens(t)
        en_tokens = count_tokens(translated)
        class_result, _ = await classify(t, "google", "")
        results.append(_make_item(t, translated, orig_tokens, en_tokens, class_result))
    return results


async def _process_flat_batch(texts: list[str]) -> list[BatchResultItem]:
    seen: dict[str, str] = {}
    unique_texts: list[str] = []
    for t in texts:
        if t not in seen:
            seen[t] = ""
            unique_texts.append(t)

    translations = await asyncio.to_thread(argos_batch, unique_texts, "es", "en")
    for t, trans in zip(unique_texts, translations):
        seen[t] = trans

    results = []
    for t in texts:
        translated = seen[t]
        orig_tokens = count_tokens(t)
        en_tokens = count_tokens(translated)
        class_result, _ = await classify(t, "google", "")
        results.append(_make_item(t, translated, orig_tokens, en_tokens, class_result))
    return results


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
        text_for_classify = text if engine == "google" else (translated if optent_tokens else text)
        cr, _ = await classify(text_for_classify, engine, deepl_api_key)
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
        review=text_es, tokens_original=tok_es, text_en=text_en, tokens_en=tok_en,
        cost_original_usd=cost_es, cost_en_usd=cost_en, best_lang=best,
        justification=just, classification=classification,
    )


def _empty_item() -> BatchResultItem:
    return BatchResultItem(
        review="", tokens_original=0, text_en="", tokens_en=0,
        cost_original_usd=0.0, cost_en_usd=0.0, best_lang="",
        justification="", classification=None,
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
    return EconomicSummary(
        total_reviews=total,
        total_tokens_original=sum_orig,
        total_tokens_en=sum_en,
        avg_tokens_original=avg_orig, avg_tokens_en=avg_en,
        daily_cost_original_10k=round(daily_orig, 2),
        daily_cost_en_10k=round(daily_en, 2),
        daily_savings_10k=round(max(0, daily_savings), 2),
        weekly_savings_10k=round(max(0, daily_savings * 7), 2),
        monthly_savings_10k=round(max(0, daily_savings * 30), 2),
        best_global_lang="en" if en_better >= es_better else "es",
    )


def _empty_summary() -> EconomicSummary:
    return EconomicSummary(
        total_reviews=0, total_tokens_original=0, total_tokens_en=0,
        avg_tokens_original=0.0, avg_tokens_en=0.0,
        daily_cost_original_10k=0.0, daily_cost_en_10k=0.0,
        daily_savings_10k=0.0, weekly_savings_10k=0.0, monthly_savings_10k=0.0,
        best_global_lang="es",
    )


def _read_file(file: UploadFile) -> pd.DataFrame:
    filename = file.filename or ""
    if filename.endswith(".csv"):
        return pd.read_csv(file.file)
    return pd.read_excel(file.file)


def _detect_text_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        low = col.lower().replace("ñ", "n")
        if any(k in low for k in ["review", "reseña", "rese", "text", "feedback", "coment"]):
            return col
    return df.columns[0] if len(df.columns) > 0 else None


def _detect_product_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        low = col.lower().replace("ñ", "n").replace("ó", "o").replace("é", "e")
        if any(k in low for k in ["producto", "product", "item", "nombre", "categoria", "category"]):
            return col
    return None
