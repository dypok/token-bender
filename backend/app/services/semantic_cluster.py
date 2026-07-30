import re
from typing import List, Dict, Tuple
from collections import defaultdict


INTENTION_STATES = {
    1: {"name": "1 ⭐ - Muy Malo", "stars": 1, "keywords": ["cierra", "crashea", "explota", "muere", "cierre", "crash", "inusable", "pésima", "pésimo", "terrible", "horrible", "inútil", "basura", "estafa"]},
    2: {"name": "2 ⭐ - Malo", "stars": 2, "keywords": ["bug", "error", "fallo", "falla", "red", "wifi", "conexion", "internet", "servidor", "login", "pago", "pagar", "tarjeta", "sesión"]},
    3: {"name": "3 ⭐ - Aceptable", "stars": 3, "keywords": ["lenta", "lento", "tilda", "congela", "cargando", "pantalla", "botón", "interfaz", "ui", "regular", "normal", "pesada", "aceptable"]},
    4: {"name": "4 ⭐ - Bueno", "stars": 4, "keywords": ["bueno", "buena", "útil", "bien", "mejora", "funciona", "sugerencia", "podría", "detalles"]},
    5: {"name": "5 ⭐ - Muy Bueno", "stars": 5, "keywords": ["excelente", "genial", "fantástico", "increíble", "me encanta", "perfecto", "super", "buenísimo", "maravilla", "10/10", "top"]}
}


def classify_intention_state(text: str) -> int:
    """
    Clasifica una reseña individual en uno de los 5 estados de intención (1-5 estrellas).
    """
    text_lower = text.lower()
    
    # 1. Buscar coincidencias en orden de prioridad (Crashes -> Errores -> Performance -> Positivo)
    for stars in [1, 2, 3, 5, 4]:
        keywords = INTENTION_STATES[stars]["keywords"]
        if any(k in text_lower for k in keywords):
            return stars
            
    # Default si no coincide palabra clave: 3 estrellas (Aceptable)
    return 3


def extract_core_phrase(text: str) -> str:
    """
    Extrae la primera cláusula u oración relevante recortando relleno secundario o ruido.
    """
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


def cluster_by_5_intentions(texts: List[str]) -> List[Dict]:
    """
    Agrupa una lista de reseñas de un producto en los 5 estados de intención (1-5 estrellas)
    y selecciona 1 frase resumen canónica para cada estado presente.
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
            
        # Extraer frases núcleo y buscar la más representativa (frecuente o limpia)
        core_counts = defaultdict(int)
        raw_map = {}
        for txt in group_texts:
            core = extract_core_phrase(txt)
            norm = re.sub(r'[^\w\s]', '', core.lower()).strip()
            core_counts[norm] += 1
            if norm not in raw_map:
                raw_map[norm] = core
                
        # Elegir la frase núcleo más común del estado
        best_norm = max(core_counts.keys(), key=lambda k: core_counts[k])
        best_canonical = raw_map[best_norm]

        clusters.append({
            "stars": stars,
            "state_name": INTENTION_STATES[stars]["name"],
            "canonical_es": best_canonical,
            "count": len(group_texts),
            "original_texts": group_texts
        })

    return clusters
