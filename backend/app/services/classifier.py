import json
import re
from app.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.http_pool import get_http


SYSTEM_PROMPT = (
    "You are a classifier for app store reviews. "
    "Given a review text, extract:\n"
    "- error_type: one of [crash, bug, performance, ui, network, feature_request]\n"
    "- component: the app component involved, e.g. login, signup, profile_picture_upload, "
    "search, checkout, payment, notifications, settings, chat, camera, gallery, map, "
    "video_player, audio_player, file_download\n\n"
    "Respond ONLY with a valid JSON object like this, no extra text:\n"
    '{"error_type": "...", "component": "..."}'
)


async def classify_ollama(text: str) -> dict | None:
    payload = {
        "model": OLLAMA_MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": f"Review: {text}\n\nJSON:",
        "stream": False,
    }
    try:
        client = get_http()
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw = data.get("response", "").strip()
        return _parse_json(raw)
    except Exception:
        return None


async def classify_combined(text: str) -> dict | None:
    prompt = (
        "Translate the following Spanish app review to English and classify the error. "
        "Respond ONLY with a valid JSON object, no extra text:\n"
        '{"translation": "...", "error_type": "crash|bug|performance|ui|network|feature_request", '
        '"component": "login|signup|profile_picture_upload|gallery|camera|chat|payment|'
        'checkout|notifications|settings|video_player|audio_player|file_download|search|map|unknown"}\n\n'
        f"Review: {text}"
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
        raw = data.get("response", "").strip()
        parsed = _parse_json(raw)
        if parsed and "translation" in parsed:
            return parsed
        return None
    except Exception:
        return None


async def classify_fallback(text: str) -> dict:
    text_lower = text.lower()
    error_type = "bug"
    if any(w in text_lower for w in ["cierra", "cierra", "crash", "crashea", "explota", "muere", "cierre"]):
        error_type = "crash"
    elif any(w in text_lower for w in ["lenta", "lento", "tilda", "congela", "cargando"]):
        error_type = "performance"
    elif any(w in text_lower for w in ["pantalla", "botón", "interfaz", "ui", "veo"]):
        error_type = "ui"
    elif any(w in text_lower for w in ["red", "wifi", "conexión", "internet", "servidor"]):
        error_type = "network"

    component = "unknown"
    comp_map = [
        ("foto", "profile_picture_upload"), ("perfil", "profile_picture_upload"),
        ("galería", "gallery"), ("cámara", "camera"),
        ("sesión", "login"), ("login", "login"), ("registr", "signup"),
        ("pagar", "checkout"), ("pago", "payment"), ("tarjeta", "payment"),
        ("notificaciones", "notifications"), ("notificación", "notifications"),
        ("chat", "chat"), ("mensaje", "chat"),
        ("video", "video_player"), ("audio", "audio_player"),
        ("descargar", "file_download"), ("archivo", "file_download"),
        ("configuración", "settings"), ("settings", "settings"),
        ("mapa", "map"), ("buscar", "search"), ("búsqueda", "search"),
    ]
    for keyword, comp in comp_map:
        if keyword in text_lower:
            component = comp
            break

    return {"error_type": error_type, "component": component}


async def classify(text: str, engine: str, deepl_api_key: str = "") -> tuple[dict, str]:
    if engine == "google":
        fallback = await classify_fallback(text)
        return fallback, "google"

    if engine == "ollama":
        result = await classify_ollama(text)
        if result:
            return result, "ollama"
        fallback = await classify_fallback(text)
        return fallback, "fallback"

    if engine == "deepl":
        result = await classify_ollama(text)
        if result:
            return result, "ollama"
        fallback = await classify_fallback(text)
        return fallback, "fallback"

    fallback = await classify_fallback(text)
    return fallback, "fallback"


def _parse_json(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    match = re.search(r'\{[^}]+\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return None
