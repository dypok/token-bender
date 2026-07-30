import pandas as pd
import asyncio
import time
from datetime import datetime
import io
from fastapi import UploadFile
from app.models.schemas import (
    BatchResultItem, BatchUploadResponse,
    Classification, EconomicSummary, COST_PER_MILLION_TOKENS
)
from app.services.tokenizer import count_tokens
from app.services.classifier import classify
from app.services.ctranslate_service import translate_ctranslate2_batch
from app.batch_tasks import add_log, set_result

REVIEWS_10K = 10000


def read_df_from_file(file: UploadFile) -> pd.DataFrame:
    filename = file.filename or ""
    if filename.endswith(".csv"):
        return pd.read_csv(file.file)
    return pd.read_excel(file.file)


def detect_text_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        low = col.lower().replace("ñ", "n")
        if any(k in low for k in ["review", "reseña", "rese", "text", "feedback", "coment"]):
            return col
    return df.columns[0] if len(df.columns) > 0 else None


def make_item(text_es: str, text_en: str, tok_es: int, tok_en: int, class_result: dict | None) -> BatchResultItem:
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


def empty_item() -> BatchResultItem:
    return BatchResultItem(
        review="", tokens_original=0, text_en="", tokens_en=0,
        cost_original_usd=0.0, cost_en_usd=0.0, best_lang="",
        justification="", classification=None,
    )


def build_summary(results: list[BatchResultItem]) -> EconomicSummary:
    total = len(results)
    if total == 0:
        return empty_summary()
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


def empty_summary() -> EconomicSummary:
    return EconomicSummary(
        total_reviews=0, total_tokens_original=0, total_tokens_en=0,
        avg_tokens_original=0.0, avg_tokens_en=0.0,
        daily_cost_original_10k=0.0, daily_cost_en_10k=0.0,
        daily_savings_10k=0.0, weekly_savings_10k=0.0, monthly_savings_10k=0.0,
        best_global_lang="es",
    )


import re

def _normalize_key(text: str) -> str:
    # Normalización rápida: minúsculas, elimina puntuación repetida y espacios extras
    clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
    return clean if clean else text.lower().strip()


async def process_batch_dataframe(df: pd.DataFrame, text_col: str, optent_tokens: bool, deepl_api_key: str = "", task_id: str | None = None) -> BatchUploadResponse:
    raw_texts = [str(t) if pd.notna(t) else "" for t in df[text_col]]
    clean_texts = [t.strip() for t in raw_texts if t.strip()]

    # Deduplicación inteligente con clave de normalización
    norm_to_original: dict[str, str] = {}
    for t in clean_texts:
        k = _normalize_key(t)
        if k not in norm_to_original:
            norm_to_original[k] = t

    uniques = list(norm_to_original.values())

    if task_id:
        savings_count = len(clean_texts) - len(uniques)
        add_log(task_id, f"Deduplicación inteligente completada: {len(uniques)} patrones únicos de {len(clean_texts)} totales (Ahorro del {(savings_count / max(1, len(clean_texts))) * 100:.1f}% en llamadas).")
        add_log(task_id, f"Traduciendo {len(uniques)} patrones únicos con inferencia vectorial MarianMT C++ en lotes de 2048...")

    start_time = time.time()
    batch_chunk_size = 2048
    translations = []

    for i in range(0, len(uniques), batch_chunk_size):
        chunk = uniques[i : i + batch_chunk_size]
        chunk_trans = await translate_ctranslate2_batch(chunk)
        translations.extend(chunk_trans)

        if task_id:
            completed = min(i + batch_chunk_size, len(uniques))
            elapsed = time.time() - start_time
            rate = completed / max(0.1, elapsed)
            remaining = (len(uniques) - completed) / max(0.1, rate)
            add_log(task_id, f"  ✓ Únicas procesadas: {completed}/{len(uniques)} ({rate:.1f} req/s) - Tiempo est. restante: {remaining:.1f}s")

    # Clasificación rápida vectorizada en bloque para todas las frases únicas
    classify_inputs = translations if optent_tokens else uniques
    from app.services.classifier import classify_batch_fast
    class_results = classify_batch_fast(classify_inputs)

    # Mapear tanto la clave exacta como la clave normalizada
    norm_cache = {}
    for txt, trans, cr in zip(uniques, translations, class_results):
        item = make_item(txt, trans, count_tokens(txt), count_tokens(trans), cr)
        norm_cache[_normalize_key(txt)] = item

    results = []
    for t in raw_texts:
        t_clean = t.strip()
        if not t_clean:
            results.append(empty_item())
        else:
            norm_k = _normalize_key(t_clean)
            if norm_k in norm_cache:
                base_item = norm_cache[norm_k]
                # Preservar el texto original de la fila específica en el objeto de resultado
                results.append(make_item(t_clean, base_item.text_en, count_tokens(t_clean), base_item.tokens_en, base_item.classification.model_dump() if base_item.classification else None))
            else:
                results.append(empty_item())

    total_elapsed = time.time() - start_time
    total_rate = len(df) / max(0.1, total_elapsed)

    if task_id:
        add_log(task_id, f"Procesamiento completado en {total_elapsed:.2f}s (Rendimiento efectivo: {total_rate:.1f} reseña/s).")

    summary = build_summary(results)
    return BatchUploadResponse(results=results, economic_summary=summary)


async def run_batch_background_bytes(task_id: str, content: bytes, filename: str, optent_tokens: bool, deepl_api_key: str):
    add_log(task_id, f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    add_log(task_id, f"Iniciando procesamiento batch (engine=ctranslate2)...")
    add_log(task_id, f"Leyendo archivo: {filename}")
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(content))
        else:
            df = pd.read_excel(io.BytesIO(content))
        text_col = detect_text_column(df)
        add_log(task_id, f"Archivo cargado: {len(df)} filas, columna texto: '{text_col}'")

        response = await process_batch_dataframe(df, text_col, optent_tokens, deepl_api_key, task_id=task_id)
        summary = response.economic_summary
        add_log(task_id, f"Resumen: {summary.total_reviews} reseñas, ahorro mensual estimado: ${summary.monthly_savings_10k}")
        add_log(task_id, "Proceso completado.")
        set_result(task_id, response)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        add_log(task_id, f"ERROR: {e}")
        add_log(task_id, f"TRACEBACK: {tb}")
        set_result(task_id, None)
