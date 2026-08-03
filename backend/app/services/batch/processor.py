import time
import traceback
from datetime import datetime
from typing import Iterable

import pandas as pd

from app.batch_tasks import add_log, set_result
from app.models.schemas import BatchUploadResponse
from app.services.batch.columns import detect_product_column, detect_text_column
from app.services.batch.economics import build_summary, make_item
from app.services.batch.io import read_df_from_bytes
from app.services.clustering import cluster_by_exact_5_intentions
from app.services.ctranslate_service import translate_ctranslate2_batch
from app.services.tokenizer import count_tokens

GENERAL_PRODUCT = "General"


def _clean_texts(series: pd.Series) -> list[str]:
    raw = [str(t) if pd.notna(t) else "" for t in series]
    return [t.strip() for t in raw if t.strip()]


def _build_clusters(df: pd.DataFrame, text_col: str) -> list[dict]:
    prod_col = detect_product_column(df)
    grouped_clusters = []

    if prod_col:
        for prod_name, sub_df in df.groupby(prod_col):
            texts = _clean_texts(sub_df[text_col])
            for c in cluster_by_exact_5_intentions(texts):
                c["product_name"] = str(prod_name)
                grouped_clusters.append(c)
    else:
        texts = _clean_texts(df[text_col])
        for c in cluster_by_exact_5_intentions(texts):
            c["product_name"] = GENERAL_PRODUCT
            grouped_clusters.append(c)

    return grouped_clusters


def _compute_product_ratings(clusters: list[dict]) -> dict[str, float]:
    star_totals: dict[str, int] = {}
    counts: dict[str, int] = {}

    for cluster in clusters:
        prod = cluster.get("product_name", GENERAL_PRODUCT)
        star_totals[prod] = star_totals.get(prod, 0) + (cluster["stars"] * cluster["count"])
        counts[prod] = counts.get(prod, 0) + cluster["count"]

    return {
        prod: round(star_totals[prod] / max(1, counts[prod]), 2)
        for prod in counts
    }


async def process_batch_dataframe(
    df: pd.DataFrame,
    text_col: str,
    optent_tokens: bool,
    task_id: str | None = None,
) -> BatchUploadResponse:
    if task_id:
        add_log(task_id, "Agrupando reseñas en exactamente 5 intenciones por producto...")

    start_time = time.time()
    clusters = _build_clusters(df, text_col)

    if task_id:
        add_log(task_id, f"Agrupamiento completado: {len(clusters)} intenciones identificadas en {len(df)} reseñas.")
        add_log(task_id, f"Ejecutando {len(clusters)} traducciones resumen con CTranslate2 C++...")

    canonical_texts = [c["canonical_es"] for c in clusters]
    translations = await translate_ctranslate2_batch(canonical_texts)

    results = []
    for cluster, trans in zip(clusters, translations):
        orig_tokens = count_tokens(cluster["canonical_es"])
        en_tokens = count_tokens(trans)
        results.append(make_item(
            text_es=cluster["canonical_es"],
            text_en=trans,
            tok_es=orig_tokens,
            tok_en=en_tokens,
            frequency=cluster["count"],
            product_name=cluster.get("product_name", GENERAL_PRODUCT),
            stars=cluster["stars"],
        ))

    total_elapsed = time.time() - start_time
    total_rate = len(df) / max(0.1, total_elapsed)

    if task_id:
        add_log(task_id, f"Procesamiento completado en {total_elapsed:.2f}s (Rendimiento efectivo: {total_rate:.1f} reseña/s).")

    return BatchUploadResponse(
        results=results,
        economic_summary=build_summary(results),
        product_ratings=_compute_product_ratings(clusters),
    )


async def run_batch_background_bytes(task_id: str, content: bytes, filename: str, optent_tokens: bool):
    add_log(task_id, f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    add_log(task_id, "Iniciando procesamiento batch (5 Intenciones por Producto + CTranslate2)...")
    add_log(task_id, f"Leyendo archivo: {filename}")
    try:
        df = read_df_from_bytes(content, filename)
        text_col = detect_text_column(df)
        add_log(task_id, f"Archivo cargado: {len(df)} filas, columna texto: '{text_col}'")

        response = await process_batch_dataframe(df, text_col, optent_tokens, task_id=task_id)
        summary = response.economic_summary
        add_log(task_id, f"Resumen: {summary.total_reviews} reseñas en {len(response.results)} intenciones, ahorro mensual estimado: ${summary.monthly_savings_10k}")
        add_log(task_id, "Proceso completado.")
        set_result(task_id, response)
    except Exception as e:
        add_log(task_id, f"ERROR: {e}")
        add_log(task_id, f"TRACEBACK: {traceback.format_exc()}")
        set_result(task_id, None)
