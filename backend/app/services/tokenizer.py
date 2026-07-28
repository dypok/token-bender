import tiktoken
from langdetect import detect
from app.config import ENCODING


def count_tokens(text: str, encoding_name: str = ENCODING) -> int:
    encoder = tiktoken.get_encoding(encoding_name)
    return len(encoder.encode(text))


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"
