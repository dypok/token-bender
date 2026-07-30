import os
import asyncio
import ctranslate2
import transformers
from concurrent.futures import ThreadPoolExecutor

_MODEL_NAME = "Helsinki-NLP/opus-mt-es-en"
_CT_MODEL_PATH = os.path.expanduser("~/.cache/ctranslate2_marian_es_en")

_tokenizer = None
_translator = None


def _init_ctranslate2():
    global _tokenizer, _translator
    if _translator is None:
        try:
            if not os.path.exists(_CT_MODEL_PATH):
                print(f"Convertir modelo HF '{_MODEL_NAME}' a CTranslate2 INT8 C++...")
                converter = ctranslate2.converters.TransformersConverter(_MODEL_NAME)
                converter.convert(_CT_MODEL_PATH, quantization="int8", force=True)
            
            _tokenizer = transformers.MarianTokenizer.from_pretrained(_MODEL_NAME)
            
            num_cpus = os.cpu_count() or 4
            
            _translator = ctranslate2.Translator(
                _CT_MODEL_PATH,
                device="cpu",
                compute_type="int8",
                inter_threads=4,
                intra_threads=0,  # 0 indica a CTranslate2 / OpenMP que use el 100% de hilos lógicos C++
            )
        except Exception as e:
            print(f"Error inicializando CTranslate2: {e}")
            _tokenizer = None
            _translator = None
    return _tokenizer, _translator


def _tokenize_text(txt: str):
    tokenizer, _ = _init_ctranslate2()
    return tokenizer.convert_ids_to_tokens(tokenizer.encode(txt))


def _decode_result(r):
    tokenizer, _ = _init_ctranslate2()
    hyp = r.hypotheses[0]
    ids = tokenizer.convert_tokens_to_ids(hyp)
    return tokenizer.decode(ids, skip_special_tokens=True)


def translate_batch_ctranslate2(texts: list[str], batch_size: int = 2048) -> list[str]:
    tokenizer, translator = _init_ctranslate2()
    if not tokenizer or not translator:
        return texts

    if not texts:
        return []

    try:
        # Pre-tokenización directa (evita la sobrecarga de context switching en GIL de Python)
        tokenized_inputs = [tokenizer.convert_ids_to_tokens(tokenizer.encode(t)) for t in texts]

        # Inferencia C++ ultrarrápida nativa multihilo
        results = translator.translate_batch(
            tokenized_inputs,
            max_batch_size=batch_size,
            batch_type="tokens",
            beam_size=1,
        )

        # Decodificación de tokens directa
        decoded = []
        for r in results:
            hyp = r.hypotheses[0]
            ids = tokenizer.convert_tokens_to_ids(hyp)
            decoded.append(tokenizer.decode(ids, skip_special_tokens=True))

        return decoded
    except Exception as e:
        print(f"Error en translate_batch_ctranslate2: {e}")
        return texts


def translate_single(text: str) -> str | None:
    res = translate_batch_ctranslate2([text])
    return res[0] if res else None


async def translate_ctranslate2(text: str) -> str | None:
    return await asyncio.to_thread(translate_single, text)


async def translate_ctranslate2_batch(texts: list[str]) -> list[str]:
    return await asyncio.to_thread(translate_batch_ctranslate2, texts)
