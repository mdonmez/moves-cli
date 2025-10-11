import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typer.testing import CliRunner
from moves_cli.main import app
from moves_cli.data.models import Speaker, Section, Settings, ProcessResult


@pytest.fixture
def runner():
    """Create a Typer CLI runner for testing"""
    return CliRunner()


@pytest.fixture
def mock_speaker():
    """Create a mock speaker for testing"""
    return Speaker(
        speaker_id="john-doe-abc12",
        name="John Doe",
        source_presentation=Path("/path/to/presentation.pdf"),
        source_transcript=Path("/path/to/transcript.pdf"),
    )


@pytest.fixture
def mock_speakers():
    """Create multiple mock speakers for testing"""
    return [
        Speaker(
            speaker_id="john-doe-abc12",
            name="John Doe",
            source_presentation=Path("/path/to/john_presentation.pdf"),
            source_transcript=Path("/path/to/john_transcript.pdf"),
        ),
        Speaker(
            speaker_id="jane-smith-xyz78",
            name="Jane Smith",
            source_presentation=Path("/path/to/jane_presentation.pdf"),
            source_transcript=Path("/path/to/jane_transcript.pdf"),
        ),
        Speaker(
            speaker_id="bob-jones-def45",
            name="Bob Jones",
            source_presentation=Path("/path/to/bob_presentation.pdf"),
            source_transcript=Path("/path/to/bob_transcript.pdf"),
        ),
    ]


@pytest.fixture
def mock_sections():
    """Create mock sections for testing"""
    return [
        Section(content="Section zero content", section_index=0),
        Section(content="Section one content", section_index=1),
        Section(content="Section two content", section_index=2),
    ]


@pytest.fixture
def mock_settings():
    """Create mock settings for testing"""
    return Settings(model="gemini/gemini-2.0-flash", key="test-api-key-12345")


@pytest.fixture
def mock_settings_no_key():
    """Create mock settings without API key"""
    return Settings(model="gemini/gemini-2.0-flash", key="")


@pytest.fixture
def mock_settings_no_model():
    """Create mock settings without model"""
    return Settings(model="", key="test-api-key-12345")


@pytest.fixture
def mock_processing_result():
    """Create a mock processing result"""
    return ProcessResult(
        section_count=15,
        transcript_from="SOURCE",
        presentation_from="SOURCE",
    )


class TestSpeakerAddCommand:
    """Test speaker add command"""

    def test_speaker_add_with_valid_files(self, runner, mock_speaker, tmp_path):
        """Test adding speaker with valid files"""
        # Create temporary files
        presentation_file = tmp_path / "presentation.pdf"
        transcript_file = tmp_path / "transcript.pdf"
        presentation_file.write_text("presentation content")
        transcript_file.write_text("transcript content")

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.add.return_value = mock_speaker
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                [
                    "speaker",
                    "add",
                    "John Doe",
                    str(presentation_file),
                    str(transcript_file),
                ],
            )

            assert result.exit_code == 0
            assert "Speaker 'John Doe' (john-doe-abc12) added." in result.output
            assert "ID -> john-doe-abc12" in result.output
            mock_manager.add.assert_called_once()

    def test_speaker_add_with_missing_presentation_file(self, runner, tmp_path):
        """Test adding speaker with missing presentation file"""
        # Create only transcript file
        transcript_file = tmp_path / "transcript.pdf"
        transcript_file.write_text("transcript content")
        presentation_file = tmp_path / "nonexistent_presentation.pdf"

        result = runner.invoke(
            app,
            [
                "speaker",
                "add",
                "John Doe",
                str(presentation_file),
                str(transcript_file),
            ],
        )

        assert result.exit_code == 1
        assert "Could not add speaker 'John Doe'." in result.output
        assert "Presentation file not found" in result.output

    def test_speaker_add_with_missing_transcript_file(self, runner, tmp_path):
        """Test adding speaker with missing transcript file"""
        # Create only presentation file
        presentation_file = tmp_path / "presentation.pdf"
        presentation_file.write_text("presentation content")
        transcript_file = tmp_path / "nonexistent_transcript.pdf"

        result = runner.invoke(
            app,
            [
                "speaker",
                "add",
                "John Doe",
                str(presentation_file),
                str(transcript_file),
            ],
        )

        assert result.exit_code == 1
        assert "Could not add speaker 'John Doe'." in result.output
        assert "Transcript file not found" in result.output

    def test_speaker_add_with_both_files_missing(self, runner, tmp_path):
        """Test adding speaker with both files missing"""
        presentation_file = tmp_path / "nonexistent_presentation.pdf"
        transcript_file = tmp_path / "nonexistent_transcript.pdf"

        result = runner.invoke(
            app,
            [
                "speaker",
                "add",
                "John Doe",
                str(presentation_file),
                str(transcript_file),
            ],
        )

        assert result.exit_code == 1
        assert "Could not add speaker 'John Doe'." in result.output
        # Should fail on presentation first
        assert "Presentation file not found" in result.output

    def test_speaker_add_handles_exception(self, runner, mock_speaker, tmp_path):
        """Test adding speaker handles exception from manager"""
        # Create temporary files
        presentation_file = tmp_path / "presentation.pdf"
        transcript_file = tmp_path / "transcript.pdf"
        presentation_file.write_text("presentation content")
        transcript_file.write_text("transcript content")

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.add.side_effect = Exception("Database error")
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                [
                    "speaker",
                    "add",
                    "John Doe",
                    str(presentation_file),
                    str(transcript_file),
                ],
            )

            assert result.exit_code == 1
            assert "Could not add speaker 'John Doe'." in result.output
            assert "Database error" in result.output


