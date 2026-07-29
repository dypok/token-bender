import json
from deep_translator import GoogleTranslator
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, DEEPL_BASE_URL
from app.http_pool import get_http


async def translate_ollama(text: str, target_lang: str = "en", source_lang: str = "auto") -> str | None:
    lang_map = {"en": "English", "es": "Spanish"}
    target = lang_map.get(target_lang, "English")
    source_lang_display = lang_map.get(source_lang) if source_lang != "auto" else "the original"

    prompt = (
        f"Translate the following text from {source_lang_display} to {target}. "
        "Make the translation sound natural and fluent — not literal or word-for-word. "
        "Preserve the original context, tone, and meaning. "
        f"Respond only with the translated text, no explanations.\n\n{text}"
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
        return None


async def translate_deepl(text: str, api_key: str, target_lang: str = "EN", source_lang: str = "") -> str | None:
    params = {
        "auth_key": api_key,
        "text": text,
        "target_lang": target_lang.upper(),
    }
    if source_lang and source_lang != "auto":
        params["source_lang"] = source_lang.upper()

    try:
        client = get_http()
        resp = await client.post(DEEPL_BASE_URL, data=params)
        resp.raise_for_status()
        data = resp.json()
        return data["translations"][0]["text"]
    except Exception:
        return None


async def translate_fallback(text: str, target_lang: str = "en", source_lang: str = "auto") -> str:
    try:
        result = GoogleTranslator(source=source_lang, target=target_lang).translate(text)
        return result
    except Exception:
        return text


async def translate(text: str, engine: str, target_lang: str = "en", source_lang: str = "auto", deepl_api_key: str = "") -> tuple[str, str]:
    if engine == "google":
        result = await translate_fallback(text, target_lang, source_lang)
        return result, "google"

    if engine == "ollama":
        result = await translate_ollama(text, target_lang, source_lang)
        if result:
            return result, "ollama"
        result = await translate_deepl(text, deepl_api_key, target_lang, source_lang)
        if result:
            return result, "deepl"
        result = await translate_fallback(text, target_lang, source_lang)
        return result, "fallback"

    if engine == "deepl":
        if deepl_api_key:
            result = await translate_deepl(text, deepl_api_key, target_lang, source_lang)
            if result:
                return result, "deepl"
        result = await translate_ollama(text, target_lang, source_lang)
        if result:
            return result, "ollama"
        result = await translate_fallback(text, target_lang, source_lang)
        return result, "fallback"

    return text, "none"


async def check_ollama_status() -> bool:
    try:
        client = get_http()
        resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
        return resp.status_code == 200
    except Exception:
        return False
