INTENTION_LABELS = {
    1: "1 Estrella ⭐ (Muy Malo)",
    2: "2 Estrellas ⭐⭐ (Malo)",
    3: "3 Estrellas ⭐⭐⭐ (Aceptable)",
    4: "4 Estrellas ⭐⭐⭐⭐ (Bueno)",
    5: "5 Estrellas ⭐⭐⭐⭐⭐ (Muy Bueno)"
}

INTENTION_KEYWORDS = {
    1: [
        "cierra", "crashea", "explota", "muere", "cierre", "crash", "inusable",
        "pésima", "pésimo", "terrible", "horrible", "inútil", "basura", "estafa",
        "porquería", "dinero tirado", "peor", "asco", "defectuoso", "no sirve"
    ],
    2: [
        "bug", "error", "fallo", "falla", "red", "wifi", "conexion", "internet",
        "servidor", "login", "pago", "pagar", "tarjeta", "sesión", "no me gustó",
        "esperaba más", "mala calidad", "malo", "mala", "defecto", "no abre",
        "problema", "dañado", "decepcion", "decepción"
    ],
    3: [
        "lenta", "lento", "tilda", "congela", "cargando", "pantalla", "botón",
        "interfaz", "ui", "regular", "normal", "pesada", "aceptable", "más o menos",
        "mediocre", "cumple a medias", "regularcito", "regularcita"
    ],
    4: [
        "bueno", "buena", "útil", "bien", "mejora", "funciona", "sugerencia",
        "podría", "detalles", "bonito", "bonita", "recomendable", "cumple",
        "me sirvió", "satisfecho", "satisfecha"
    ],
    5: [
        "excelente", "genial", "fantástico", "increíble", "me encanta", "perfecto",
        "perfecta", "super", "buenísimo", "buenísima", "maravilla", "10/10", "top",
        "encantado", "encantada", "magnífico", "magnífica", "lo mejor"
    ]
}

# Orden de prioridad: las intenciones más graves/impactantes se evalúan primero
_PRIORITY_ORDER = [1, 5, 2, 4, 3]

_POSITIVE_HINTS = ["gran", "buen", "excelent", "gust"]
_NEGATIVE_HINTS = ["no ", "sin ", "mal", "pésim"]


def classify_intention_state(text: str) -> int:
    """Clasifica una reseña en una de las 5 intenciones (1-5 estrellas)."""
    text_lower = text.lower()

    for stars in _PRIORITY_ORDER:
        keywords = INTENTION_KEYWORDS[stars]
        if any(k in text_lower for k in keywords):
            return stars

    if any(neg in text_lower for neg in _NEGATIVE_HINTS):
        return 2
    if any(pos in text_lower for pos in _POSITIVE_HINTS):
        return 4

    return 3
