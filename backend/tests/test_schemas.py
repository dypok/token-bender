from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    TokenVariant,
    TokenizeRequest,
)


class TestTokenizeRequest:
    def test_default_encoding(self):
        req = TokenizeRequest(text="hola")
        assert req.encoding == "o200k_base"


class TestAnalyzeRequest:
    def test_default_engine(self):
        req = AnalyzeRequest(text="hola")
        assert req.engine == "ctranslate2"

    def test_default_classify(self):
        req = AnalyzeRequest(text="hola")
        assert req.classify is False


class TestAnalyzeResponse:
    def test_optional_classification(self):
        orig = TokenVariant(text="a", language="es", token_count=1)
        trans = TokenVariant(text="b", language="en", token_count=1)
        spang = TokenVariant(text="c", language="mix", token_count=1)
        resp = AnalyzeResponse(
            original=orig,
            translated=trans,
            spanglish=spang,
            engine_used="ctranslate2",
        )
        assert resp.classification is None
