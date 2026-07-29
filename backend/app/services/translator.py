import httpx
import json
import time
import asyncio
from deep_translator import GoogleTranslator
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL, DEEPL_BASE_URL


_ollama_cache = {"available": None, "last_checked": 0}


async def is_ollama_online() -> bool:
    now = time.time()
    if _ollama_cache["available"] is not None and (now - _ollama_cache["last_checked"]) < 15:
        return _ollama_cache["available"]
    
    _ollama_cache["available"] = False
    _ollama_cache["last_checked"] = now
    
    online = await check_ollama_status()
    _ollama_cache["available"] = online
    return online


async def translate_ollama(text: str, target_lang: str = "en", source_lang: str = "auto") -> str | None:
    if not await is_ollama_online():
        return None

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
        async with httpx.AsyncClient(timeout=60) as client:
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
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(DEEPL_BASE_URL, data=params)
            resp.raise_for_status()
            data = resp.json()
            return data["translations"][0]["text"]
    except Exception:
        return None


async def translate_fallback(text: str, target_lang: str = "en", source_lang: str = "auto") -> str:
    try:
        result = await asyncio.to_thread(
            GoogleTranslator(source=source_lang, target=target_lang).translate, text
        )
        return result
    except Exception:
        return text


async def translate(text: str, engine: str, target_lang: str = "en", source_lang: str = "auto", deepl_api_key: str = "") -> tuple[str, str]:
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
        async with httpx.AsyncClient(timeout=0.5) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return resp.status_code == 200
    except Exception:
        return False
