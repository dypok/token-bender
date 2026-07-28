from fastapi import APIRouter, Header
from app.models.schemas import TranslateRequest, TranslateResponse
from app.services.translator import translate

router = APIRouter()


@router.post("/api/translate", response_model=TranslateResponse)
async def translate_endpoint(req: TranslateRequest, deepl_api_key: str = Header(default="")):
    result, engine_used = await translate(
        req.text, req.engine, req.target_lang, req.source_lang, deepl_api_key
    )
    return TranslateResponse(text=result, engine_used=engine_used)
