from fastapi import APIRouter
from app.models.schemas import TokenizeRequest, TokenizeResponse
from app.services.tokenizer import count_tokens, detect_language
from app.config import ENCODING

router = APIRouter()


@router.post("/api/tokenize", response_model=TokenizeResponse)
def tokenize(req: TokenizeRequest):
    lang = detect_language(req.text)
    count = count_tokens(req.text, req.encoding)
    return TokenizeResponse(text=req.text, token_count=count, detected_language=lang)