class TestSpeakerEditCommand:
    """Test speaker edit command"""

    def test_speaker_edit_presentation_only(self, runner, mock_speaker, tmp_path):
        """Test editing speaker presentation file only"""
        new_presentation = tmp_path / "new_presentation.pdf"
        new_presentation.write_text("new presentation content")

        updated_speaker = Speaker(
            speaker_id=mock_speaker.speaker_id,
            name=mock_speaker.name,
            source_presentation=new_presentation,
            source_transcript=mock_speaker.source_transcript,
        )

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.edit.return_value = updated_speaker
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                [
                    "speaker",
                    "edit",
                    "John Doe",
                    "--presentation",
                    str(new_presentation),
                ],
            )

            assert result.exit_code == 0
            assert "Speaker 'John Doe' updated." in result.output
            assert "Presentation ->" in result.output
            mock_manager.edit.assert_called_once()

    def test_speaker_edit_transcript_only(self, runner, mock_speaker, tmp_path):
        """Test editing speaker transcript file only"""
        new_transcript = tmp_path / "new_transcript.pdf"
        new_transcript.write_text("new transcript content")

        updated_speaker = Speaker(
            speaker_id=mock_speaker.speaker_id,
            name=mock_speaker.name,
            source_presentation=mock_speaker.source_presentation,
            source_transcript=new_transcript,
        )

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.edit.return_value = updated_speaker
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                ["speaker", "edit", "John Doe", "--transcript", str(new_transcript)],
            )

            assert result.exit_code == 0
            assert "Speaker 'John Doe' updated." in result.output
            assert "Transcript ->" in result.output

    def test_speaker_edit_both_files(self, runner, mock_speaker, tmp_path):
        """Test editing both presentation and transcript files"""
        new_presentation = tmp_path / "new_presentation.pdf"
        new_transcript = tmp_path / "new_transcript.pdf"
        new_presentation.write_text("new presentation content")
        new_transcript.write_text("new transcript content")

        updated_speaker = Speaker(
            speaker_id=mock_speaker.speaker_id,
            name=mock_speaker.name,
            source_presentation=new_presentation,
            source_transcript=new_transcript,
        )

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.edit.return_value = updated_speaker
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                [
                    "speaker",
                    "edit",
                    "John Doe",
                    "--presentation",
                    str(new_presentation),
                    "--transcript",
                    str(new_transcript),
                ],
            )

            assert result.exit_code == 0
            assert "Speaker 'John Doe' updated." in result.output
            assert "Presentation ->" in result.output
            assert "Transcript ->" in result.output

    def test_speaker_edit_with_no_parameters(self, runner):
        """Test editing speaker with no parameters fails"""
        result = runner.invoke(app, ["speaker", "edit", "John Doe"])

        assert result.exit_code == 1
        assert "At least one update parameter" in result.output

    def test_speaker_edit_with_missing_presentation_file(
        self, runner, mock_speaker, tmp_path
    ):
        """Test editing speaker with missing presentation file"""
        nonexistent_file = tmp_path / "nonexistent.pdf"

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                [
                    "speaker",
                    "edit",
                    "John Doe",
                    "--presentation",
                    str(nonexistent_file),
                ],
            )

            assert result.exit_code == 1
            assert "Could not update speaker 'John Doe'." in result.output
            assert "Presentation file not found" in result.output

    def test_speaker_edit_with_missing_transcript_file(
        self, runner, mock_speaker, tmp_path
    ):
        """Test editing speaker with missing transcript file"""
        nonexistent_file = tmp_path / "nonexistent.pdf"

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                ["speaker", "edit", "John Doe", "--transcript", str(nonexistent_file)],
            )

            assert result.exit_code == 1
            assert "Could not update speaker 'John Doe'." in result.output
            assert "Transcript file not found" in result.output

    def test_speaker_edit_handles_exception(self, runner, mock_speaker, tmp_path):
        """Test editing speaker handles exception"""
        new_presentation = tmp_path / "new_presentation.pdf"
        new_presentation.write_text("new presentation content")

        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = Exception("Speaker not found")
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app,
                [
                    "speaker",
                    "edit",
                    "John Doe",
                    "--presentation",
                    str(new_presentation),
                ],
            )

            assert result.exit_code == 1
            assert "Error:" in result.output
            assert "Speaker not found" in result.output


