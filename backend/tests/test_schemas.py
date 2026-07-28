from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    TokenVariant,
    ProjectionRequest,
    ProjectionResponse,
    TokenizeRequest,
)


class TestTokenizeRequest:
    def test_default_encoding(self):
        req = TokenizeRequest(text="hola")
        assert req.encoding == "o200k_base"


class TestAnalyzeRequest:
    def test_default_engine(self):
        req = AnalyzeRequest(text="hola")
        assert req.engine == "ollama"

    def test_default_classify(self):
        req = AnalyzeRequest(text="hola")
        assert req.classify is False


class TestProjectionRequest:
    def test_defaults(self):
        req = ProjectionRequest(tokens_original=27, tokens_translated=19)
        assert req.reviews_per_day == 10000
        assert req.cost_per_million_tokens_usd == 2.5
        assert req.days == 30


class TestProjectionResponse:
    def test_fields(self):
        resp = ProjectionResponse(
            daily_token_diff=80000,
            monthly_token_diff=2400000,
            monthly_savings_usd=6.0,
        )
        assert resp.monthly_savings_usd == 6.0


class TestAnalyzeResponse:
    def test_optional_classification(self):
        orig = TokenVariant(text="a", language="es", token_count=1)
        trans = TokenVariant(text="b", language="en", token_count=1)
        spang = TokenVariant(text="c", language="mix", token_count=1)
        resp = AnalyzeResponse(
            original=orig,
            translated=trans,
            spanglish=spang,
            engine_used="ollama",
        )
        assert resp.classification is None
