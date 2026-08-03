import pandas as pd

_TEXT_HINTS = ["review", "reseña", "rese", "text", "feedback", "coment"]
_PRODUCT_HINTS = ["producto", "product", "item", "nombre", "categoria", "category"]


def _normalize(col: str) -> str:
    return (
        col.lower()
        .replace("ñ", "n")
        .replace("ó", "o")
        .replace("é", "e")
    )


def detect_text_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        low = _normalize(col)
        if any(k in low for k in _TEXT_HINTS):
            return col
    return df.columns[0] if len(df.columns) > 0 else None


def detect_product_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        low = _normalize(col)
        if any(k in low for k in _PRODUCT_HINTS):
            return col
    return None
