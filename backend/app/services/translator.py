from app.services.ctranslate_service import translate_ctranslate2


async def translate(text: str, target_lang: str = "en", source_lang: str = "es") -> tuple[str, str]:
    res = await translate_ctranslate2(text)
    if res and res.strip() != text.strip():
        return res, "ctranslate2"
    return text, "ctranslate2"
