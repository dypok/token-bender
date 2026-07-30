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
from app.services.ctranslate_service import translate_ctranslate2_batch
from app.services.semantic_cluster import cluster_by_5_intentions, INTENTION_STATES
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


def detect_product_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        low = col.lower().replace("ñ", "n").replace("ó", "o").replace("é", "e")
        if any(k in low for k in ["producto", "product", "item", "nombre", "categoria", "category"]):
            return col
    return None


def make_item(text_es: str, text_en: str, tok_es: int, tok_en: int, class_result: dict | None, frequency: int = 1, product_name: str | None = None, stars: int = 3) -> BatchResultItem:
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
        frequency=frequency, product_name=product_name, stars=stars
    )


def empty_item() -> BatchResultItem:
    return BatchResultItem(
        review="", tokens_original=0, text_en="", tokens_en=0,
        cost_original_usd=0.0, cost_en_usd=0.0, best_lang="",
        justification="", classification=None, frequency=0, product_name=None, stars=3
    )


def build_summary(results: list[BatchResultItem]) -> EconomicSummary:
    total = sum(r.frequency for r in results)
    if total == 0:
        return empty_summary()
    # Métricas basadas en la tokenización individual de la frase resumen por su frecuencia
    sum_orig = sum(r.tokens_original * r.frequency for r in results)
    sum_en = sum(r.tokens_en * r.frequency for r in results)
    avg_orig = round(sum_orig / total, 1)
    avg_en = round(sum_en / total, 1)
    daily_orig = (avg_orig / 1_000_000) * COST_PER_MILLION_TOKENS * REVIEWS_10K
    daily_en = (avg_en / 1_000_000) * COST_PER_MILLION_TOKENS * REVIEWS_10K
    daily_savings = daily_orig - daily_en
    en_better = sum(r.frequency for r in results if r.best_lang == "en")
    es_better = sum(r.frequency for r in results if r.best_lang == "es")
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


async def process_batch_dataframe(df: pd.DataFrame, text_col: str, optent_tokens: bool, deepl_api_key: str = "", task_id: str | None = None) -> BatchUploadResponse:
    prod_col = detect_product_column(df)
    
    if task_id:
        add_log(task_id, f"Clasificando reseñas en 5 Estados de Intención por producto...")

    start_time = time.time()
    
    # 1. Agrupar reseñas en los 5 Estados de Intención por Producto
    grouped_clusters = []
    if prod_col:
        for prod_name, sub_df in df.groupby(prod_col):
            sub_texts = [str(t) if pd.notna(t) else "" for t in sub_df[text_col]]
            sub_texts = [t.strip() for t in sub_texts if t.strip()]
            clusters = cluster_by_5_intentions(sub_texts)
            for c in clusters:
                c["product_name"] = str(prod_name)
            grouped_clusters.extend(clusters)
    else:
        raw_texts = [str(t) if pd.notna(t) else "" for t in df[text_col]]
        clean_texts = [t.strip() for t in raw_texts if t.strip()]
        clusters = cluster_by_5_intentions(clean_texts)
        for c in clusters:
            c["product_name"] = "General"
        grouped_clusters.extend(clusters)

    if task_id:
        add_log(task_id, f"Agrupamiento completado: {len(grouped_clusters)} estados de intención identificados en {len(df)} reseñas.")
        add_log(task_id, f"Traduciendo {len(grouped_clusters)} resúmenes únicos con CTranslate2 C++...")

    # 2. Traducir ÚNICAMENTE las 5 frases resumen canónicas por producto
    canonical_texts = [c["canonical_es"] for c in grouped_clusters]
    translations = await translate_ctranslate2_batch(canonical_texts)

    # 3. Clasificación rápida por palabras clave sobre los resúmenes
    from app.services.classifier import classify_batch_fast
    classify_inputs = translations if optent_tokens else canonical_texts
    class_results = classify_batch_fast(classify_inputs)

    # 4. Construir resultados agregados por Estado de Intención
    results = []
    product_star_totals = {}
    product_counts = {}

    for cluster, trans, cr in zip(grouped_clusters, translations, class_results):
        canon_es = cluster["canonical_es"]
        count = cluster["count"]
        prod = cluster.get("product_name", "General")
        stars = cluster["stars"]
        
        # Gasto de tokens basado ÚNICAMENTE en la reseña resumen traducida única
        orig_tokens = count_tokens(canon_es)
        en_tokens = count_tokens(trans)
        
        item = make_item(
            text_es=canon_es,
            text_en=trans,
            tok_es=orig_tokens,
            tok_en=en_tokens,
            class_result=cr,
            frequency=count,
            product_name=prod,
            stars=stars
        )
        results.append(item)

        # Acumular para el rating promedio del producto
        product_star_totals[prod] = product_star_totals.get(prod, 0) + (stars * count)
        product_counts[prod] = product_counts.get(prod, 0) + count

    # Calcular rating promedio (1.00 a 5.00 ⭐) por producto
    product_ratings = {
        p: round(product_star_totals[p] / max(1, product_counts[p]), 2)
        for p in product_counts
    }

    total_elapsed = time.time() - start_time
    total_rate = len(df) / max(0.1, total_elapsed)

    if task_id:
        add_log(task_id, f"Procesamiento completado en {total_elapsed:.2f}s (Rendimiento efectivo: {total_rate:.1f} reseña/s).")

    summary = build_summary(results)
    return BatchUploadResponse(results=results, economic_summary=summary, product_ratings=product_ratings)


async def run_batch_background_bytes(task_id: str, content: bytes, filename: str, optent_tokens: bool, deepl_api_key: str):
    add_log(task_id, f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    add_log(task_id, f"Iniciando procesamiento batch (5 Estados de Intención + CTranslate2)...")
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
        add_log(task_id, f"Resumen: {summary.total_reviews} reseñas en {len(response.results)} estados, ahorro mensual estimado: ${summary.monthly_savings_10k}")
        add_log(task_id, "Proceso completado.")
        set_result(task_id, response)
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        add_log(task_id, f"ERROR: {e}")
        add_log(task_id, f"TRACEBACK: {tb}")
        set_result(task_id, None)
