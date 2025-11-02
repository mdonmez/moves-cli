"""Consolidated tests for utility modules."""

import pytest
import re
from pathlib import Path
from unittest.mock import MagicMock, patch
import httpx
from moves_cli.utils import (
    data_handler,
    id_generator,
    text_normalizer,
    model_downloader,
)


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


class TestModelDownloader:
    """Critical tests for model downloading functionality."""

    def test_models_config_structure(self):
        """Test that MODELS dictionary has correct structure."""
        assert "embedding" in model_downloader.MODELS
        assert "stt" in model_downloader.MODELS

        for model_type, config in model_downloader.MODELS.items():
            assert "name" in config
            assert "base_url" in config
            assert "files" in config
            assert isinstance(config["files"], list)
            assert len(config["files"]) > 0

    def test_download_file_creates_file(self, tmp_path, monkeypatch):
        """Test that _download_file creates a file with correct content."""
        test_file = tmp_path / "test_model.txt"
        test_content = b"test model content"

        # Mock httpx.Client and response
        mock_response = MagicMock()
        mock_response.headers.get.return_value = str(len(test_content))
        mock_response.iter_bytes.return_value = [test_content]
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response

        model_downloader._download_file(mock_client, "http://test.url", test_file)

        assert test_file.exists()
        assert test_file.read_bytes() == test_content

    def test_download_file_skips_existing(self, tmp_path):
        """Test that _download_file skips already downloaded files."""
        test_file = tmp_path / "existing.txt"
        test_file.write_bytes(b"existing content")

        mock_client = MagicMock()

        model_downloader._download_file(mock_client, "http://test.url", test_file)

        # Should not make any HTTP request
        mock_client.stream.assert_not_called()
        assert test_file.read_bytes() == b"existing content"

    def test_download_file_handles_http_error(self, tmp_path):
        """Test that _download_file handles HTTP errors properly."""
        test_file = tmp_path / "failed.txt"

        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404", request=MagicMock(), response=MagicMock()
        )
        mock_response.__enter__ = lambda self: self
        mock_response.__exit__ = lambda self, *args: None

        mock_client = MagicMock()
        mock_client.stream.return_value = mock_response

        with pytest.raises(RuntimeError, match="Download failed"):
            model_downloader._download_file(mock_client, "http://test.url", test_file)

        # File should be cleaned up on failure
        assert not test_file.exists()

    def test_download_model_invalid_type(self):
        """Test that download_model raises error for invalid model type."""
        with pytest.raises(ValueError, match="Unsupported model type"):
            model_downloader.download_model("invalid_type")  # type: ignore[arg-type]

    def test_download_model_creates_directory(self, tmp_path, monkeypatch):
        """Test that download_model creates the model directory."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        # Mock the HTTP client and download
        with patch(
            "moves_cli.utils.model_downloader.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = lambda self: self
            mock_client.__exit__ = lambda self, *args: None
            mock_client_class.return_value = mock_client

            # Mock successful download
            mock_response = MagicMock()
            mock_response.headers.get.return_value = "100"
            mock_response.iter_bytes.return_value = [b"test"]
            mock_response.__enter__ = lambda self: self
            mock_response.__exit__ = lambda self, *args: None
            mock_client.stream.return_value = mock_response

            result = model_downloader.download_model("embedding")

            expected_dir = tmp_path / "ml_models" / "all-MiniLM-L6-v2_quint8_avx2"
            assert result == expected_dir
            assert expected_dir.exists()

    def test_download_model_downloads_all_files(self, tmp_path, monkeypatch):
        """Test that download_model attempts to download all required files."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        with patch(
            "moves_cli.utils.model_downloader.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = lambda self: self
            mock_client.__exit__ = lambda self, *args: None
            mock_client_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.headers.get.return_value = "100"
            mock_response.iter_bytes.return_value = [b"test"]
            mock_response.__enter__ = lambda self: self
            mock_response.__exit__ = lambda self, *args: None
            mock_client.stream.return_value = mock_response

            model_downloader.download_model("stt")

            # Should have called stream for each file in the STT model
            expected_files = model_downloader.MODELS["stt"]["files"]
            assert mock_client.stream.call_count == len(expected_files)

    def test_cleanup_removes_unknown_folders(self, tmp_path, monkeypatch):
        """Test cleanup deletes entire folders not in MODELS."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create current model folders
        (ml_models / "all-MiniLM-L6-v2_quint8_avx2").mkdir()
        (ml_models / "nemo-streaming-stt-480ms-int8").mkdir()

        # Create old model folder
        old_model = ml_models / "old-model-v1"
        old_model.mkdir()
        (old_model / "old_file.onnx").write_text("old")

        result = model_downloader.cleanup_old_models()

        assert result["deleted_folders"] == 1
        assert not old_model.exists()
        assert (ml_models / "all-MiniLM-L6-v2_quint8_avx2").exists()
        assert (ml_models / "nemo-streaming-stt-480ms-int8").exists()

    def test_cleanup_removes_root_level_files(self, tmp_path, monkeypatch):
        """Test cleanup deletes stray files in ml_models root."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create stray files in root
        (ml_models / "temp.txt").write_text("temp")
        (ml_models / ".DS_Store").write_text("system")

        result = model_downloader.cleanup_old_models()

        assert result["deleted_files"] == 2
        assert not (ml_models / "temp.txt").exists()
        assert not (ml_models / ".DS_Store").exists()

    def test_cleanup_removes_invalid_files_in_valid_folders(
        self, tmp_path, monkeypatch
    ):
        """Test cleanup deletes old files inside current model folders."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create valid model folder with mix of valid and invalid files
        model_dir = ml_models / "all-MiniLM-L6-v2_quint8_avx2"
        model_dir.mkdir()
        (model_dir / "model.onnx").write_text("valid")  # Valid file
        (model_dir / "config.json").write_text("valid")  # Valid file
        (model_dir / "old_model.onnx").write_text("old")  # Invalid file
        (model_dir / "backup.json").write_text("old")  # Invalid file

        result = model_downloader.cleanup_old_models()

        assert result["deleted_files"] == 2
        assert (model_dir / "model.onnx").exists()
        assert (model_dir / "config.json").exists()
        assert not (model_dir / "old_model.onnx").exists()
        assert not (model_dir / "backup.json").exists()

    def test_cleanup_removes_nested_folders_in_model_dirs(self, tmp_path, monkeypatch):
        """Test cleanup deletes unexpected subdirectories in model folders."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create valid model folder with unexpected subdirectory
        model_dir = ml_models / "nemo-streaming-stt-480ms-int8"
        model_dir.mkdir()
        backup_dir = model_dir / "backup"
        backup_dir.mkdir()
        (backup_dir / "old_encoder.onnx").write_text("old")

        result = model_downloader.cleanup_old_models()

        assert result["deleted_folders"] == 1
        assert not backup_dir.exists()
        assert model_dir.exists()

    def test_cleanup_preserves_valid_structure(self, tmp_path, monkeypatch):
        """Test cleanup keeps all files defined in MODELS config."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create complete valid structure for embedding model
        embedding_dir = ml_models / "all-MiniLM-L6-v2_quint8_avx2"
        embedding_dir.mkdir()
        for fname in model_downloader.MODELS["embedding"]["files"]:
            (embedding_dir / fname).write_text("valid")

        # Create complete valid structure for STT model
        stt_dir = ml_models / "nemo-streaming-stt-480ms-int8"
        stt_dir.mkdir()
        for fname in model_downloader.MODELS["stt"]["files"]:
            (stt_dir / fname).write_text("valid")

        result = model_downloader.cleanup_old_models()

        assert result["deleted_folders"] == 0
        assert result["deleted_files"] == 0
        # All files should still exist
        for fname in model_downloader.MODELS["embedding"]["files"]:
            assert (embedding_dir / fname).exists()
        for fname in model_downloader.MODELS["stt"]["files"]:
            assert (stt_dir / fname).exists()

    def test_cleanup_handles_missing_directory(self, tmp_path, monkeypatch):
        """Test cleanup handles non-existent ml_models directory."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        result = model_downloader.cleanup_old_models()

        assert result == {"deleted_folders": 0, "deleted_files": 0}

    def test_cleanup_handles_partial_model_folders(self, tmp_path, monkeypatch):
        """Test cleanup with missing files in valid folders."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create valid folder with only subset of expected files
        model_dir = ml_models / "all-MiniLM-L6-v2_quint8_avx2"
        model_dir.mkdir()
        (model_dir / "model.onnx").write_text("valid")
        (model_dir / "config.json").write_text("valid")
        # Missing other expected files

        result = model_downloader.cleanup_old_models()

        # Folder preserved, existing files not deleted
        assert result["deleted_folders"] == 0
        assert result["deleted_files"] == 0
        assert model_dir.exists()
        assert (model_dir / "model.onnx").exists()
        assert (model_dir / "config.json").exists()

    def test_cleanup_returns_correct_stats(self, tmp_path, monkeypatch):
        """Test cleanup returns accurate deletion counts."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create 2 old folders
        (ml_models / "old-model-1").mkdir()
        (ml_models / "old-model-2").mkdir()

        # Create 3 stray files in root
        (ml_models / "file1.txt").write_text("stray")
        (ml_models / "file2.txt").write_text("stray")
        (ml_models / "file3.txt").write_text("stray")

        # Create valid folder with 1 invalid file
        model_dir = ml_models / "all-MiniLM-L6-v2_quint8_avx2"
        model_dir.mkdir()
        (model_dir / "old_file.onnx").write_text("old")

        result = model_downloader.cleanup_old_models()

        assert result["deleted_folders"] == 2
        assert result["deleted_files"] == 4  # 3 in root + 1 in valid folder

    def test_cleanup_handles_permission_errors_gracefully(self, tmp_path, monkeypatch):
        """Test cleanup raises RuntimeError on permission errors."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()

        # Create a file in root
        test_file = ml_models / "test.txt"
        test_file.write_text("test")

        # Mock unlink to raise PermissionError
        original_unlink = Path.unlink

        def mock_unlink(self, *args, **kwargs):
            if self.name == "test.txt":
                raise PermissionError("Permission denied")
            return original_unlink(self, *args, **kwargs)

        monkeypatch.setattr(Path, "unlink", mock_unlink)

        with pytest.raises(RuntimeError, match="Cleanup failed"):
            model_downloader.cleanup_old_models()

    def test_download_model_triggers_cleanup(self, tmp_path, monkeypatch):
        """Test download_model calls cleanup automatically."""
        monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)

        # Create ml_models with old folder
        ml_models = tmp_path / "ml_models"
        ml_models.mkdir()
        old_model = ml_models / "old-model"
        old_model.mkdir()

        with patch(
            "moves_cli.utils.model_downloader.httpx.Client"
        ) as mock_client_class:
            mock_client = MagicMock()
            mock_client.__enter__ = lambda self: self
            mock_client.__exit__ = lambda self, *args: None
            mock_client_class.return_value = mock_client

            mock_response = MagicMock()
            mock_response.headers.get.return_value = "100"
            mock_response.iter_bytes.return_value = [b"test"]
            mock_response.__enter__ = lambda self: self
            mock_response.__exit__ = lambda self, *args: None
            mock_client.stream.return_value = mock_response

            model_downloader.download_model("embedding")

            # Old model folder should be cleaned up
            assert not old_model.exists()
