import asyncio
import threading
import time
from contextlib import suppress
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from queue import Empty, Full, Queue

import sounddevice as sd
from pynput.keyboard import Controller, Key, Listener
from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from sherpa_onnx import OnlineRecognizer, VadModelConfig, VoiceActivityDetector

from moves_cli.config import (
    SIMILARITY_THRESHOLD,
    VAD_BUFFER_SIZE,
    VAD_MIN_SILENCE,
    VAD_MIN_SPEECH,
    VAD_THRESHOLD,
    VAD_WINDOW_SIZE,
    WINDOW_SIZE,
)
from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Section, SttModel, VadModel
from moves_cli.utils import model_preparer, text_normalizer


class ControllerState(StrEnum):
    """State machine states for presentation control."""

    ACTIVE = "ACTIVE"  # Normal operation - listening, auto-navigation enabled
    PAUSED = "PAUSED"  # Microphone paused - no processing, keyboard still listened
    LOCKED = "LOCKED"  # Manual override - listening but navigation disabled


# =============================================================================
# Rich UI Theme & Style Mapping
# =============================================================================
THEME = Theme(
    {
        "accent": "bold cyan",
        "accent.light": "cyan",
        "status.active": "bold green",
        "status.paused": "bold yellow",
        "status.locked": "bold red",
        "sim.high": "bold green",
        "sim.medium": "bold yellow",
        "sim.low": "bold red",
        "nav.action": "bold magenta",
        "muted": "dim",
        "text": "bright_white",
    }
)

STATE_STYLE = {
    ControllerState.ACTIVE: "status.active",
    ControllerState.PAUSED: "status.paused",
    ControllerState.LOCKED: "status.locked",
}


# =============================================================================
# UI Data Model
# =============================================================================
@dataclass(frozen=True, slots=True)
class UIData:
    """Dashboard display state for Rich UI."""

    state: ControllerState
    slide: int
    total: int
    similarity: float
    delta: int
    speech: list[str]
    match: list[str]
    vad: bool


# =============================================================================
# UI Builder Functions
# =============================================================================
def _format_speech_text(words: list[str], icon: str) -> Text:
    """Create a wrapped speech text block."""
    text = " ".join(words)
    return Text.from_markup(f"{icon} [text]{text}[/]")


