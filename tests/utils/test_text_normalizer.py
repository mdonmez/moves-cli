from moves_cli.utils import text_normalizer


class TestNormalization:
    """Tests for text normalization operations."""

    def test_lowercase_conversion(self):
        input_text = "HELLO World"
        expected = "hello world"

        result = text_normalizer.normalize_text(input_text)

        assert result == expected

    def test_numbers_to_words(self):
        input_text = "I have 3 cats"
        expected = "i have three cats"

        result = text_normalizer.normalize_text(input_text)

        assert result == expected

    def test_special_characters_removal(self):
        input_text = "too !? many     characters..."
        expected = "too many characters"

        result = text_normalizer.normalize_text(input_text)

        assert result == expected

    def test_accented_characters_normalization(self):
        input_text = "café"
        expected = "cafe"

        result = text_normalizer.normalize_text(input_text)

        assert result == expected
