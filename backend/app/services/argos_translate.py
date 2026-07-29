import argostranslate.package
import argostranslate.translate

_es_to_en = None
_en_to_es = None


def init_packages():
    global _es_to_en, _en_to_es
    if _es_to_en is None:
        try:
            _es_to_en = argostranslate.translate.get_translation_from_codes("es", "en")
            _en_to_es = argostranslate.translate.get_translation_from_codes("en", "es")
        except Exception:
            argostranslate.package.update_package_index()
            for pkg in argostranslate.package.get_available_packages():
                if pkg.from_code == "es" and pkg.to_code == "en":
                    argostranslate.package.install_from_path(pkg.download())
                if pkg.from_code == "en" and pkg.to_code == "es":
                    argostranslate.package.install_from_path(pkg.download())
            _es_to_en = argostranslate.translate.get_translation_from_codes("es", "en")
            _en_to_es = argostranslate.translate.get_translation_from_codes("en", "es")
    return _es_to_en, _en_to_es


def translate(text: str, source_lang: str = "es", target_lang: str = "en") -> str:
    es_to_en, en_to_es = init_packages()
    if source_lang == "es" and target_lang == "en":
        return es_to_en.translate(text)
    if source_lang == "en" and target_lang == "es":
        return en_to_es.translate(text)
    return text


def batch_translate(texts: list[str], source_lang: str = "es", target_lang: str = "en") -> list[str]:
    es_to_en, en_to_es = init_packages()
    translator = es_to_en if source_lang == "es" and target_lang == "en" else en_to_es
    return [translator.translate(t) for t in texts]
