import tiktoken
from langdetect import detect
from app.config import ENCODING

_encoder = None


def get_encoder(encoding_name: str = ENCODING):
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding(encoding_name)
    return _encoder


def count_tokens(text: str, encoding_name: str = ENCODING) -> int:
    encoder = get_encoder(encoding_name)
    return len(encoder.encode(text))


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"
