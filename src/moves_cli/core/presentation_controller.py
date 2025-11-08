import threading
import time
from pathlib import Path
from queue import Queue, Empty, Full

import sounddevice as sd
from pynput.keyboard import Key, Controller, Listener
from sherpa_onnx import OnlineRecognizer

from moves_cli.data.models import Section
from moves_cli.utils import text_normalizer
from moves_cli.utils import data_handler
from moves_cli.utils import model_downloader
from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator


class PresentationController:
    SAMPLE_RATE = 16000
    FRAME_DURATION = 0.1
    AUDIO_QUEUE_SIZE = 5
    WORDS_QUEUE_SIZE = 1
    NUM_THREADS = 8
    MODEL_DIR = Path(
        data_handler.DATA_FOLDER / "ml_models" / "nemo-streaming-stt-480ms-int8"
    )

    def __init__(
        self,
        sections: list[Section],
        window_size: int = 12,
    ):
        self.window_size = window_size
        self.shutdown_flag = threading.Event()

        self.audio_queue = Queue(maxsize=PresentationController.AUDIO_QUEUE_SIZE)
        self.words_queue = Queue(maxsize=PresentationController.WORDS_QUEUE_SIZE)

        model_downloader.download_model("embedding")
        model_downloader.download_model("stt")

        try:
            self.recognizer = OnlineRecognizer.from_transducer(
                tokens=str(self.MODEL_DIR.joinpath("tokens.txt")),
                encoder=str(self.MODEL_DIR.joinpath("encoder.int8.onnx")),
                decoder=str(self.MODEL_DIR.joinpath("decoder.int8.onnx")),
                joiner=str(self.MODEL_DIR.joinpath("joiner.int8.onnx")),
                num_threads=8,
                decoding_method="greedy_search",
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load STT model from {self.MODEL_DIR}: {e}"
            ) from e

        self.sections = sections
        self.chunks = chunk_producer.generate_chunks(sections, window_size)
        self.candidate_chunk_generator = chunk_producer.CandidateChunkGenerator(
            self.chunks
        )
        self.similarity_calculator = SimilarityCalculator(self.chunks)
        self.paused = False

        self.keyboard_controller = Controller()

        self.stt_processor_thread = threading.Thread(
            target=self._stt_processor_task, daemon=True
        )
        self.navigator_thread = threading.Thread(
            target=self._navigator_task, daemon=True
        )
        self.keyboard_listener = Listener(on_press=self._on_key_press)

    def _audio_sampler_callback(self, indata, frames, time, status):
        if not self.audio_queue.full():
            try:
                self.audio_queue.put_nowait(indata[:, 0].copy())
            except Full:
                # This case is rare due to the .full() check but included for safety.
                pass
        # If the queue is full, the new audio chunk is silently discarded.

    def _stt_processor_task(self):
        stream = self.recognizer.create_stream()
        while not self.shutdown_flag.is_set():
            try:
                # 1. WAIT: Efficiently waits for a new audio chunk to arrive.
                audio_chunk = self.audio_queue.get(timeout=1)

                # 2. PROCESS: Feed the chunk to the STT engine.
                stream.accept_waveform(self.SAMPLE_RATE, audio_chunk)
                while self.recognizer.is_ready(stream):
                    self.recognizer.decode_stream(stream)

                # 3. PUBLISH: If new text is available, publish the latest words.
                if text := self.recognizer.get_result(stream):
                    normalized_text = text_normalizer.normalize_text(text)
                    latest_words = normalized_text.strip().split()[-self.window_size :]

                    if not latest_words:
                        continue

                    # Clear any stale data from the single-slot queue before putting the new one.
                    try:
                        self.words_queue.get_nowait()
                    except Empty:
                        pass

                    try:
                        self.words_queue.put_nowait(latest_words)
                    except Full:
                        # Navigator is still busy with the previous data. This is fine.
                        pass
            except Empty:
                # Timeout occurred, loop continues to check shutdown_flag.
                continue
            except Exception as e:
                print(f"Error in STT Processor thread: {e}")
                self.shutdown_flag.set()

    def _navigator_task(self):
        previous_words = []
        while not self.shutdown_flag.is_set():
            try:
                # 1. WAIT: Efficiently waits for a new word list to arrive.
                current_words = self.words_queue.get(timeout=1)

                if (
                    self.paused
                    or len(current_words) < self.window_size
                    or current_words == previous_words
                ):
                    continue

                # 2. PROCESS: Perform the heavy CS&SC calculation.
                input_text = " ".join(current_words)
                candidate_chunks = self.candidate_chunk_generator.get_candidate_chunks(
                    self.current_section
                )
                if not candidate_chunks:
                    continue

                similarity_results = self.similarity_calculator.compare(
                    input_text, candidate_chunks
                )

                # TODO: Add a check for similarity score threshold here. e.g., if similarity_results[0].score > 0.65:
                best_result = similarity_results[0]
                best_chunk = best_result.chunk
                target_section = best_chunk.source_sections[-1]

                # 3. ACT: If a valid navigation is found, send keyboard commands.
                self._perform_navigation(target_section, current_words, best_chunk)
                previous_words = current_words

            except Empty:
                continue
            except Exception as e:
                print(f"Error in Navigator thread: {e}")
                self.shutdown_flag.set()

    def _perform_navigation(self, target_section, current_words, best_chunk):
        current_idx = self.current_section.section_index
        target_idx = target_section.section_index
        distance = target_idx - current_idx

        if distance != 0:
            key_to_press = Key.right if distance > 0 else Key.left
            for _ in range(abs(distance)):
                self.keyboard_controller.press(key_to_press)
                self.keyboard_controller.release(key_to_press)
                time.sleep(0.01)  # Small delay for reliability

        self.current_section = target_section

        # Print status for user feedback
        recent_speech = " ".join(current_words[-7:])
        recent_match = " ".join(best_chunk.partial_content.strip().split()[-7:])
        print(
            f"\n[{target_section.section_index + 1}/{len(self.sections)}] Match Found"
        )
        print(f"  Speech -> ...{recent_speech}")
        print(f"  Match  -> ...{recent_match}")

    def _on_key_press(self, key):
        if key == Key.right:
            current_idx = self.current_section.section_index
            if current_idx < len(self.sections) - 1:
                self.current_section = self.sections[current_idx + 1]
                print(
                    f"\n[Manual] Next: {self.current_section.section_index + 1}/{len(self.sections)}"
                )
        elif key == Key.left:
            current_idx = self.current_section.section_index
            if current_idx > 0:
                self.current_section = self.sections[current_idx - 1]
                print(
                    f"\n[Manual] Previous: {self.current_section.section_index + 1}/{len(self.sections)}"
                )
        elif key == Key.insert:
            self.paused = not self.paused
            status = "Paused" if self.paused else "Resumed"
            print(
                f"\n[{status}] Automatic navigation is now {'OFF' if self.paused else 'ON'}."
            )

    def control(self):
        self.stt_processor_thread.start()
        self.navigator_thread.start()
        self.keyboard_listener.start()

        BLOCKSIZE = int(self.SAMPLE_RATE * self.FRAME_DURATION)

        try:
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=BLOCKSIZE,
                dtype="float32",
                channels=1,
                callback=self._audio_sampler_callback,
                latency="low",
            ):
                while not self.shutdown_flag.is_set():
                    self.shutdown_flag.wait(timeout=0.5)

        except KeyboardInterrupt:
            print("\nGracefully shutting down...")
        except Exception as e:
            print(f"\nAn error occurred in the audio stream: {e}")

        finally:
            if self.keyboard_listener.is_alive():
                self.keyboard_listener.stop()

            self.shutdown_flag.set()

            threads_to_join = [self.stt_processor_thread, self.navigator_thread]
            for thread in threads_to_join:
                if thread.is_alive():
                    thread.join(timeout=2.0)

            print("Shut down successfully.")
