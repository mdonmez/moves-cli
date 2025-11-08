import threading
import time
from contextlib import suppress
from pathlib import Path
from queue import Empty, Full, Queue

import sounddevice as sd
from pynput.keyboard import Controller, Key, Listener
from sherpa_onnx import OnlineRecognizer

from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.data.models import Chunk, Section
from moves_cli.utils import data_handler, model_downloader, text_normalizer


class PresentationController:
    SAMPLE_RATE = 16000
    FRAME_DURATION = 0.1
    AUDIO_QUEUE_SIZE = 5
    WORDS_QUEUE_SIZE = 1
    NUM_THREADS = 8
    DISPLAY_WORD_COUNT = 7
    KEY_PRESS_DELAY = 0.01
    MODEL_DIR = Path(
        data_handler.DATA_FOLDER / "ml_models" / "nemo-streaming-stt-480ms-int8"
    )

    def __init__(
        self,
        sections: list[Section],
        window_size: int = 12,
    ) -> None:
        # Core state
        self.window_size = window_size
        self.sections = sections
        self.current_section = sections[0]
        self.section_lock = threading.Lock()
        self.paused = False
        self.shutdown_flag = threading.Event()

        # Inter-thread communication
        self.audio_queue = Queue(maxsize=PresentationController.AUDIO_QUEUE_SIZE)
        self.words_queue = Queue(maxsize=PresentationController.WORDS_QUEUE_SIZE)

        # Model downloads
        model_downloader.download_model("embedding")
        model_downloader.download_model("stt")

        # STT model initialization
        try:
            self.recognizer = OnlineRecognizer.from_transducer(
                tokens=str(self.MODEL_DIR.joinpath("tokens.txt")),
                encoder=str(self.MODEL_DIR.joinpath("encoder.int8.onnx")),
                decoder=str(self.MODEL_DIR.joinpath("decoder.int8.onnx")),
                joiner=str(self.MODEL_DIR.joinpath("joiner.int8.onnx")),
                num_threads=self.NUM_THREADS,
                decoding_method="greedy_search",
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load STT model from {self.MODEL_DIR}: {e}"
            ) from e

        # Processing pipeline
        self.chunks = chunk_producer.generate_chunks(sections, window_size)
        self.candidate_chunk_generator = chunk_producer.CandidateChunkGenerator(
            self.chunks
        )
        self.similarity_calculator = SimilarityCalculator(self.chunks)

        # Controllers
        self.keyboard_controller = Controller()

        # Worker threads
        self.stt_processor_thread = threading.Thread(
            target=self._stt_processor_task, daemon=True
        )
        self.navigator_thread = threading.Thread(
            target=self._navigator_task, daemon=True
        )
        self.keyboard_listener = Listener(on_press=self._on_key_press)

    def _audio_sampler_callback(self, indata, frames, time, status) -> None:
        if not self.audio_queue.full():
            with suppress(Full):
                self.audio_queue.put_nowait(indata[:, 0].copy())

    def _stt_processor_task(self) -> None:
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
                    if not (
                        latest_words := normalized_text.strip().split()[
                            -self.window_size :
                        ]
                    ):
                        continue

                    # Clear stale data and publish new words
                    with suppress(Empty):
                        self.words_queue.get_nowait()
                    with suppress(Full):
                        self.words_queue.put_nowait(latest_words)

            except Empty:
                # Timeout occurred, loop continues to check shutdown_flag.
                continue
            except Exception as e:
                print(f"Error in STT Processor thread: {e}")
                self.shutdown_flag.set()

    def _navigator_task(self) -> None:
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
                with self.section_lock:
                    current_section = self.current_section

                if not (
                    candidate_chunks
                    := self.candidate_chunk_generator.get_candidate_chunks(
                        current_section
                    )
                ):
                    continue

                similarity_results = self.similarity_calculator.compare(
                    input_text, candidate_chunks
                )

                # TODO: Add a check for similarity score threshold here. e.g., if similarity_results[0].score > 0.65:
                top_match = similarity_results[0]
                best_chunk = top_match.chunk
                target_section = best_chunk.source_sections[-1]

                # 3. ACT: If a valid navigation is found, send keyboard commands.
                self._perform_navigation(target_section, current_words, best_chunk)
                previous_words = current_words

            except Empty:
                continue
            except Exception as e:
                print(f"Error in Navigator thread: {e}")
                self.shutdown_flag.set()

    def _perform_navigation(
        self, target_section: Section, current_words: list[str], best_chunk: Chunk
    ) -> None:
        with self.section_lock:
            current_slide = self.current_section.section_index
            target_slide = target_section.section_index
            slide_delta = target_slide - current_slide

            if slide_delta != 0:
                key_to_press = Key.right if slide_delta > 0 else Key.left
                for _ in range(abs(slide_delta)):
                    self.keyboard_controller.press(key_to_press)
                    self.keyboard_controller.release(key_to_press)
                    time.sleep(self.KEY_PRESS_DELAY)  # Small delay for reliability

            self.current_section = target_section

        # Print status for user feedback
        recent_speech = " ".join(current_words[-self.DISPLAY_WORD_COUNT :])
        recent_match = " ".join(
            best_chunk.partial_content.strip().split()[-self.DISPLAY_WORD_COUNT :]
        )
        print(
            f"\n[{target_section.section_index + 1}/{len(self.sections)}] Match Found"
        )
        print(f"  Speech -> ...{recent_speech}")
        print(f"  Match  -> ...{recent_match}")

    def _on_key_press(self, key) -> None:
        with self.section_lock:
            current_slide = self.current_section.section_index

            match key:
                case Key.right:
                    if current_slide < len(self.sections) - 1:
                        self.current_section = self.sections[current_slide + 1]
                        print(
                            f"\n[Manual] Next: {self.current_section.section_index + 1}/{len(self.sections)}"
                        )
                case Key.left:
                    if current_slide > 0:
                        self.current_section = self.sections[current_slide - 1]
                        print(
                            f"\n[Manual] Previous: {self.current_section.section_index + 1}/{len(self.sections)}"
                        )
                case Key.insert:
                    self.paused = not self.paused
                    match self.paused:
                        case True:
                            print("\n[Paused] Automatic navigation is now OFF.")
                        case False:
                            print("\n[Resumed] Automatic navigation is now ON.")

    def control(self) -> None:
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
