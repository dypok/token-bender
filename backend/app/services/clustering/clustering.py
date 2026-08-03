import re
from collections import defaultdict
from typing import Dict, List

from app.services.clustering.intentions import (
    INTENTION_LABELS,
    classify_intention_state,
)


def extract_core_phrase(text: str) -> str:
    """Extrae la frase principal de una reseña (primer cláusula relevante)."""
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


def _pick_canonical(group_texts: List[str]) -> str:
    """Elige la frase más frecuente dentro de un grupo como representante."""
    core_counts = defaultdict(int)
    raw_map = {}
    for txt in group_texts:
        core = extract_core_phrase(txt)
        norm = re.sub(r'[^\w\s]', '', core.lower()).strip()
        core_counts[norm] += 1
        if norm not in raw_map:
            raw_map[norm] = core

    best_norm = max(core_counts.keys(), key=lambda k: core_counts[k])
    return raw_map[best_norm]


def cluster_by_exact_5_intentions(texts: List[str]) -> List[Dict]:
    """Agrupa las reseñas en hasta 5 intenciones (1-5 estrellas).

    Cada cluster representa una intención con su frase canónica representativa.
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

        clusters.append({
            "stars": stars,
            "state_label": INTENTION_LABELS[stars],
            "canonical_es": _pick_canonical(group_texts),
            "count": len(group_texts),
            "original_texts": group_texts,
        })

    return clusters
