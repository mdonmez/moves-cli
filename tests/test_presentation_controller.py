import pytest
from unittest.mock import patch, MagicMock
from collections import deque
import threading
from moves_cli.core.presentation_controller import PresentationController
from moves_cli.data.models import Section


@pytest.fixture
def sample_sections():
    """Create sample sections for testing"""
    return [
        Section(content="Section zero content", section_index=0),
        Section(content="Section one content", section_index=1),
        Section(content="Section two content", section_index=2),
        Section(content="Section three content", section_index=3),
        Section(content="Section four content", section_index=4),
    ]


@pytest.fixture
def start_section(sample_sections):
    """Get the starting section"""
    return sample_sections[0]


@pytest.fixture
def mock_recognizer():
    """Mock the OnlineRecognizer to avoid loading ML models"""
    with patch("moves_cli.core.presentation_controller.OnlineRecognizer") as mock:
        mock_instance = MagicMock()
        mock_stream = MagicMock()
        mock_instance.create_stream.return_value = mock_stream
        mock.from_transducer.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_sounddevice():
    """Mock sounddevice to avoid audio device initialization"""
    with patch("moves_cli.core.presentation_controller.sd") as mock:
        mock.default.device = [0, 0]  # [input, output]
        yield mock


@pytest.fixture
def mock_keyboard():
    """Mock keyboard controller and listener"""
    with (
        patch("moves_cli.core.presentation_controller.Controller") as mock_controller,
        patch("moves_cli.core.presentation_controller.Listener") as mock_listener,
    ):
        yield {"controller": mock_controller, "listener": mock_listener}


@pytest.fixture
def controller(
    sample_sections, start_section, mock_recognizer, mock_sounddevice, mock_keyboard
):
    """Create a PresentationController instance for testing"""
    return PresentationController(sample_sections, start_section)


