import pytest
from app.services.tokenizer import count_tokens, detect_language


class TestCountTokens:
    def test_empty_string(self):
        assert count_tokens("") == 0

    def test_simple_text(self):
        assert count_tokens("Hola mundo") == 2

    def test_longer_text(self):
        text = "La aplicación se cierra inesperadamente cada vez que intento subir una foto de perfil"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)


class TestDetectLanguage:
    def test_detect_spanish(self):
        assert detect_language("Hola mundo") == "es"

    def test_detect_english(self):
        assert detect_language("The application crashes every time I try to upload a photo") == "en"

    def test_empty_returns_unknown(self):
        assert detect_language("") == "unknown"
