from fastapi import APIRouter
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, TokenVariant, Classification
from app.services.tokenizer import count_tokens, detect_language
from app.services.translator import translate
from app.services.spanglish import generate_spanglish
from app.services.classifier import classify

router = APIRouter()


@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    source_lang = detect_language(req.text)
    target_lang = "en" if source_lang == "es" else "es"

    original_tokens = count_tokens(req.text)

    translated_text, engine_used = await translate(req.text, target_lang, source_lang)

    classification = None
    if req.classify:
        class_result = await classify(req.text)
        classification = Classification(**class_result)

    translated_tokens = count_tokens(translated_text)

    if not req.skip_spanglish:
        spanglish_text = await generate_spanglish(req.text, source_lang)
        spanglish_tokens = count_tokens(spanglish_text)
    else:
        spanglish_text = ""
        spanglish_tokens = 0

    return AnalyzeResponse(
        original=TokenVariant(text=req.text, language=source_lang, token_count=original_tokens),
        translated=TokenVariant(text=translated_text, language=target_lang, token_count=translated_tokens),
        spanglish=TokenVariant(text=spanglish_text, language="mix", token_count=spanglish_tokens),
        classification=classification,
        engine_used=engine_used,
    )