class TestPresentationControllerInitialization:
    """Test PresentationController initialization"""

    def test_initialization_with_sections(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test initialization with sections"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.sections == sample_sections
        assert len(controller.sections) == 5

    def test_initialization_sets_current_section(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that current section is set to start section"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.current_section == start_section
        assert controller.current_section.section_index == 0

    def test_initialization_with_different_start_section(
        self, sample_sections, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test initialization with different start section"""
        start = sample_sections[2]
        controller = PresentationController(sample_sections, start)

        assert controller.current_section == start
        assert controller.current_section.section_index == 2

    def test_initialization_sets_window_size(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that window size is set correctly"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.window_size == 12

    def test_initialization_with_custom_window_size(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test initialization with custom window size"""
        controller = PresentationController(
            sample_sections, start_section, window_size=20
        )

        assert controller.window_size == 20

    def test_initialization_sets_frame_duration(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that frame duration is set"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.frame_duration == 0.1

    def test_initialization_sets_sample_rate(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that sample rate is set"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.sample_rate == 16000

    def test_initialization_creates_similarity_calculator(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that similarity calculator is created"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.similarity_calculator is not None
        from moves_cli.core.components.similarity_calculator import SimilarityCalculator

        assert isinstance(controller.similarity_calculator, SimilarityCalculator)

    def test_initialization_generates_chunks(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that chunks are generated from sections"""
        controller = PresentationController(sample_sections, start_section)

        assert controller.chunks is not None
        assert len(controller.chunks) > 0

    def test_initialization_creates_shutdown_flag(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that shutdown flag is created"""
        controller = PresentationController(sample_sections, start_section)

        assert isinstance(controller.shutdown_flag, threading.Event)
        assert not controller.shutdown_flag.is_set()


class TestAudioQueue:
    """Test audio queue initialization and size limit"""

    def test_audio_queue_is_created(self, controller):
        """Test that audio queue is created"""
        assert controller.audio_queue is not None

    def test_audio_queue_is_deque(self, controller):
        """Test that audio queue is a deque"""
        assert isinstance(controller.audio_queue, deque)

    def test_audio_queue_has_correct_size_limit(self, controller):
        """Test that audio queue has maxlen of 5"""
        assert controller.audio_queue.maxlen == 5

    def test_audio_queue_starts_empty(self, controller):
        """Test that audio queue starts empty"""
        assert len(controller.audio_queue) == 0

    def test_audio_queue_size_limit_enforced(self, controller):
        """Test that audio queue enforces size limit"""
        # Add more than maxlen items
        for i in range(10):
            controller.audio_queue.append(f"item_{i}")

        # Should only keep the last 5
        assert len(controller.audio_queue) == 5
        # Check that it's the last 5 items
        assert controller.audio_queue[0] == "item_5"
        assert controller.audio_queue[4] == "item_9"

    def test_audio_queue_fifo_behavior(self, controller):
        """Test that audio queue has FIFO behavior with size limit"""
        # Add exactly maxlen items
        for i in range(5):
            controller.audio_queue.append(f"item_{i}")

        # Add one more - should drop the first
        controller.audio_queue.append("item_5")

        assert len(controller.audio_queue) == 5
        assert "item_0" not in controller.audio_queue
        assert controller.audio_queue[0] == "item_1"
        assert controller.audio_queue[-1] == "item_5"


class TestKeyboardController:
    """Test keyboard controller initialization"""

    def test_keyboard_controller_is_created(self, controller):
        """Test that keyboard controller is created"""
        assert controller.keyboard_controller is not None

    def test_keyboard_controller_is_correct_type(self, controller, mock_keyboard):
        """Test that keyboard controller is a Controller instance"""
        # Should have been called to create the controller
        mock_keyboard["controller"].assert_called_once()

    def test_keyboard_listener_is_created(self, controller):
        """Test that keyboard listener is created"""
        assert controller.keyboard_listener is not None

    def test_keyboard_listener_has_on_press_handler(self, controller, mock_keyboard):
        """Test that keyboard listener is created with on_press handler"""
        # Listener should be called with on_press parameter
        mock_keyboard["listener"].assert_called_once()
        call_kwargs = mock_keyboard["listener"].call_args.kwargs
        assert "on_press" in call_kwargs


class TestNavigatorState:
    """Test navigator state initialization"""

    def test_navigator_working_starts_false(self, controller):
        """Test that navigator_working flag starts as False"""
        assert controller.navigator_working is False

    def test_paused_starts_false(self, controller):
        """Test that paused flag starts as False"""
        assert controller.paused is False

    def test_navigator_thread_is_created(self, controller):
        """Test that navigator thread is created"""
        assert controller.navigator is not None
        assert isinstance(controller.navigator, threading.Thread)

    def test_navigator_thread_is_daemon(self, controller):
        """Test that navigator thread is a daemon thread"""
        assert controller.navigator.daemon is True

    def test_navigator_thread_not_started(self, controller):
        """Test that navigator thread is not started during init"""
        # Thread should be created but not started
        assert not controller.navigator.is_alive()


class TestRecentWords:
    """Test recent words tracking initialization"""

    def test_recent_words_is_created(self, controller):
        """Test that recent_words deque is created"""
        assert controller.recent_words is not None

    def test_recent_words_is_deque(self, controller):
        """Test that recent_words is a deque"""
        assert isinstance(controller.recent_words, deque)

    def test_recent_words_has_window_size_limit(self, controller):
        """Test that recent_words maxlen equals window_size"""
        assert controller.recent_words.maxlen == controller.window_size
        assert controller.recent_words.maxlen == 12

    def test_recent_words_starts_empty(self, controller):
        """Test that recent_words starts empty"""
        assert len(controller.recent_words) == 0

    def test_previous_recent_words_is_list(self, controller):
        """Test that previous_recent_words is a list"""
        assert isinstance(controller.previous_recent_words, list)

    def test_previous_recent_words_starts_empty(self, controller):
        """Test that previous_recent_words starts empty"""
        assert len(controller.previous_recent_words) == 0

    def test_recent_words_respects_custom_window_size(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that recent_words maxlen matches custom window size"""
        controller = PresentationController(
            sample_sections, start_section, window_size=20
        )

        assert controller.recent_words.maxlen == 20


class TestRecognizerInitialization:
    """Test speech recognizer initialization"""

    def test_recognizer_is_created(self, controller, mock_recognizer):
        """Test that recognizer is created"""
        assert controller.recognizer is not None

    def test_recognizer_from_transducer_called(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that OnlineRecognizer.from_transducer is called"""
        PresentationController(sample_sections, start_section)

        mock_recognizer.from_transducer.assert_called_once()

    def test_recognizer_configured_with_model_paths(
        self,
        sample_sections,
        start_section,
        mock_recognizer,
        mock_sounddevice,
        mock_keyboard,
    ):
        """Test that recognizer is configured with model paths"""
        PresentationController(sample_sections, start_section)

        call_kwargs = mock_recognizer.from_transducer.call_args.kwargs
        assert "tokens" in call_kwargs
        assert "encoder" in call_kwargs
        assert "decoder" in call_kwargs
        assert "joiner" in call_kwargs
        assert "tokens.txt" in call_kwargs["tokens"]
        assert "encoder.int8.onnx" in call_kwargs["encoder"]

    def test_recognizer_stream_is_created(self, controller):
        """Test that recognizer stream is created"""
        assert controller.stream is not None

    def test_recognizer_create_stream_called(self, controller, mock_recognizer):
        """Test that create_stream is called on recognizer"""
        # Get the recognizer instance that was created
        recognizer_instance = mock_recognizer.from_transducer.return_value
        recognizer_instance.create_stream.assert_called_once()


class TestMicrophoneSelection:
    """Test microphone selection initialization"""

    def test_selected_mic_is_set(self, controller):
        """Test that selected_mic is set"""
        assert controller.selected_mic is not None

    def test_selected_mic_uses_default_device(self, controller, mock_sounddevice):
        """Test that selected_mic uses default input device"""
        # Should use the first element of default.device (input device)
        assert controller.selected_mic == mock_sounddevice.default.device[0]
        assert controller.selected_mic == 0


class TestInitializationWithMinimalSections:
    """Test initialization with edge cases"""

    def test_initialization_with_single_section(
        self, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test initialization with single section"""
        sections = [Section(content="Only section", section_index=0)]
        controller = PresentationController(sections, sections[0])

        assert len(controller.sections) == 1
        assert controller.current_section == sections[0]

    def test_initialization_with_two_sections(
        self, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test initialization with two sections"""
        sections = [
            Section(content="First section", section_index=0),
            Section(content="Second section", section_index=1),
        ]
        controller = PresentationController(sections, sections[0])

        assert len(controller.sections) == 2
        assert controller.current_section == sections[0]

    def test_initialization_with_many_sections(
        self, mock_recognizer, mock_sounddevice, mock_keyboard
    ):
        """Test initialization with many sections"""
        sections = [Section(content=f"Section {i}", section_index=i) for i in range(50)]
        controller = PresentationController(sections, sections[25])

        assert len(controller.sections) == 50
        assert controller.current_section == sections[25]
        assert controller.current_section.section_index == 25


class TestControllerAttributes:
    """Test various controller attributes after initialization"""

    def test_has_sections_attribute(self, controller):
        """Test that sections attribute exists"""
        assert hasattr(controller, "sections")

    def test_has_current_section_attribute(self, controller):
        """Test that current_section attribute exists"""
        assert hasattr(controller, "current_section")

    def test_has_chunks_attribute(self, controller):
        """Test that chunks attribute exists"""
        assert hasattr(controller, "chunks")

    def test_has_audio_queue_attribute(self, controller):
        """Test that audio_queue attribute exists"""
        assert hasattr(controller, "audio_queue")

    def test_has_similarity_calculator_attribute(self, controller):
        """Test that similarity_calculator attribute exists"""
        assert hasattr(controller, "similarity_calculator")

    def test_has_recognizer_attribute(self, controller):
        """Test that recognizer attribute exists"""
        assert hasattr(controller, "recognizer")

    def test_has_stream_attribute(self, controller):
        """Test that stream attribute exists"""
        assert hasattr(controller, "stream")

    def test_has_recent_words_attribute(self, controller):
        """Test that recent_words attribute exists"""
        assert hasattr(controller, "recent_words")

    def test_has_previous_recent_words_attribute(self, controller):
        """Test that previous_recent_words attribute exists"""
        assert hasattr(controller, "previous_recent_words")

    def test_has_keyboard_controller_attribute(self, controller):
        """Test that keyboard_controller attribute exists"""
        assert hasattr(controller, "keyboard_controller")

    def test_has_navigator_working_attribute(self, controller):
        """Test that navigator_working attribute exists"""
        assert hasattr(controller, "navigator_working")

    def test_has_paused_attribute(self, controller):
        """Test that paused attribute exists"""
        assert hasattr(controller, "paused")

    def test_has_navigator_attribute(self, controller):
        """Test that navigator attribute exists"""
        assert hasattr(controller, "navigator")

    def test_has_keyboard_listener_attribute(self, controller):
        """Test that keyboard_listener attribute exists"""
        assert hasattr(controller, "keyboard_listener")

    def test_has_selected_mic_attribute(self, controller):
        """Test that selected_mic attribute exists"""
        assert hasattr(controller, "selected_mic")

    def test_has_shutdown_flag_attribute(self, controller):
        """Test that shutdown_flag attribute exists"""
        assert hasattr(controller, "shutdown_flag")

