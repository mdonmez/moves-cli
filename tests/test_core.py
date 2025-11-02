"""Consolidated tests for core modules."""

import pytest
from unittest.mock import patch, MagicMock

from moves_cli.core.settings_editor import SettingsEditor
from moves_cli.core.speaker_manager import SpeakerManager
from moves_cli.core.presentation_controller import PresentationController
from moves_cli.data.models import Section
from moves_cli.utils import data_handler


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_data_folder(tmp_path, monkeypatch):
    """Replace DATA_FOLDER with a temporary directory for testing."""
    monkeypatch.setattr(data_handler, "DATA_FOLDER", tmp_path)
    return tmp_path


@pytest.fixture
def temp_settings_template(tmp_path, monkeypatch):
    """Create a temporary settings template."""
    template_path = tmp_path / "settings_template.toml"
    template_content = """model = "gemini/gemini-2.0-flash"
key = "None"
"""
    template_path.write_text(template_content, encoding="utf-8")
    monkeypatch.setattr(SettingsEditor, "template", template_path)
    return template_path


@pytest.fixture
def settings_editor(mock_data_folder, temp_settings_template, monkeypatch):
    """Create a SettingsEditor instance for testing."""
    settings_path = mock_data_folder / "settings.toml"
    monkeypatch.setattr(SettingsEditor, "settings", settings_path)
    return SettingsEditor()


@pytest.fixture
def speaker_manager(mock_data_folder):
    """Create a SpeakerManager instance."""
    return SpeakerManager()


@pytest.fixture
def sample_files(tmp_path):
    """Create sample presentation and transcript files."""
    presentation = tmp_path / "presentation.pdf"
    transcript = tmp_path / "transcript.pdf"
    presentation.write_text("Sample presentation content")
    transcript.write_text("Sample transcript content")
    return {"presentation": presentation, "transcript": transcript}


@pytest.fixture
def sample_sections():
    """Create sample sections for testing."""
    return [
        Section(content="Section zero content", section_index=0),
        Section(content="Section one content", section_index=1),
        Section(content="Section two content", section_index=2),
    ]


