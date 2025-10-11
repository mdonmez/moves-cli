"""Simplified CLI integration tests - critical paths only."""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from moves_cli.main import app
from moves_cli.data.models import Speaker, Settings


@pytest.fixture
def runner():
    """Create a Typer CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_speaker():
    """Create a mock speaker."""
    return Speaker(
        speaker_id="john-doe-abc12",
        name="John Doe",
        source_presentation=Path("/path/to/presentation.pdf"),
        source_transcript=Path("/path/to/transcript.pdf"),
    )


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return Settings(model="gemini/gemini-2.0-flash", key="test-api-key")


# ============================================================================
# Speaker Commands
# ============================================================================


class TestSpeakerCommands:
    """Critical tests for speaker CLI commands."""

    def test_speaker_add_success(self, runner, mock_speaker, tmp_path):
        """Test successful speaker addition."""
        presentation = tmp_path / "presentation.pdf"
        transcript = tmp_path / "transcript.pdf"
        presentation.write_text("content")
        transcript.write_text("content")

        with patch("moves_cli.main.speaker_manager_instance") as mock_mgr:
            mock_manager = MagicMock()
            mock_manager.add.return_value = mock_speaker
            mock_mgr.return_value = mock_manager

            result = runner.invoke(
                app,
                ["speaker", "add", "John Doe", str(presentation), str(transcript)],
            )

            assert result.exit_code == 0
            assert "john-doe-abc12" in result.output

    def test_speaker_add_missing_files(self, runner, tmp_path):
        """Test speaker add with missing files."""
        presentation = tmp_path / "missing.pdf"
        transcript = tmp_path / "transcript.pdf"
        transcript.write_text("content")

        result = runner.invoke(
            app,
            ["speaker", "add", "John Doe", str(presentation), str(transcript)],
        )

        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_speaker_list(self, runner, mock_speaker):
        """Test speaker list command."""
        with patch("moves_cli.main.speaker_manager_instance") as mock_mgr:
            mock_manager = MagicMock()
            mock_manager.list.return_value = [mock_speaker]
            mock_mgr.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "list"])

            assert result.exit_code == 0
            assert "john-doe-abc12" in result.output

    def test_speaker_delete(self, runner):
        """Test speaker delete command."""
        with patch("moves_cli.main.speaker_manager_instance") as mock_mgr:
            mock_manager = MagicMock()
            mock_manager.delete.return_value = True
            mock_mgr.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "delete", "john-doe-abc12"])

            assert result.exit_code == 0


# ============================================================================
# Settings Commands
# ============================================================================


class TestSettingsCommands:
    """Critical tests for settings CLI commands."""

    def test_settings_list(self, runner, mock_settings):
        """Test settings list command."""
        with patch("moves_cli.main.settings_editor_instance") as mock_editor:
            mock_ed = MagicMock()
            mock_ed.list.return_value = mock_settings
            mock_editor.return_value = mock_ed

            result = runner.invoke(app, ["settings", "list"])

            assert result.exit_code == 0
            assert "gemini" in result.output.lower()

    def test_settings_set(self, runner):
        """Test settings set command."""
        with patch("moves_cli.main.settings_editor_instance") as mock_editor:
            mock_ed = MagicMock()
            mock_ed.set.return_value = True
            mock_editor.return_value = mock_ed

            result = runner.invoke(app, ["settings", "set", "model", "gpt-4"])

            assert result.exit_code == 0


# ============================================================================
# Process Commands
# ============================================================================


class TestProcessCommands:
    """Critical tests for process CLI commands."""

    def test_process_missing_speaker(self, runner):
        """Test process with non-existent speaker."""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_mgr,
            patch("moves_cli.main.settings_editor_instance") as mock_set,
        ):
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = Exception("Speaker not found")
            mock_mgr.return_value = mock_manager

            mock_settings = MagicMock()
            mock_settings.list.return_value = Settings(model="gpt-4", key="test")
            mock_set.return_value = mock_settings

            result = runner.invoke(app, ["speaker", "process", "nonexistent-id"])

            assert result.exit_code == 1
            assert (
                "not found" in result.output.lower() or "error" in result.output.lower()
            )

    def test_process_missing_api_key(self, runner, mock_speaker):
        """Test process without API key."""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_spk,
            patch("moves_cli.main.settings_editor_instance") as mock_set,
        ):
            mock_speaker_mgr = MagicMock()
            mock_speaker_mgr.resolve.return_value = mock_speaker
            mock_spk.return_value = mock_speaker_mgr

            mock_settings_ed = MagicMock()
            mock_settings_ed.list.return_value = Settings(model="gpt-4", key="")
            mock_set.return_value = mock_settings_ed

            result = runner.invoke(app, ["speaker", "process", "john-doe-abc12"])

            assert result.exit_code == 1
            assert "api key" in result.output.lower() or "key" in result.output.lower()


# ============================================================================
# Present Commands
# ============================================================================


class TestPresentCommands:
    """Critical tests for present CLI commands."""

    def test_present_missing_speaker(self, runner):
        """Test present with non-existent speaker."""
        with patch("moves_cli.main.speaker_manager_instance") as mock_mgr:
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = Exception("Speaker not found")
            mock_mgr.return_value = mock_manager

            result = runner.invoke(app, ["presentation", "control", "nonexistent-id"])

            assert result.exit_code == 1
            assert (
                "not found" in result.output.lower() or "error" in result.output.lower()
            )

    def test_present_no_sections(self, runner, mock_speaker, tmp_path):
        """Test present without processed sections."""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_spk,
            patch("moves_cli.main.data_handler") as mock_data,
        ):
            mock_speaker_mgr = MagicMock()
            mock_speaker_mgr.resolve.return_value = mock_speaker
            mock_spk.return_value = mock_speaker_mgr

            # Simulate missing sections file
            mock_data.DATA_FOLDER = tmp_path

            result = runner.invoke(app, ["presentation", "control", "john-doe-abc12"])

            assert result.exit_code == 1
