from app.models.schemas import (
    BatchResultItem,
    EconomicSummary,
    COST_PER_MILLION_TOKENS,
)

REVIEWS_10K = 10000


def make_item(
    text_es: str,
    text_en: str,
    tok_es: int,
    tok_en: int,
    frequency: int = 1,
    product_name: str | None = None,
    stars: int = 3,
) -> BatchResultItem:
    cost_es = round((tok_es / 1_000_000) * COST_PER_MILLION_TOKENS, 6)
    cost_en = round((tok_en / 1_000_000) * COST_PER_MILLION_TOKENS, 6)
    diff = tok_en - tok_es
    if diff < 0:
        best = "en"
        just = f"Inglés tiene {abs(diff)} tokens menos que español (${abs(round(cost_en - cost_es, 6))} más barato)"
    elif diff > 0:
        best = "es"
        just = f"Español tiene {diff} tokens menos que inglés (${abs(round(cost_es - cost_en, 6))} más barato)"
    else:
        best = "igual"
        just = "Ambos idiomas tienen el mismo costo de tokens"

    return BatchResultItem(
        review=text_es, tokens_original=tok_es, text_en=text_en, tokens_en=tok_en,
        cost_original_usd=cost_es, cost_en_usd=cost_en, best_lang=best,
        justification=just, classification=None,
        frequency=frequency, product_name=product_name, stars=stars,
    )


def empty_summary() -> EconomicSummary:
    return EconomicSummary(
        total_reviews=0, total_tokens_original=0, total_tokens_en=0,
        avg_tokens_original=0.0, avg_tokens_en=0.0,
        daily_cost_original_10k=0.0, daily_cost_en_10k=0.0,
        daily_savings_10k=0.0, weekly_savings_10k=0.0, monthly_savings_10k=0.0,
        best_global_lang="es",
    )


def build_summary(results: list[BatchResultItem]) -> EconomicSummary:
    total = sum(r.frequency for r in results)
    if total == 0:
        return empty_summary()

    sum_orig = sum(r.tokens_original * r.frequency for r in results)
    sum_en = sum(r.tokens_en * r.frequency for r in results)
    avg_orig = round(sum_orig / total, 1)
    avg_en = round(sum_en / total, 1)

    daily_orig = (avg_orig / 1_000_000) * COST_PER_MILLION_TOKENS * REVIEWS_10K
    daily_en = (avg_en / 1_000_000) * COST_PER_MILLION_TOKENS * REVIEWS_10K
    daily_savings = daily_orig - daily_en

    en_better = sum(r.frequency for r in results if r.best_lang == "en")
    es_better = sum(r.frequency for r in results if r.best_lang == "es")

    return EconomicSummary(
        total_reviews=total,
        total_tokens_original=sum_orig,
        total_tokens_en=sum_en,
        avg_tokens_original=avg_orig, avg_tokens_en=avg_en,
        daily_cost_original_10k=round(daily_orig, 2),
        daily_cost_en_10k=round(daily_en, 2),
        daily_savings_10k=round(max(0, daily_savings), 2),
        weekly_savings_10k=round(max(0, daily_savings * 7), 2),
        monthly_savings_10k=round(max(0, daily_savings * 30), 2),
        best_global_lang="en" if en_better >= es_better else "es",
    )
