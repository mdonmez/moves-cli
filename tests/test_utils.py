"""Consolidated tests for utility modules."""

import pytest
import re
from pathlib import Path
from moves_cli.utils import data_handler, id_generator, text_normalizer


@pytest.fixture
def mock_data_folder(tmp_path, monkeypatch):
    """Replace DATA_FOLDER with a temporary directory for testing."""
    monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)
    return tmp_path


class TestDataHandler:
    """Critical tests for data handler operations."""

    def test_write_and_read_text(self, mock_data_folder):
        """Test basic write and read operations."""
        test_path = Path("test.txt")
        test_data = "Hello, World!"

        assert data_handler.write(test_path, test_data)
        assert data_handler.read(test_path) == test_data

    def test_write_with_unicode(self, mock_data_folder):
        """Test unicode handling."""
        test_path = Path("unicode.txt")
        test_data = "Café ☕ München 🎉"

        data_handler.write(test_path, test_data)
        assert data_handler.read(test_path) == test_data

    def test_write_creates_directories(self, mock_data_folder):
        """Test automatic directory creation."""
        test_path = Path("nested/dirs/file.txt")
        test_data = "Nested content"

        assert data_handler.write(test_path, test_data)
        assert (mock_data_folder / test_path).exists()

    def test_read_nonexistent_file(self, mock_data_folder):
        """Test reading non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            data_handler.read(Path("nonexistent.txt"))


class TestIDGenerator:
    """Critical tests for ID generation."""

    def test_speaker_id_format(self):
        """Test speaker ID has correct format."""
        speaker_id = id_generator.generate_speaker_id("John Doe")

        # Format: name-slug-xxxxx
        assert speaker_id.startswith("john-doe-")
        assert len(speaker_id.split("-")[-1]) == 5

    def test_speaker_id_url_safe(self):
        """Test speaker ID is URL-safe."""
        speaker_id = id_generator.generate_speaker_id("María García!@#")

        # Should only contain alphanumeric, hyphens, and underscores
        assert re.match(r"^[a-zA-Z0-9_-]+$", speaker_id)

    def test_speaker_id_handles_accents(self):
        """Test accent normalization in speaker IDs."""
        speaker_id = id_generator.generate_speaker_id("Café Owner")

        assert speaker_id.startswith("cafe-owner-")


class TestTextNormalizer:
    """Critical tests for text normalization."""

    def test_lowercase_and_whitespace(self):
        """Test basic normalization."""
        result = text_normalizer.normalize_text("HELLO   World")
        assert result == "hello world"

    def test_numbers_to_words(self):
        """Test number conversion."""
        result = text_normalizer.normalize_text("I have 3 cats")
        assert result == "i have three cats"

    def test_special_characters_removal(self):
        """Test special character handling."""
        result = text_normalizer.normalize_text("Hello!!! World???")
        assert result == "hello world"

    def test_accent_normalization(self):
        """Test accent removal."""
        result = text_normalizer.normalize_text("café")
        assert result == "cafe"