class TestSpeakerListCommand:
    """Test speaker list command"""

    def test_speaker_list_with_speakers(self, runner, mock_speakers):
        """Test listing speakers when speakers exist"""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.data_handler") as mock_data_handler,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = mock_speakers
            mock_manager_func.return_value = mock_manager

            # Mock DATA_FOLDER and sections file check
            mock_data_handler.DATA_FOLDER = Path("/mock/data")

            result = runner.invoke(app, ["speaker", "list"])

            assert result.exit_code == 0
            assert "Registered Speakers (3)" in result.output
            assert "john-doe-abc12" in result.output
            assert "Jane Smith" in result.output
            assert "bob-jones-def45" in result.output

    def test_speaker_list_with_no_speakers(self, runner):
        """Test listing speakers when no speakers exist"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.list.return_value = []
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "list"])

            assert result.exit_code == 0
            assert "No speakers are registered." in result.output

    def test_speaker_list_handles_exception(self, runner):
        """Test speaker list handles exception"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.list.side_effect = Exception("Database error")
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "list"])

            assert result.exit_code == 1
            assert "Error accessing speaker data" in result.output
            assert "Database error" in result.output


class TestSpeakerShowCommand:
    """Test speaker show command"""

    def test_speaker_show_displays_details(self, runner, mock_speaker):
        """Test showing speaker details"""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.data_handler") as mock_data_handler,
        ):
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager_func.return_value = mock_manager

            # Mock DATA_FOLDER
            mock_data_handler.DATA_FOLDER = Path("/mock/data")

            result = runner.invoke(app, ["speaker", "show", "John Doe"])

            assert result.exit_code == 0
            assert "Showing details for speaker 'John Doe'" in result.output
            assert "john-doe-abc12" in result.output
            assert "Name -> John Doe" in result.output
            assert "Status ->" in result.output

    def test_speaker_show_handles_exception(self, runner):
        """Test speaker show handles exception"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = Exception("Speaker not found")
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "show", "John Doe"])

            assert result.exit_code == 1
            assert "Error:" in result.output
            assert "Speaker not found" in result.output


class TestSpeakerProcessCommand:
    """Test speaker process command"""

    def test_speaker_process_single_speaker(
        self, runner, mock_speaker, mock_settings, mock_processing_result
    ):
        """Test processing single speaker"""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.settings_editor_instance") as mock_settings_func,
        ):
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.process.return_value = [mock_processing_result]
            mock_manager_func.return_value = mock_manager

            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process", "John Doe"])

            assert result.exit_code == 0
            assert "Processing speaker 'John Doe'" in result.output
            assert "15 sections created." in result.output
            mock_manager.process.assert_called_once()

    def test_speaker_process_multiple_speakers(
        self, runner, mock_speakers, mock_settings
    ):
        """Test processing multiple speakers"""
        results = [
            ProcessResult(
                section_count=15,
                transcript_from="SOURCE",
                presentation_from="SOURCE",
            ),
            ProcessResult(
                section_count=20,
                transcript_from="SOURCE",
                presentation_from="SOURCE",
            ),
            ProcessResult(
                section_count=18,
                transcript_from="SOURCE",
                presentation_from="SOURCE",
            ),
        ]

        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.settings_editor_instance") as mock_settings_func,
        ):
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = mock_speakers
            mock_manager.process.return_value = results
            mock_manager_func.return_value = mock_manager

            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(
                app, ["speaker", "process", "John Doe", "Jane Smith", "Bob Jones"]
            )

            assert result.exit_code == 0
            assert "Processing 3 speakers..." in result.output
            assert "3 speakers processed." in result.output
            assert "15 sections created" in result.output
            assert "20 sections created" in result.output

    def test_speaker_process_all_speakers(self, runner, mock_speakers, mock_settings):
        """Test processing all speakers"""
        results = [
            ProcessResult(
                section_count=15,
                transcript_from="SOURCE",
                presentation_from="SOURCE",
            ),
            ProcessResult(
                section_count=20,
                transcript_from="SOURCE",
                presentation_from="SOURCE",
            ),
            ProcessResult(
                section_count=18,
                transcript_from="SOURCE",
                presentation_from="SOURCE",
            ),
        ]

        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.settings_editor_instance") as mock_settings_func,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = mock_speakers
            mock_manager.process.return_value = results
            mock_manager_func.return_value = mock_manager

            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process", "--all"])

            assert result.exit_code == 0
            assert "Processing 3 speakers..." in result.output
            assert "3 speakers processed." in result.output

    def test_speaker_process_without_model(self, runner, mock_settings_no_model):
        """Test processing without model configured"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings_no_model
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process", "John Doe"])

            assert result.exit_code == 1
            assert "LLM model not configured" in result.output

    def test_speaker_process_without_api_key(self, runner, mock_settings_no_key):
        """Test processing without API key configured"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings_no_key
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process", "John Doe"])

            assert result.exit_code == 1
            assert "LLM API key not configured" in result.output

    def test_speaker_process_with_no_arguments(self, runner):
        """Test processing with no speakers specified"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = Settings(
                model="test-model", key="test-key"
            )
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process"])

            assert result.exit_code == 1
            assert "Either provide speaker names or use --all" in result.output

    def test_speaker_process_all_with_no_speakers(self, runner, mock_settings):
        """Test processing all when no speakers exist"""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.settings_editor_instance") as mock_settings_func,
        ):
            mock_manager = MagicMock()
            mock_manager.list.return_value = []
            mock_manager_func.return_value = mock_manager

            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process", "--all"])

            assert result.exit_code == 0
            assert "No speakers found to process." in result.output

    def test_speaker_process_handles_exception(
        self, runner, mock_speaker, mock_settings
    ):
        """Test speaker process handles exception"""
        with (
            patch("moves_cli.main.speaker_manager_instance") as mock_manager_func,
            patch("moves_cli.main.settings_editor_instance") as mock_settings_func,
        ):
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.process.side_effect = Exception("Processing error")
            mock_manager_func.return_value = mock_manager

            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["speaker", "process", "John Doe"])

            assert result.exit_code == 1
            assert "Processing error:" in result.output
            assert "Processing error" in result.output


