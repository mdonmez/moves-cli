import threading
import time
from collections import deque

import sounddevice as sd
from pynput.keyboard import Key, Controller, Listener
from sherpa_onnx import OnlineRecognizer

from moves_cli.data.models import Section
from moves_cli.utils import text_normalizer
from moves_cli.utils import data_handler
from moves_cli.utils import model_downloader
from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from pathlib import Path


class PresentationController:
    def __init__(
        self,
        sections: list[Section],
        start_section: Section,
        window_size: int = 12,
    ):
        self.frame_duration = 0.1
        self.sample_rate = 16000
        self.window_size = window_size

        model_downloader.download_model("embedding")
        model_downloader.download_model("stt")

        self.similarity_calculator = SimilarityCalculator()

        self.sections = sections
        self.current_section = start_section
        self.chunks = chunk_producer.generate_chunks(sections, window_size)

        self.audio_queue = deque(maxlen=5)
        self.shutdown_flag = threading.Event()

        model_dir = Path(
            data_handler.DATA_FOLDER / "ml_models" / "nemo-streaming-stt-480ms-int8"
        )

        self.recognizer = OnlineRecognizer.from_transducer(
            tokens=str(model_dir.joinpath("tokens.txt")),
            encoder=str(model_dir.joinpath("encoder.int8.onnx")),
            decoder=str(model_dir.joinpath("decoder.int8.onnx")),
            joiner=str(model_dir.joinpath("joiner.int8.onnx")),
            num_threads=8,
            decoding_method="greedy_search",
        )

        self.stream = self.recognizer.create_stream()

        self.recent_words: deque[str] = deque(maxlen=window_size)
        self.previous_recent_words: list[str] = []

        self.keyboard_controller = Controller()
        self.navigator_working = False
        self.paused = False

        self.navigator = threading.Thread(
            target=self.navigate_presentation, daemon=True
        )

        self.keyboard_listener = Listener(on_press=self._on_key_press)

        # Always use the default sounddevice input
        self.selected_mic = sd.default.device[0]

    def process_audio(self):
        while not self.shutdown_flag.is_set():
            try:
                if self.audio_queue:
                    chunk = self.audio_queue.popleft()
                else:
                    self.shutdown_flag.wait(0.001)
                    continue

                self.stream.accept_waveform(self.sample_rate, chunk)

                while self.recognizer.is_ready(self.stream):
                    self.recognizer.decode_stream(self.stream)

                if text := self.recognizer.get_result(self.stream):
                    normalized_text = text_normalizer.normalize_text(text)
                    words = normalized_text.strip().split()[-self.window_size :]
                    if words and words != list(self.recent_words):
                        self.recent_words.clear()
                        self.recent_words.extend(words)

            except Exception as e:
                raise RuntimeError(f"Audio processing error: {e}") from e

    def navigate_presentation(self):
        while not self.shutdown_flag.is_set():
            try:
                current_words = list(self.recent_words)

                if len(current_words) < self.window_size:
                    self.shutdown_flag.wait(0.001)
                    continue

                # Skip automatic navigation when paused
                if self.paused:
                    self.shutdown_flag.wait(0.001)
                    continue

                if (
                    current_words != self.previous_recent_words
                    and not self.navigator_working
                ):
                    self.navigator_working = True

                    try:
                        candidate_chunks = chunk_producer.get_candidate_chunks(
                            self.current_section, self.chunks
                        )

                        if not candidate_chunks:
                            continue

                        input_text = " ".join(current_words)
                        similarity_results = self.similarity_calculator.compare(
                            input_text, candidate_chunks
                        )

                        best_result = similarity_results[0]
                        best_chunk = best_result.chunk

                        target_section = best_chunk.source_sections[-1]

                        current_idx = self.current_section.section_index
                        target_idx = target_section.section_index
                        navigation_distance = target_idx - current_idx

                        # Print status with speech and match info
                        recent_speech = " ".join(current_words[-7:])
                        recent_match = " ".join(
                            best_chunk.partial_content.strip().split()[-7:]
                        )

                        if navigation_distance != 0:
                            key = Key.right if navigation_distance > 0 else Key.left
                            abs_distance = abs(navigation_distance)

                            for _ in range(abs_distance):
                                self.keyboard_controller.press(key)
                                self.keyboard_controller.release(key)

                                if abs_distance > 1 and _ < abs_distance - 1:
                                    time.sleep(0.01)

                        print(
                            f"\n[{target_section.section_index + 1}/{len(self.sections)}]"
                        )
                        print(f"Speech  -> {recent_speech}")
                        print(f"Match   -> {recent_match}")

                        self.current_section = target_section
                        self.previous_recent_words = current_words.copy()

                    except Exception as e:
                        raise RuntimeError(f"Navigation execution error: {e}") from e
                    finally:
                        self.navigator_working = False

                self.shutdown_flag.wait(0.001)

            except Exception as e:
                raise RuntimeError(f"Navigation error: {e}") from e

    def _on_key_press(self, key):
        try:
            if key == Key.right:
                self._next_section()
            elif key == Key.left:
                self._prev_section()
            elif key == Key.insert:
                self._toggle_pause()
        except Exception:
            pass

    def _next_section(self):
        current_idx = self.current_section.section_index
        if current_idx < len(self.sections) - 1:
            self.current_section = self.sections[current_idx + 1]
            print(
                f"\n[Next Section] ({self.current_section.section_index}/{len(self.sections)} -> {self.current_section.section_index + 1}/{len(self.sections)})"
            )

    def _prev_section(self):
        current_idx = self.current_section.section_index
        if current_idx > 0:
            prev_idx = current_idx
            self.current_section = self.sections[current_idx - 1]
            print(
                f"\n[Previous Section] ({prev_idx + 1}/{len(self.sections)} -> {self.current_section.section_index + 1}/{len(self.sections)})"
            )

    def _toggle_pause(self):
        self.paused = not self.paused
        if self.paused:
            print("\n[Paused]")
        else:
            print("\n[Resumed]")

    def control(self):
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()
        self.navigator.start()
        self.keyboard_listener.start()

        blocksize = int(self.sample_rate * self.frame_duration)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=blocksize,
                dtype="float32",
                channels=1,
                callback=lambda indata, *_: self.audio_queue.append(
                    indata[:, 0].copy()
                ),
                latency="low",
                device=self.selected_mic,
            ):
                while not self.shutdown_flag.is_set():
                    sd.sleep(20)

        except KeyboardInterrupt:
            pass

        finally:
            self.shutdown_flag.set()

            if audio_thread.is_alive():
                audio_thread.join(timeout=1.0)
            if self.navigator.is_alive():
                self.navigator.join(timeout=1.0)
            if self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()
