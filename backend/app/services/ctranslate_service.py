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
            
            # Escalamiento dinámico a TODOS los hilos disponibles en el sistema (100% CPU cores)
            num_cpus = os.cpu_count() or 4
            intra = max(1, num_cpus // 2)
            inter = max(1, num_cpus // intra)
            
            _translator = ctranslate2.Translator(
                _CT_MODEL_PATH,
                device="cpu",
                compute_type="int8",
                inter_threads=inter,
                intra_threads=intra,
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
        # Escalar dinámicamente según la CPU del servidor
        num_workers = min(32, (os.cpu_count() or 4) * 2)

        # 1. Pre-tokenización paralela distribuida en todos los hilos
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            tokenized_inputs = list(executor.map(_tokenize_text, texts))

        # 2. Inferencia C++ ultrarrápida
        results = translator.translate_batch(
            tokenized_inputs,
            max_batch_size=batch_size,
            batch_type="tokens",
            beam_size=1,
        )

        # 3. Decodificación de tokens paralela distribuida
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            decoded = list(executor.map(_decode_result, results))

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
