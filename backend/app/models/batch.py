from pydantic import BaseModel
from typing import Literal, Optional

from app.models.analyze import Classification


class BatchUploadRequest(BaseModel):
    optent_tokens: bool = True
    engine: Literal["ctranslate2"] = "ctranslate2"


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
    frequency: int = 1
    product_name: Optional[str] = None
    stars: int = 3


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
    product_ratings: Optional[dict[str, float]] = None
