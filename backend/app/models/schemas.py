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
    engine: Literal["ollama", "deepl"] = "ollama"
    classify: bool = False


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
    engine: Literal["ollama", "deepl"] = "ollama"


class TranslateResponse(BaseModel):
    text: str
    engine_used: str


class BatchUploadRequest(BaseModel):
    optent_tokens: bool = True
    engine: Literal["ollama", "deepl"] = "ollama"


class BatchFolderRequest(BaseModel):
    folder_path: str
    optent_tokens: bool = True
    engine: Literal["ollama", "deepl"] = "ollama"


class ProjectionRequest(BaseModel):
    tokens_original: int
    tokens_translated: int
    reviews_per_day: int = 10000
    cost_per_million_tokens_usd: float = 2.5
    days: int = 30


class ProjectionResponse(BaseModel):
    daily_token_diff: int
    monthly_token_diff: int
    monthly_savings_usd: float


COST_PER_MILLION_TOKENS = 2.5


class BatchResultItem(BaseModel):
    review: str
    tokens_original: int
    text_en: str
    tokens_en: int
    cost_original_usd: float
    cost_en_usd: float
    best_lang: str
    justification: str
    classification: Optional[Classification] = None


class EconomicSummary(BaseModel):
    total_reviews: int
    total_tokens_original: int
    total_tokens_en: int
    avg_tokens_original: float
    avg_tokens_en: float
    daily_cost_original_10k: float
    daily_cost_en_10k: float
    daily_savings_10k: float
    weekly_savings_10k: float
    monthly_savings_10k: float
    best_global_lang: str


class BatchUploadResponse(BaseModel):
    results: list[BatchResultItem]
    economic_summary: EconomicSummary


class ConfigStatusResponse(BaseModel):
    ollama_available: bool
    deepl_configured: bool
