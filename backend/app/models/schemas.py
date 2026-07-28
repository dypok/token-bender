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


class BatchResultItem(BaseModel):
    review: str
    tokens: int
    classification: Optional[Classification] = None


class EconomicSummary(BaseModel):
    total_reviews: int
    total_tokens_processed: int
    projected_daily_tokens_10k: int
    projected_monthly_tokens_10k: int
    projected_monthly_savings_usd_10k: float
    avg_tokens_per_review: float


class BatchUploadResponse(BaseModel):
    results: list[BatchResultItem]
    economic_summary: EconomicSummary


class ConfigStatusResponse(BaseModel):
    ollama_available: bool
    deepl_configured: bool