class TestSpeakerDeleteCommand:
    """Test speaker delete command"""

    def test_speaker_delete_single_speaker(self, runner, mock_speaker):
        """Test deleting single speaker"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.delete.return_value = True
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "delete", "John Doe"])

            assert result.exit_code == 0
            assert "Deleting 1 speaker(s)..." in result.output
            assert "Speaker 'John Doe' (john-doe-abc12) deleted." in result.output
            mock_manager.delete.assert_called_once()

    def test_speaker_delete_multiple_speakers(self, runner, mock_speakers):
        """Test deleting multiple speakers"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = mock_speakers
            mock_manager.delete.return_value = True
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(
                app, ["speaker", "delete", "John Doe", "Jane Smith", "Bob Jones"]
            )

            assert result.exit_code == 0
            assert "Deleting 3 speaker(s)..." in result.output
            assert "Speaker 'John Doe'" in result.output
            assert "Speaker 'Jane Smith'" in result.output
            assert "Speaker 'Bob Jones'" in result.output

    def test_speaker_delete_all_speakers(self, runner, mock_speakers):
        """Test deleting all speakers"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.list.return_value = mock_speakers
            mock_manager.delete.return_value = True
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "delete", "--all"])

            assert result.exit_code == 0
            assert "Deleting 3 speaker(s)..." in result.output

    def test_speaker_delete_with_no_arguments(self, runner):
        """Test deleting with no speakers specified"""
        result = runner.invoke(app, ["speaker", "delete"])

        assert result.exit_code == 1
        assert "Either provide speaker names or use --all" in result.output

    def test_speaker_delete_all_with_no_speakers(self, runner):
        """Test deleting all when no speakers exist"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.list.return_value = []
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "delete", "--all"])

            assert result.exit_code == 0
            assert "No speakers found to delete." in result.output

    def test_speaker_delete_failure(self, runner, mock_speaker):
        """Test deleting speaker when deletion fails"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.return_value = mock_speaker
            mock_manager.delete.return_value = False
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "delete", "John Doe"])

            assert result.exit_code == 1
            assert "Could not delete speaker 'John Doe'." in result.output
            assert "Failed to delete speaker data." in result.output

    def test_speaker_delete_handles_exception(self, runner):
        """Test speaker delete handles exception"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = Exception("Speaker not found")
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["speaker", "delete", "John Doe"])

            assert result.exit_code == 1
            assert "Error:" in result.output
            assert "Speaker not found" in result.output


