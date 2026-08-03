async def classify(text: str) -> dict:
    return classify_fallback_fast(text)


def classify_fallback_fast(text: str) -> dict:
    text_lower = text.lower()
    error_type = "bug"
    if any(w in text_lower for w in ["cierra", "crashea", "explota", "muere", "cierre", "crash"]):
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
