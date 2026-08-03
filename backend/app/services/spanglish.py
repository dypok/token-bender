import json
import os

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


async def generate_spanglish(text: str, source_lang: str) -> str:
    return apply_dictionary(text, source_lang)