@pytest.fixture
def mock_recognizer():
    """Mock the OnlineRecognizer."""
    with patch("moves_cli.core.presentation_controller.OnlineRecognizer") as mock:
        mock_instance = MagicMock()
        # Make create_stream return a new mock each time it's called
        mock_instance.create_stream.side_effect = lambda: MagicMock()
        mock.from_transducer.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice."""
    with patch("moves_cli.core.presentation_controller.sd") as mock:
        mock.default.device = [0, 0]
        yield mock


@pytest.fixture
def mock_keyboard():
    """Mock keyboard controller and listener."""
    with (
        patch("moves_cli.core.presentation_controller.Controller") as mock_controller,
        patch("moves_cli.core.presentation_controller.Listener") as mock_listener,
    ):
        yield {"controller": mock_controller, "listener": mock_listener}


# ============================================================================
# Settings Editor Tests
# ============================================================================


class TestSettingsEditor:
    """Critical tests for settings management."""

    def test_initialization_creates_settings_file(
        self, mock_data_folder, temp_settings_template, monkeypatch
    ):
        """Test settings file creation on initialization."""
        settings_path = mock_data_folder / "settings.toml"
        assert not settings_path.exists()

        monkeypatch.setattr(SettingsEditor, "settings", settings_path)
        SettingsEditor()

        assert settings_path.exists()

    def test_loads_defaults_from_template(self, settings_editor):
        """Test default values from template."""
        settings = settings_editor.list()

        assert settings.model == "gemini/gemini-2.0-flash"
        assert settings.key == "None"

    def test_set_and_get_value(self, settings_editor):
        """Test setting and retrieving values."""
        assert settings_editor.set("model", "gpt-4")

        settings = settings_editor.list()
        assert settings.model == "gpt-4"

    def test_preserves_existing_settings(
        self, mock_data_folder, temp_settings_template, monkeypatch
    ):
        """Test existing settings are preserved."""
        settings_path = mock_data_folder / "settings.toml"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(
            'model = "custom-model"\nkey = "custom-key"\n', encoding="utf-8"
        )

        monkeypatch.setattr(SettingsEditor, "settings", settings_path)
        editor = SettingsEditor()
        settings = editor.list()

        assert settings.model == "custom-model"
        assert settings.key == "custom-key"

    def test_handles_corrupted_settings(
        self, mock_data_folder, temp_settings_template, monkeypatch
    ):
        """Test graceful handling of corrupted settings."""
        settings_path = mock_data_folder / "settings.toml"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text("invalid toml [[[content", encoding="utf-8")

        monkeypatch.setattr(SettingsEditor, "settings", settings_path)
        editor = SettingsEditor()
        settings = editor.list()

        # Should fall back to defaults
        assert settings.model == "gemini/gemini-2.0-flash"


# ============================================================================
# Speaker Manager Tests
# ============================================================================


class TestSpeakerManager:
    """Critical tests for speaker management."""

    def test_add_speaker(self, speaker_manager, sample_files, mock_data_folder):
        """Test adding a new speaker."""
        name = "John Doe"
        speaker = speaker_manager.add(
            name, sample_files["presentation"], sample_files["transcript"]
        )

        assert speaker.name == name
        assert speaker.speaker_id.startswith("john-doe-")
        assert speaker.source_presentation == sample_files["presentation"].resolve()

        # Verify speaker.json was created
        speaker_folder = mock_data_folder / "speakers" / speaker.speaker_id
        assert (speaker_folder / "speaker.json").exists()

    def test_add_multiple_speakers_same_name(self, speaker_manager, sample_files):
        """Test multiple speakers can have the same name."""
        name = "John Doe"
        speaker1 = speaker_manager.add(
            name, sample_files["presentation"], sample_files["transcript"]
        )
        speaker2 = speaker_manager.add(
            name, sample_files["presentation"], sample_files["transcript"]
        )

        assert speaker1.speaker_id != speaker2.speaker_id
        assert speaker1.name == speaker2.name

    def test_list_speakers(self, speaker_manager, sample_files):
        """Test listing all speakers."""
        speaker_manager.add(
            "Alice", sample_files["presentation"], sample_files["transcript"]
        )
        speaker_manager.add(
            "Bob", sample_files["presentation"], sample_files["transcript"]
        )

        speakers = speaker_manager.list()

        assert len(speakers) == 2
        assert any(s.name == "Alice" for s in speakers)
        assert any(s.name == "Bob" for s in speakers)

    def test_delete_speaker(self, speaker_manager, sample_files, mock_data_folder):
        """Test deleting a speaker."""
        speaker = speaker_manager.add(
            "John Doe", sample_files["presentation"], sample_files["transcript"]
        )
        speaker_folder = mock_data_folder / "speakers" / speaker.speaker_id
        assert speaker_folder.exists()

        result = speaker_manager.delete(speaker)

        assert result is True
        assert not speaker_folder.exists()

    def test_handles_special_characters_in_name(self, speaker_manager, sample_files):
        """Test special characters in speaker names."""
        name = "María García-López Jr."
        speaker = speaker_manager.add(
            name, sample_files["presentation"], sample_files["transcript"]
        )

        assert speaker.name == name
        # ID should be URL-safe
        assert all(c.isalnum() or c in "-_" for c in speaker.speaker_id)


# ============================================================================
# Presentation Controller Tests
# ============================================================================


class TestPresentationController:
    """Critical tests for presentation control."""

    def test_initialization(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test basic initialization."""
        start_section = sample_sections[0]
        controller = PresentationController(
            sample_sections, start_section, window_size=8
        )

        assert controller.sections == sample_sections
        assert controller.current_section == start_section
        assert controller.window_size == 8

    def test_custom_window_size(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test initialization with custom window size."""
        controller = PresentationController(
            sample_sections, sample_sections[0], window_size=20
        )

        assert controller.window_size == 20

    def test_different_start_section(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test starting from a different section."""
        start_section = sample_sections[1]
        controller = PresentationController(
            sample_sections, start_section, window_size=8
        )

        assert controller.current_section == start_section
        assert controller.current_section.section_index == 1

    def test_audio_buffer_initialization(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test audio buffer is initialized."""
        controller = PresentationController(
            sample_sections, sample_sections[0], window_size=8
        )

        # Verify controller was initialized without errors
        assert controller.frame_duration == 0.1

    def test_pause_clears_audio_queue(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test that pausing clears the audio queue."""
        controller = PresentationController(
            sample_sections, sample_sections[0], window_size=8
        )

        # Add some data to the audio queue
        import numpy as np

        controller.audio_queue.append(np.array([1.0, 2.0, 3.0]))
        controller.audio_queue.append(np.array([4.0, 5.0, 6.0]))

        assert len(controller.audio_queue) == 2

        # Pause should clear the queue
        controller._toggle_pause()

        assert controller.paused is True
        assert len(controller.audio_queue) == 0

    def test_resume_resets_stream_and_word_buffers(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test that resuming resets STT stream and clears word buffers."""
        controller = PresentationController(
            sample_sections, sample_sections[0], window_size=8
        )

        # Add some data to word buffers
        controller.recent_words.extend(["hello", "world", "test"])
        controller.previous_recent_words = ["previous", "words"]

        # Store the initial stream
        initial_stream = controller.stream

        # Pause first
        controller._toggle_pause()
        assert controller.paused is True

        # Resume should reset stream and clear word buffers
        controller._toggle_pause()

        assert controller.paused is False
        assert len(controller.recent_words) == 0
        assert controller.previous_recent_words == []
        # Stream should be a new instance after resume
        assert controller.stream != initial_stream

    def test_audio_callback_respects_pause(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test that audio callback doesn't add data when paused."""
        controller = PresentationController(
            sample_sections, sample_sections[0], window_size=8
        )

        import numpy as np

        test_audio = np.array([[1.0], [2.0], [3.0], [4.0], [5.0]])

        # Add audio when not paused
        controller._audio_callback(test_audio, None, None, None)
        assert len(controller.audio_queue) == 1

        # Pause and try to add more audio
        controller._toggle_pause()
        controller._audio_callback(test_audio, None, None, None)

        # Queue should still be empty (cleared on pause)
        assert len(controller.audio_queue) == 0

        # Resume and add audio again
        controller._toggle_pause()
        controller._audio_callback(test_audio, None, None, None)
        assert len(controller.audio_queue) == 1

    def test_process_audio_skips_when_paused(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test that process_audio skips processing when paused."""
        controller = PresentationController(
            sample_sections, sample_sections[0], window_size=8
        )

        import numpy as np

        controller.audio_queue.append(np.array([1.0, 2.0, 3.0]))

        # Pause the controller
        controller.paused = True

        # Set shutdown flag to exit after one iteration
        controller.shutdown_flag.set()

        # Process audio should not process the queue when paused
        controller.process_audio()

        # Queue should still have data (wasn't processed)
        assert len(controller.audio_queue) == 1
        # Stream should not have been called with waveform
        assert not controller.stream.accept_waveform.called
