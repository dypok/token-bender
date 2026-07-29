import json
import os
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.http_pool import get_http

DICT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "spanglish_dict.json")


def load_spanglish_dict() -> dict:
    with open(DICT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


_spanglish_dict: dict | None = None


def get_dict() -> dict:
    global _spanglish_dict
    if _spanglish_dict is None:
        _spanglish_dict = load_spanglish_dict()
    return _spanglish_dict


def apply_dictionary(text: str, source_lang: str) -> str:
    d = get_dict()
    if source_lang == "es":
        substitutions = d.get("es_to_en", {})
    else:
        substitutions = d.get("en_to_es", {})
    for word, replacement in substitutions.items():
        text = text.replace(word, replacement)
    return text


async def generate_spanglish(text: str, source_lang: str, engine: str = "ollama") -> str:
    dict_text = apply_dictionary(text, source_lang)

    if engine != "ollama":
        return dict_text

    lang_pair = "Spanish to English" if source_lang == "es" else "English to Spanish"
    prompt = (
        f"You are a Spanglish generator. Given a {lang_pair} text, rewrite it by "
        "mixing words from both languages. Prioritize the shorter (in characters) "
        "word for each concept. The result must remain grammatically coherent and "
        "easily understandable. Do not translate the whole sentence — just replace "
        "individual words where the other language's word is shorter.\n\n"
        f"Text: {dict_text}\n\nSpanglish:"
    )

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    try:
        client = get_http()
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()
    except Exception:
        return dict_text
