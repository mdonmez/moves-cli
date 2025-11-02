import queue
import threading
import time

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
        window_size: int,
        similarity_threshold: float = 0.65,
    ):
        self.frame_duration = 0.1
        self.sample_rate = 16000
        self.window_size = window_size
        self.similarity_threshold = similarity_threshold

        model_downloader.download_model("embedding")
        model_downloader.download_model("stt")

        self.sections = sections
        self.current_section = start_section
        self.chunks = chunk_producer.generate_chunks(sections, window_size)

        self.similarity_calculator = SimilarityCalculator(all_chunks=self.chunks)

        # Thread-safe queues for inter-thread communication
        self.audio_queue: queue.Queue[tuple] = queue.Queue(maxsize=10)
        self.words_queue: queue.Queue[list[str]] = queue.Queue()
        self.keyboard_queue: queue.Queue[tuple[Key, int]] = queue.Queue()

        # Thread synchronization primitives
        self.shutdown_flag = threading.Event()
        self.is_paused = threading.Event()
        self.section_lock = threading.Lock()

        # Keyboard automation thread
        self.keyboard_thread = threading.Thread(
            target=self._keyboard_worker, daemon=True
        )

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

        self.candidate_chunk_generator = chunk_producer.CandidateChunkGenerator(
            all_chunks=self.chunks
        )

        self.stream = self.recognizer.create_stream()

        self.keyboard_controller = Controller()

        self.navigator = threading.Thread(
            target=self.navigate_presentation, daemon=True
        )

        self.keyboard_listener = Listener(on_press=self._on_key_press)

        self.selected_mic = sd.default.device[0]

    def process_audio(self):
        while not self.shutdown_flag.is_set():
            try:
                # Check pause state
                if self.is_paused.is_set():
                    time.sleep(0.01)
                    continue

                # Blocking get with timeout
                try:
                    chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                self.stream.accept_waveform(self.sample_rate, chunk)

                while self.recognizer.is_ready(self.stream):
                    self.recognizer.decode_stream(self.stream)

                if text := self.recognizer.get_result(self.stream):
                    normalized_text = text_normalizer.normalize_text(text)
                    words = normalized_text.strip().split()[-self.window_size :]
                    if words:
                        # Put words on queue for navigator (non-blocking)
                        try:
                            self.words_queue.put_nowait(words)
                        except queue.Full:
                            # Drop if navigator is backed up (shouldn't happen)
                            pass

                self.audio_queue.task_done()

            except Exception as e:
                raise RuntimeError(f"Audio processing error: {e}") from e

    def _keyboard_worker(self):
        """Dedicated thread for processing keyboard commands without blocking navigation."""
        while not self.shutdown_flag.is_set():
            try:
                # Wait for keyboard command with timeout for shutdown check
                try:
                    key, count = self.keyboard_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                # Execute the key presses
                for i in range(count):
                    self.keyboard_controller.press(key)
                    self.keyboard_controller.release(key)

                    # Small delay between multiple presses for presentation software
                    if count > 1 and i < count - 1:
                        time.sleep(0.01)

                self.keyboard_queue.task_done()

            except Exception as e:
                # Log but don't crash - keyboard errors shouldn't kill the thread
                print(f"\n[Keyboard error: {e}]")

    def navigate_presentation(self):
        previous_words = []

        while not self.shutdown_flag.is_set():
            try:
                # Blocking get with timeout
                try:
                    current_words = self.words_queue.get(timeout=0.5)
                except queue.Empty:
                    continue  # Timeout - check shutdown

                # Skip if paused
                if self.is_paused.is_set():
                    self.words_queue.task_done()
                    continue

                # Verify we have enough words
                if len(current_words) < self.window_size:
                    self.words_queue.task_done()
                    continue

                # Skip if words haven't changed (deduplication)
                if current_words == previous_words:
                    self.words_queue.task_done()
                    continue

                try:
                    with self.section_lock:
                        current_section = self.current_section

                    candidate_chunks = (
                        self.candidate_chunk_generator.get_candidate_chunks(
                            current_section
                        )
                    )

                    if not candidate_chunks:
                        previous_words = current_words
                        self.words_queue.task_done()
                        continue

                    input_text = " ".join(current_words)
                    similarity_results = self.similarity_calculator.compare(
                        input_text, candidate_chunks
                    )

                    best_result = similarity_results[0]
                    best_score = best_result.score

                    # Check if best match meets threshold
                    if best_score < self.similarity_threshold:
                        recent_speech = " ".join(current_words[-7:])
                        print(
                            f"\n[Ignored - Low confidence: {best_score:.3f} < {self.similarity_threshold}]"
                        )
                        print(f"Speech  -> {recent_speech}")
                        previous_words = current_words
                        self.words_queue.task_done()
                        continue

                    best_chunk = best_result.chunk
                    target_section = best_chunk.source_sections[-1]

                    with self.section_lock:
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
                        self.keyboard_queue.put((key, abs_distance))

                    print(
                        f"\n[{target_section.section_index + 1}/{len(self.sections)}]"
                    )
                    print(f"Score   -> {best_score:.3f}")
                    print(f"Speech  -> {recent_speech}")
                    print(f"Match   -> {recent_match}")

                    with self.section_lock:
                        self.current_section = target_section

                    previous_words = current_words

                except Exception as e:
                    raise RuntimeError(f"Navigation execution error: {e}") from e
                finally:
                    self.words_queue.task_done()

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
        with self.section_lock:
            current_idx = self.current_section.section_index
            if current_idx < len(self.sections) - 1:
                self.current_section = self.sections[current_idx + 1]
                print(
                    f"\n[Next Section] ({current_idx + 1}/{len(self.sections)} -> {self.current_section.section_index + 1}/{len(self.sections)})"
                )

    def _prev_section(self):
        with self.section_lock:
            current_idx = self.current_section.section_index
            if current_idx > 0:
                prev_idx = current_idx
                self.current_section = self.sections[current_idx - 1]
                print(
                    f"\n[Previous Section] ({prev_idx + 1}/{len(self.sections)} -> {self.current_section.section_index + 1}/{len(self.sections)})"
                )

    def _toggle_pause(self):
        if not self.is_paused.is_set():
            # Pausing
            self.is_paused.set()

            # Drain queues
            while not self.audio_queue.empty():
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.task_done()
                except queue.Empty:
                    break

            while not self.words_queue.empty():
                try:
                    self.words_queue.get_nowait()
                    self.words_queue.task_done()
                except queue.Empty:
                    break

            print("\n[Paused]")
        else:
            # Resuming
            self.is_paused.clear()

            # Reset STT stream to clear internal context
            self.stream = self.recognizer.create_stream()

            print("\n[Resumed]")

    def _audio_callback(self, indata, frames, time_info, status):
        """Audio input callback that respects pause state."""
        if not self.is_paused.is_set():
            try:
                # Non-blocking put - drops frame if queue full
                self.audio_queue.put_nowait(indata[:, 0].copy())
            except queue.Full:
                # Drop frame if processing can't keep up
                pass

    def control(self):
        audio_thread = threading.Thread(target=self.process_audio, daemon=True)
        audio_thread.start()
        self.keyboard_thread.start()
        self.navigator.start()
        self.keyboard_listener.start()

        blocksize = int(self.sample_rate * self.frame_duration)

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=blocksize,
                dtype="float32",
                channels=1,
                callback=self._audio_callback,
                latency="low",
                device=self.selected_mic,
            ):
                while not self.shutdown_flag.is_set():
                    sd.sleep(20)

        except KeyboardInterrupt:
            pass

        finally:
            self.shutdown_flag.set()

            # Wait for pending commands in queues to complete
            try:
                self.audio_queue.join()
            except Exception:
                pass

            try:
                self.words_queue.join()
            except Exception:
                pass

            try:
                self.keyboard_queue.join()
            except Exception:
                pass

            if audio_thread.is_alive():
                audio_thread.join(timeout=1.0)
            if self.keyboard_thread.is_alive():
                self.keyboard_thread.join(timeout=1.0)
            if self.navigator.is_alive():
                self.navigator.join(timeout=1.0)
            if self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()
