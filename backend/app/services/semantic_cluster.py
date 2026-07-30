import re
from typing import List, Dict
from collections import defaultdict


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


def classify_intention_state(text: str) -> int:
    text_lower = text.lower()
    
    # 1. Probar en orden explícito de mayor a menor gravedad / impacto
    for stars in [1, 5, 2, 4, 3]:
        keywords = INTENTION_KEYWORDS[stars]
        if any(k in text_lower for k in keywords):
            return stars
            
    # 2. Análisis heurístico secundario si no coincide keyword exacta
    if any(neg in text_lower for neg in ["no ", "sin ", "mal", "pésim"]):
        return 2
    if any(pos in text_lower for pos in ["gran", "buen", "excelent", "gust"]):
        return 4
        
    return 3


def extract_core_phrase(text: str) -> str:
    if not text:
        return ""
    clauses = re.split(r'[;\.\n\r]|\b(pero|aunque|sin embargo)\b', text, flags=re.IGNORECASE)
    for clause in clauses:
        if clause and len(clause.strip()) > 3:
            clean = clause.strip()
            words = clean.split()
            if len(words) > 10:
                sub_parts = clean.split(',')
                if sub_parts and len(sub_parts[0].strip()) > 5:
                    return sub_parts[0].strip()
            return clean
    return text.strip()


def cluster_by_exact_5_intentions(texts: List[str]) -> List[Dict]:
    """
    Agrupa todo el universo de reseñas en exactamente hasta 5 intenciones por producto.
    """
    state_groups: Dict[int, List[str]] = defaultdict(list)
    
    for t in texts:
        t_clean = t.strip()
        if not t_clean:
            continue
        stars = classify_intention_state(t_clean)
        state_groups[stars].append(t_clean)

    clusters = []
    for stars in range(1, 6):
        group_texts = state_groups[stars]
        if not group_texts:
            continue
            
        core_counts = defaultdict(int)
        raw_map = {}
        for txt in group_texts:
            core = extract_core_phrase(txt)
            norm = re.sub(r'[^\w\s]', '', core.lower()).strip()
            core_counts[norm] += 1
            if norm not in raw_map:
                raw_map[norm] = core
                
        best_norm = max(core_counts.keys(), key=lambda k: core_counts[k])
        best_canonical = raw_map[best_norm]

        clusters.append({
            "stars": stars,
            "state_label": INTENTION_LABELS[stars],
            "canonical_es": best_canonical,
            "count": len(group_texts),
            "original_texts": group_texts
        })

    return clusters
