from fastapi import APIRouter
from app.models.schemas import TranslateRequest, TranslateResponse
from app.services.translator import translate

router = APIRouter()


@router.post("/api/translate", response_model=TranslateResponse)
async def translate_endpoint(req: TranslateRequest):
    result, engine_used = await translate(req.text, req.target_lang, req.source_lang)
    return TranslateResponse(text=result, engine_used=engine_used)