class TestPresentationControlCommand:
    """Test presentation control command

    Note: Full integration tests for presentation control are skipped due to
    complex mocking requirements with litellm. Basic error handling is tested.
    """

    def test_presentation_control_handles_speaker_not_found(self, runner):
        """Test presentation control handles speaker not found"""
        with patch("moves_cli.main.speaker_manager_instance") as mock_manager_func:
            mock_manager = MagicMock()
            mock_manager.resolve.side_effect = Exception("Speaker not found")
            mock_manager_func.return_value = mock_manager

            result = runner.invoke(app, ["presentation", "control", "Unknown"])

            assert result.exit_code == 1


class TestSettingsListCommand:
    """Test settings list command"""

    def test_settings_list_with_all_settings(self, runner, mock_settings):
        """Test listing settings with all values configured"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "list"])

            assert result.exit_code == 0
            assert "Application Settings." in result.output
            assert "model (LLM Model) -> gemini/gemini-2.0-flash" in result.output
            assert "key (API Key) -> test-api-key-12345" in result.output

    def test_settings_list_with_missing_model(self, runner, mock_settings_no_model):
        """Test listing settings with missing model"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings_no_model
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "list"])

            assert result.exit_code == 0
            assert "model (LLM Model) -> Not configured" in result.output
            assert "key (API Key) -> test-api-key-12345" in result.output

    def test_settings_list_with_missing_key(self, runner, mock_settings_no_key):
        """Test listing settings with missing API key"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.return_value = mock_settings_no_key
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "list"])

            assert result.exit_code == 0
            assert "model (LLM Model) -> gemini/gemini-2.0-flash" in result.output
            assert "key (API Key) -> Not configured" in result.output

    def test_settings_list_handles_exception(self, runner):
        """Test settings list handles exception"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.list.side_effect = Exception("Settings file corrupt")
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "list"])

            assert result.exit_code == 1
            assert "Error accessing settings" in result.output
            assert "Settings file corrupt" in result.output


