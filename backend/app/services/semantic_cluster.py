import re
from typing import List, Dict, Tuple
from collections import defaultdict


def extract_core_phrase(text: str) -> str:
    """
    Extrae la primera cláusula u oración relevante recortando relleno secundario o ruido.
    """
    if not text:
        return ""
    # Dividir por signos de puntuación principales (puntos, comas largas, saltos)
    clauses = re.split(r'[;\.\n\r]|\b(pero|aunque|sin embargo)\b', text, flags=re.IGNORECASE)
    for clause in clauses:
        if clause and len(clause.strip()) > 3:
            clean = clause.strip()
            # Si tiene más de 8 palabras, recortar en la primera coma si existe
            words = clean.split()
            if len(words) > 10:
                sub_parts = clean.split(',')
                if sub_parts and len(sub_parts[0].strip()) > 5:
                    return sub_parts[0].strip()
            return clean
    return text.strip()


def _tokenize_ngrams(text: str, n: int = 2) -> set[str]:
    clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
    words = clean.split()
    if len(words) < n:
        return set(words)
    return set(' '.join(words[i:i+n]) for i in range(len(words) - n + 1))


def compute_similarity(text1: str, text2: str) -> float:
    """
    Calcula similitud de Jaccard sobre n-gramas de palabras entre dos textos.
    """
    set1 = _tokenize_ngrams(text1)
    set2 = _tokenize_ngrams(text2)
    if not set1 or not set2:
        return 0.0
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / max(1, union)


def cluster_semantic_reviews(texts: List[str], similarity_threshold: float = 0.35) -> List[Dict]:
    """
    Agrupa una lista de reseñas por contexto/similitud semántica y extrae la frase canónica representativa.
    Retorna una lista de clusters con:
    - canonical_es: Frase núcleo representativa
    - count: Frecuencia de ocurrencias
    - original_texts: Lista de todas las reseñas pertenecientes al cluster
    """
    clusters: List[Dict] = []
    
    # 1. Extraer frases núcleo y contar frecuencias exactas de núcleos primero
    core_frequency: Dict[str, Tuple[str, List[str]]] = defaultdict(lambda: ("", []))
    
    for t in texts:
        t_clean = t.strip()
        if not t_clean:
            continue
        core = extract_core_phrase(t_clean)
        norm_core = re.sub(r'[^\w\s]', '', core.lower()).strip()
        if not norm_core:
            norm_core = t_clean.lower()
            
        current_canonical, raw_list = core_frequency[norm_core]
        if not current_canonical:
            current_canonical = core
        raw_list.append(t_clean)
        core_frequency[norm_core] = (current_canonical, raw_list)

    # 2. Agrupamiento por Similitud Semántica entre Núcleos
    unique_cores = list(core_frequency.items())
    visited = set()

    for i, (norm_i, (canonical_i, raw_list_i)) in enumerate(unique_cores):
        if i in visited:
            continue
        visited.add(i)
        
        cluster_canonical = canonical_i
        cluster_raw_texts = list(raw_list_i)

        for j in range(i + 1, len(unique_cores)):
            if j in visited:
                continue
            norm_j, (canonical_j, raw_list_j) = unique_cores[j]
            
            sim = compute_similarity(canonical_i, canonical_j)
            if sim >= similarity_threshold:
                visited.add(j)
                cluster_raw_texts.extend(raw_list_j)

        clusters.append({
            "canonical_es": cluster_canonical,
            "count": len(cluster_raw_texts),
            "original_texts": cluster_raw_texts
        })

    # Ordenar los clusters por frecuencia descendente (los problemas más comunes primero)
    clusters.sort(key=lambda c: c["count"], reverse=True)
    return clusters