def _build_header(d: UIData) -> Table:
    """Build the header row: State | Slide | Metrics."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right", ratio=1)

    # State
    state = Text(d.state, style=STATE_STYLE[d.state])

    # Slide counter
    slide = Text.from_markup(f"[accent]{d.slide}[/][muted]/{d.total}[/]")

    # Navigation + Similarity
    sim_style = (
        "sim.high"
        if d.similarity >= 0.75
        else ("sim.medium" if d.similarity >= 0.5 else "sim.low")
    )

    if d.delta > 0:
        nav = Text.from_markup(f"[nav.action]{d.delta} ▶[/]  ")
    elif d.delta < 0:
        nav = Text.from_markup(f"  [nav.action]◀ {abs(d.delta)}[/]")
    else:
        nav = Text.from_markup("  [muted]■[/]  ")

    nav.append(f" {int(d.similarity * 100)}%", style=sim_style)

    grid.add_row(state, slide, nav)
    return grid


def _build_content(d: UIData) -> Group:
    """Build the content section: Wrapped Speech + Full Section Text."""
    vad_icon = "●" if d.vad else "○"

    # --- Speech Block (Wrapped) ---
    speech_display = _format_speech_text(d.speech, vad_icon)

    # --- Match/Section Block (Full Text) ---
    section_text = " ".join(d.match)
    section_display = Text.from_markup(f"≈ [muted]{section_text}[/]")

    return Group(
        speech_display,
        Rule(style="muted"),
        section_display,
    )


def _build_footer() -> Align:
    """Build the footer with keyboard shortcuts."""
    return Align.center(
        Text.from_markup(
            "[accent][M][/] [muted]Pause[/]  [accent][← →][/] [muted]Nav[/]  [accent][Q][/] [muted]Quit[/]"
        )
    )


def _build_frame(d: UIData) -> Panel:
    """Assemble the complete dashboard frame."""
    return Panel(
        Group(
            _build_header(d),
            Rule(style="muted"),
            _build_content(d),
            Rule(style="muted"),
            _build_footer(),
        ),
        title="[accent]moves[/] Presenter",
        border_style="accent.light",
        box=box.ROUNDED,
        padding=(0, 1),
    )


class PresentationController:
    # The logic specific constants defined here, for general configuration see config.py
    # Should not change these
    SAMPLE_RATE: int = 16000
    FRAME_DURATION: float = 0.1
    AUDIO_QUEUE_SIZE: int = 5
    WORDS_QUEUE_SIZE: int = 1
    NUM_THREADS: int = 8
    DISPLAY_WORD_COUNT: int = 7
    KEY_PRESS_DELAY: float = 0.01
    QUEUE_TIMEOUT: float = 1.0
    THREAD_JOIN_TIMEOUT: float = 2.0
    SHUTDOWN_CHECK_INTERVAL: float = 0.5
    MODEL_DIR: Path = SttModel.model_dir
    VAD_MODEL_DIR: Path = VadModel.model_dir
    # VAD configuration loaded from config.py
    VAD_THRESHOLD: float = VAD_THRESHOLD
    VAD_MIN_SILENCE: float = VAD_MIN_SILENCE
    VAD_MIN_SPEECH: float = VAD_MIN_SPEECH
    VAD_WINDOW_SIZE: int = VAD_WINDOW_SIZE
    VAD_BUFFER_SIZE: float = VAD_BUFFER_SIZE
    # from config.py
    SIMILARITY_THRESHOLD: float = SIMILARITY_THRESHOLD
    WINDOW_SIZE: int = WINDOW_SIZE

    def __init__(
        self,
        sections: list[Section],
        window_size: int = WINDOW_SIZE,
    ) -> None:
        asyncio.run(model_preparer.prepare_models())

        try:
            self.recognizer = OnlineRecognizer.from_transducer(
                tokens=str(self.MODEL_DIR / "tokens.txt"),
                encoder=str(self.MODEL_DIR / "encoder.int8.onnx"),
                decoder=str(self.MODEL_DIR / "decoder.int8.onnx"),
                joiner=str(self.MODEL_DIR / "joiner.int8.onnx"),
                num_threads=self.NUM_THREADS,
                decoding_method="greedy_search",
                enable_endpoint_detection=True,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load STT model from {self.MODEL_DIR}: {e}"
            ) from e

        # Initialize VAD for filtering background noise in crowded environments
        try:
            vad_config = VadModelConfig()
            vad_config.silero_vad.model = str(
                self.VAD_MODEL_DIR / "silero_vad.int8.onnx"
            )
            vad_config.sample_rate = self.SAMPLE_RATE
            vad_config.silero_vad.threshold = self.VAD_THRESHOLD
            vad_config.silero_vad.min_silence_duration = self.VAD_MIN_SILENCE
            vad_config.silero_vad.min_speech_duration = self.VAD_MIN_SPEECH
            vad_config.silero_vad.window_size = self.VAD_WINDOW_SIZE

            self.vad = VoiceActivityDetector(
                vad_config, buffer_size_in_seconds=self.VAD_BUFFER_SIZE
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load VAD model from {self.VAD_MODEL_DIR}: {e}"
            ) from e

        self.window_size = window_size
        self.sections = sections
        self.section_lock = threading.Lock()
        self.shutdown_flag = threading.Event()

        # State machine for manual controls
        self._state = ControllerState.ACTIVE
        self._state_lock = threading.Lock()

        # Echo suppression: prevents our own key presses from triggering state changes
        self._echo_suppression = threading.Event()

        # VAD status flag for display (atomic bool via Event for thread-safety)
        self._vad_active = threading.Event()

        # Sliding window buffer - persists across stream resets
        # Maintains last window_size words for consistent matching
        self._word_buffer: list[str] = []
        self._word_buffer_lock = threading.Lock()

        with self.section_lock:
            self.current_section = sections[0]

        self.audio_queue = Queue(maxsize=PresentationController.AUDIO_QUEUE_SIZE)
        self.words_queue = Queue(maxsize=PresentationController.WORDS_QUEUE_SIZE)

        self.chunks = chunk_producer.generate_chunks(sections, window_size)
        self.candidate_chunk_generator = chunk_producer.CandidateChunkGenerator(
            self.chunks
        )
        self.similarity_calculator = SimilarityCalculator(self.chunks)

        self.keyboard_controller = Controller()

        self.stt_processor_thread = threading.Thread(
            target=self._stt_processor_task, daemon=True
        )
        self.navigator_thread = threading.Thread(
            target=self._navigator_task, daemon=True
        )

        # Rich UI console and live display - created lazily in control() to avoid
        # interfering with typer prompts before presentation starts
        self._console: Console | None = None
        self._live: Live | None = None

        # Cache last displayed content for UI persistence during manual actions
        self._last_speech: list[str] = []
        self._last_match: list[str] = []
        self._last_similarity: float = 0.0
        self._display_buffer: list[str] = []  # Larger buffer for visual transcript

        # Manual navigation indicator state
        self._manual_delta: int = 0
        self._manual_delta_expiry: float = 0.0

    # ─────────────────────────────────────────────────────────────────────────
    # State Machine Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _get_state(self) -> ControllerState:
        """Thread-safe state getter."""
        with self._state_lock:
            return self._state

    def _set_state(self, new_state: ControllerState) -> None:
        """Thread-safe state setter."""
        with self._state_lock:
            if self._state != new_state:
                self._state = new_state

    def _on_key_press(self, key: Key) -> None:
        """Global keyboard listener callback for manual controls.

        Handles:
        - M key: Toggle between PAUSED and ACTIVE states
        - Arrow keys: Detect manual intervention, transition to LOCKED
        """
        # Ignore our own key presses (echo prevention)
        if self._echo_suppression.is_set():
            return

        current_state = self._get_state()

        # Handle Q key - quit
        if hasattr(key, "char") and key.char == "q":
            self.shutdown_flag.set()
            return

        # Handle M key - pause/resume toggle
        if hasattr(key, "char") and key.char == "m":
            new_state: ControllerState | None = None
            match current_state:
                case ControllerState.ACTIVE:
                    new_state = ControllerState.PAUSED
                case ControllerState.LOCKED:
                    # IMPORTANT: From LOCKED, M goes to PAUSED (not ACTIVE)
                    # Supervisor likely wants full control in front of 1000 people
                    new_state = ControllerState.PAUSED
                case ControllerState.PAUSED:
                    # From PAUSED, M always returns to ACTIVE
                    # Supervisor is giving control back to the system
                    new_state = ControllerState.ACTIVE

            if new_state:
                self._set_state(new_state)
                # Ensure VAD shows inactive when paused
                if new_state == ControllerState.PAUSED:
                    self._vad_active.clear()
            return

        # Handle arrow keys - manual intervention detection
        if key in (Key.left, Key.right):
            # Update current section based on arrow key pressed
            with self.section_lock:
                current_idx = self.current_section.section_index
                direction = 1 if key == Key.right else -1

                if key == Key.right and current_idx < len(self.sections):
                    new_idx = min(current_idx + 1, len(self.sections))
                    self.current_section = self.sections[new_idx - 1]
                elif key == Key.left and current_idx > 1:
                    new_idx = max(current_idx - 1, 1)
                    self.current_section = self.sections[new_idx - 1]
                else:
                    direction = 0  # Bound reached

                # Update cumulative manual delta and timer
                if direction != 0:
                    # Clear display buffer on slide change (visual reset only)
                    self._display_buffer = []
                    self._last_speech = []

                    now = time.time()
                    # If same direction and within 1s, increment. Otherwise restart.
                    if (
                        now < self._manual_delta_expiry
                        and (self._manual_delta * direction) > 0
                    ):
                        self._manual_delta += direction
                    else:
                        self._manual_delta = direction

                    self._manual_delta_expiry = now + 1.0  # Reset 1s timer

            match current_state:
                case ControllerState.ACTIVE:
                    # Manual intervention detected - lock navigation
                    self._set_state(ControllerState.LOCKED)
                case ControllerState.LOCKED | ControllerState.PAUSED:
                    # Already locked or paused - just track the movement
                    pass

    # ─────────────────────────────────────────────────────────────────────────
    # Audio & Processing Methods
    # ─────────────────────────────────────────────────────────────────────────

    def _audio_sampler_callback(self, indata, _frames, _time, _status) -> None:
        """VAD-gated audio sampling: only speech passes to STT."""
        # When PAUSED, don't process audio at all (mic effectively muted)
        if self._get_state() == ControllerState.PAUSED:
            self._vad_active.clear()
            return

        samples = indata[:, 0].copy()

        # Feed samples to VAD for speech detection
        self.vad.accept_waveform(samples)

        # Update VAD status flag for display
        is_speech = self.vad.is_speech_detected()
        if is_speech:
            self._vad_active.set()
        else:
            self._vad_active.clear()

        # Only send to STT if speech is detected (filters crowd noise, coughs, applause)
        if is_speech:
            if not self.audio_queue.full():
                with suppress(Full):
                    self.audio_queue.put_nowait(samples)

    def _stt_processor_task(self) -> None:
        stream = self.recognizer.create_stream()
        last_word_count = 0  # Track previous word count to detect new words

        while not self.shutdown_flag.is_set():
            try:
                audio_chunk = self.audio_queue.get(timeout=self.QUEUE_TIMEOUT)

                stream.accept_waveform(self.SAMPLE_RATE, audio_chunk)
                while self.recognizer.is_ready(stream):
                    self.recognizer.decode_stream(stream)

                if text := self.recognizer.get_result(stream):
                    current_words = text.strip().split()

                    # Detect new words since last check
                    if len(current_words) > last_word_count:
                        new_words = current_words[last_word_count:]

                        # Update sliding window buffer (thread-safe)
                        with self._word_buffer_lock:
                            self._word_buffer.extend(new_words)
                            self._display_buffer.extend(new_words)

                            # Keep logic buffer small, display buffer large
                            self._word_buffer = self._word_buffer[-self.window_size :]
                            self._display_buffer = self._display_buffer[-100:]

                            # Prepare words for matching
                            buffer_text = " ".join(self._word_buffer)
                            normalized = text_normalizer.normalize_text(buffer_text)
                            words = normalized.strip().split()

                        # Send to navigator if enough context
                        if len(words) >= 3:
                            with suppress(Empty):
                                self.words_queue.get_nowait()
                            with suppress(Full):
                                self.words_queue.put_nowait(words)

                        last_word_count = len(current_words)

                # Reset stream on endpoint (natural speech pauses)
                # Buffer persists - only STT internal state is cleared
                if self.recognizer.is_endpoint(stream):
                    self.recognizer.reset(stream)
                    last_word_count = 0  # Reset counter for new stream

            except Empty:
                continue
            except Exception as e:
                self._console.print(f"[bold red]Error in STT Processor thread:[/] {e}")
                self.shutdown_flag.set()

    def _navigator_task(self) -> None:
        previous_words: list[str] = []
        while not self.shutdown_flag.is_set():
            try:
                # get the words from the queue
                current_words = self.words_queue.get(timeout=self.QUEUE_TIMEOUT)

                if current_words == previous_words:
                    continue

                input_text = " ".join(current_words)
                with self.section_lock:
                    current_section = self.current_section

                # ensure the candidate chunks for the current section
                if not (
                    candidate_chunks
                    := self.candidate_chunk_generator.get_candidate_chunks(
                        current_section
                    )
                ):
                    continue

                similarity_results = self.similarity_calculator.compare(
                    input_text, candidate_chunks, current_section.section_index
                )

                top_match = similarity_results[0]
                best_chunk = top_match.chunk
                target_section = best_chunk.source_sections[-1]
                slide_delta = (
                    target_section.section_index - current_section.section_index
                )

                # Get current state for display and logic
                current_state = self._get_state()

                # Prepare display data and cache for UI persistence
                speech_display = self._display_buffer[-100:]
                # We want to show the full current section text in the match area
                match_display = current_section.content.strip().split()

                # Cache values for manual navigation UI updates
                self._last_speech = speech_display
                self._last_match = match_display
                self._last_similarity = top_match.score

                # State-aware navigation logic
                if top_match.score >= self.SIMILARITY_THRESHOLD:
                    match current_state:
                        case ControllerState.ACTIVE:
                            # If auto-navigating, clear manual delta labels
                            if slide_delta != 0:
                                self._manual_delta = 0
                            # Normal operation - perform navigation
                            self._perform_navigation(target_section)
                        case ControllerState.LOCKED:
                            # Check for consensus: if top match equals current section, unlock
                            if slide_delta == 0:
                                self._set_state(ControllerState.ACTIVE)
                            # Otherwise stay locked, don't navigate
                        case ControllerState.PAUSED:
                            # No action - system is paused
                            pass

                previous_words = current_words

            except Empty:
                continue
            except Exception as e:
                self._console.print(f"[bold red]Error in Navigator thread:[/] {e}")
                self.shutdown_flag.set()

    def _update_display(self, data: UIData) -> None:
        """Update the Rich Live display with current state."""
        if self._live is not None:
            frame = _build_frame(data)
            self._live.update(frame, refresh=True)

    def _perform_navigation(self, target_section: Section) -> None:
        """Navigate to target section with echo suppression.

        Echo suppression prevents our own key presses from triggering
        the keyboard listener (which would incorrectly transition to LOCKED).
        """
        with self.section_lock:
            current_slide = self.current_section.section_index
            target_slide = target_section.section_index
            slide_delta = target_slide - current_slide

            if slide_delta != 0:
                # Clear display buffer on slide change (visual reset only)
                self._display_buffer = []
                self._last_speech = []

                # Enable echo suppression before pressing keys
                self._echo_suppression.set()
                try:
                    key_to_press = Key.right if slide_delta > 0 else Key.left
                    for _ in range(abs(slide_delta)):
                        self.keyboard_controller.press(key_to_press)
                        self.keyboard_controller.release(key_to_press)
                        time.sleep(self.KEY_PRESS_DELAY)
                finally:
                    # Always clear echo suppression
                    self._echo_suppression.clear()

            self.current_section = target_section

    def control(self) -> None:
        """Main control loop with keyboard listener and audio processing."""
        self.stt_processor_thread.start()
        self.navigator_thread.start()

        blocksize = int(self.SAMPLE_RATE * self.FRAME_DURATION)

        # Create console before starting threads so they can use it for error messages
        self._console = Console(theme=THEME)

        # Start global keyboard listener for manual controls
        keyboard_listener = Listener(on_press=self._on_key_press)
        keyboard_listener.start()

        # Create initial UI frame
        initial_data = UIData(
            state=self._get_state(),
            slide=self.current_section.section_index,
            total=len(self.sections),
            similarity=0.0,
            delta=0,
            speech=[],
            match=[],
            vad=False,
        )

        try:
            with Live(
                _build_frame(initial_data),
                console=self._console,
                screen=True,
                auto_refresh=False,
            ) as self._live:
                with sd.InputStream(
                    samplerate=self.SAMPLE_RATE,
                    blocksize=blocksize,
                    dtype="float32",
                    channels=1,
                    callback=self._audio_sampler_callback,
                    latency="low",
                ):
                    while not self.shutdown_flag.is_set():
                        # --- UI Heartbeat & State Check ---
                        now = time.time()

                        # Handle manual delta expiry
                        if now >= self._manual_delta_expiry:
                            self._manual_delta = 0

                        # Construct current UI data
                        with self.section_lock:
                            current_state = self._get_state()
                            ui_data = UIData(
                                state=current_state,
                                slide=self.current_section.section_index,
                                total=len(self.sections),
                                similarity=self._last_similarity,
                                delta=self._manual_delta,
                                speech=self._last_speech,
                                match=self._last_match,
                                vad=self._vad_active.is_set(),
                            )

                        self._update_display(ui_data)

                        # Wait for next refresh (100ms Heartbeat)
                        self.shutdown_flag.wait(timeout=0.1)

        except KeyboardInterrupt:
            pass  # Clean exit on Ctrl+C
        except Exception as e:
            self._console.print(f"[bold red]Audio stream error:[/] {e}")

        finally:
            self.shutdown_flag.set()
            self._live = None  # Clear live reference

            # Stop keyboard listener
            keyboard_listener.stop()

            # Gracefully shutdown the threads
            threads_to_join = [self.stt_processor_thread, self.navigator_thread]
            for thread in threads_to_join:
                if thread.is_alive():
                    thread.join(timeout=self.THREAD_JOIN_TIMEOUT)

            self._console.print("[accent]Presentation ended.[/]")
