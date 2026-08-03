from pydantic import BaseModel
from typing import Literal, Optional


class TokenizeRequest(BaseModel):
    text: str
    encoding: str = "o200k_base"


class TokenizeResponse(BaseModel):
    text: str
    token_count: int
    detected_language: str


class AnalyzeRequest(BaseModel):
    text: str
    engine: Literal["ctranslate2"] = "ctranslate2"
    classify: bool = False
    skip_spanglish: bool = False


class TokenVariant(BaseModel):
    text: str
    language: str
    token_count: int


class Classification(BaseModel):
    error_type: str
    component: str


class AnalyzeResponse(BaseModel):
    original: TokenVariant
    translated: TokenVariant
    spanglish: TokenVariant
    classification: Optional[Classification] = None
    engine_used: str


class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"
    engine: Literal["ctranslate2"] = "ctranslate2"


class TranslateResponse(BaseModel):
    text: str
    engine_used: str
