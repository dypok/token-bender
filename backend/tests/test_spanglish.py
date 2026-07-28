from app.services.spanglish import apply_dictionary, load_spanglish_dict


class TestSpanglishDict:
    def test_dict_loads(self):
        d = load_spanglish_dict()
        assert "es_to_en" in d
        assert "en_to_es" in d

    def test_es_to_en_substitution(self):
        result = apply_dictionary("definitivamente", "es")
        assert "definitely" in result

    def test_en_to_es_substitution(self):
        result = apply_dictionary("absolutely", "en")
        assert "de una" in result

    def test_no_substitution_needed(self):
        result = apply_dictionary("Hola mundo", "es")
        assert result == "Hola mundo"