class TestSettingsSetCommand:
    """Test settings set command"""

    def test_settings_set_model(self, runner):
        """Test setting model value"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.set.return_value = True
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "set", "model", "gpt-4"])

            assert result.exit_code == 0
            assert "Setting 'model' updated." in result.output
            assert "New Value -> gpt-4" in result.output
            mock_settings_editor.set.assert_called_once_with("model", "gpt-4")

    def test_settings_set_key(self, runner):
        """Test setting API key value"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.set.return_value = True
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "set", "key", "new-api-key-xyz"])

            assert result.exit_code == 0
            assert "Setting 'key' updated." in result.output
            assert "New Value -> new-api-key-xyz" in result.output
            mock_settings_editor.set.assert_called_once_with("key", "new-api-key-xyz")

    def test_settings_set_invalid_key(self, runner):
        """Test setting invalid key name"""
        result = runner.invoke(app, ["settings", "set", "invalid_key", "value"])

        assert result.exit_code == 1
        assert "Invalid setting key 'invalid_key'" in result.output
        assert "Valid keys: model, key" in result.output

    def test_settings_set_failure(self, runner):
        """Test setting when set operation fails"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.set.return_value = False
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "set", "model", "gpt-4"])

            assert result.exit_code == 1
            assert "Could not update setting 'model'." in result.output

    def test_settings_set_handles_exception(self, runner):
        """Test settings set handles exception"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.set.side_effect = Exception("Permission denied")
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "set", "model", "gpt-4"])

            assert result.exit_code == 1
            assert "Unexpected error:" in result.output
            assert "Permission denied" in result.output


class TestSettingsUnsetCommand:
    """Test settings unset command"""

    def test_settings_unset_model(self, runner):
        """Test unsetting model to default"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.unset.return_value = True
            mock_settings_editor._template_defaults = {
                "model": "gemini/gemini-2.0-flash"
            }
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "unset", "model"])

            assert result.exit_code == 0
            assert "Setting 'model' reset to default." in result.output
            assert "New Value -> gemini/gemini-2.0-flash" in result.output
            mock_settings_editor.unset.assert_called_once_with("model")

    def test_settings_unset_key(self, runner):
        """Test unsetting API key to default (None)"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.unset.return_value = True
            mock_settings_editor._template_defaults = {"key": None}
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "unset", "key"])

            assert result.exit_code == 0
            assert "Setting 'key' reset to default." in result.output
            assert "New Value -> Not configured" in result.output

    def test_settings_unset_invalid_key(self, runner):
        """Test unsetting invalid key name"""
        result = runner.invoke(app, ["settings", "unset", "invalid_key"])

        assert result.exit_code == 1
        assert "Invalid setting key 'invalid_key'" in result.output
        assert "Valid keys: model, key" in result.output

    def test_settings_unset_failure(self, runner):
        """Test unsetting when unset operation fails"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.unset.return_value = False
            mock_settings_editor._template_defaults = {"model": "default-model"}
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "unset", "model"])

            assert result.exit_code == 1
            assert "Could not reset setting 'model'." in result.output

    def test_settings_unset_handles_exception(self, runner):
        """Test settings unset handles exception"""
        with patch("moves_cli.main.settings_editor_instance") as mock_settings_func:
            mock_settings_editor = MagicMock()
            mock_settings_editor.unset.side_effect = Exception("File locked")
            mock_settings_editor._template_defaults = {"model": "default"}
            mock_settings_func.return_value = mock_settings_editor

            result = runner.invoke(app, ["settings", "unset", "model"])

            assert result.exit_code == 1
            assert "Unexpected error:" in result.output
            assert "File locked" in result.output


class TestVersionCallback:
    """Test version callback"""

    def test_version_flag_displays_version(self, runner):
        """Test that --version displays version"""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.return_value = "1.0.0"

            result = runner.invoke(app, ["--version"])

            assert result.exit_code == 0
            assert "moves-cli version 1.0.0" in result.output

    def test_version_flag_handles_error(self, runner):
        """Test that --version handles error gracefully"""
        with patch("importlib.metadata.version") as mock_version:
            mock_version.side_effect = Exception("Version not found")

            result = runner.invoke(app, ["--version"])

            assert result.exit_code == 0
            assert "Error retrieving version" in result.output
