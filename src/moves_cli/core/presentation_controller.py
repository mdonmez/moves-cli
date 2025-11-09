import logging
import threading
import time
from contextlib import suppress
from pathlib import Path
from queue import Empty, Full, Queue

import sounddevice as sd
from pynput.keyboard import Controller, Key
from sherpa_onnx import OnlineRecognizer

from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.data.models import Section
from moves_cli.utils import data_handler, model_downloader, text_normalizer

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class PresentationController:
    SAMPLE_RATE = 16000
    FRAME_DURATION = 0.1
    AUDIO_QUEUE_SIZE = 5
    WORDS_QUEUE_SIZE = 1
    NUM_THREADS = 8
    DISPLAY_WORD_COUNT = 7
    KEY_PRESS_DELAY = 0.01
    SIMILARITY_THRESHOLD = 0.7
    QUEUE_TIMEOUT = 1.0
    THREAD_JOIN_TIMEOUT = 2.0
    SHUTDOWN_CHECK_INTERVAL = 0.5
    MODEL_DIR = Path(
        data_handler.DATA_FOLDER / "ml_models" / "nemo-streaming-stt-480ms-int8"
    )

    def __init__(
        self,
        sections: list[Section],
        window_size: int = 12,
    ) -> None:
        self.window_size = window_size
        self.sections = sections
        self.current_section = sections[0]
        self.section_lock = threading.Lock()
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
                num_threads=self.NUM_THREADS,
                decoding_method="greedy_search",
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load STT model from {self.MODEL_DIR}: {e}"
            ) from e

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

    def _audio_sampler_callback(self, indata, _frames, _time, _status) -> None:
        if not self.audio_queue.full():
            with suppress(Full):
                self.audio_queue.put_nowait(indata[:, 0].copy())

    def _stt_processor_task(self) -> None:
        stream = self.recognizer.create_stream()
        while not self.shutdown_flag.is_set():
            try:
                audio_chunk = self.audio_queue.get(timeout=self.QUEUE_TIMEOUT)

                stream.accept_waveform(self.SAMPLE_RATE, audio_chunk)
                while self.recognizer.is_ready(stream):
                    self.recognizer.decode_stream(stream)

                if text := self.recognizer.get_result(stream):
                    recent_words = text.strip().split()[-self.window_size :]
                    normalized = text_normalizer.normalize_text(" ".join(recent_words))
                    words = normalized.strip().split()

                    if words:
                        with suppress(Empty):
                            self.words_queue.get_nowait()
                        with suppress(Full):
                            self.words_queue.put_nowait(words)

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in STT Processor thread: {e}")
                self.shutdown_flag.set()

    def _navigator_task(self) -> None:
        previous_words = []
        while not self.shutdown_flag.is_set():
            try:
                current_words = self.words_queue.get(timeout=self.QUEUE_TIMEOUT)

                if current_words == previous_words:
                    continue

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

                top_match = similarity_results[0]
                best_chunk = top_match.chunk
                target_section = best_chunk.source_sections[-1]
                slide_delta = (
                    target_section.section_index - current_section.section_index
                )

                slide_position = (
                    f"{current_section.section_index + 1}/{len(self.sections)}"
                )
                similarity_pct = f"%{int(top_match.score * 100)}"

                match (top_match.score >= self.SIMILARITY_THRESHOLD, slide_delta):
                    case (False, _):
                        status = "✖"
                    case (True, 0):
                        status = "■"
                    case (True, delta) if delta > 0:
                        status = f"▶ {abs(delta)}"
                    case (True, delta):
                        status = f"◀ {abs(delta)}"

                speech_preview = " ".join(current_words[-self.DISPLAY_WORD_COUNT :])
                match_words = best_chunk.partial_content.strip().split()
                match_preview = " ".join(match_words[-self.DISPLAY_WORD_COUNT :])

                logger.info(
                    f"{slide_position} | {similarity_pct} | {status}\n"
                    f"    Speech → ...{speech_preview}\n"
                    f"    Match  → ...{match_preview}\n"
                )

                if top_match.score >= self.SIMILARITY_THRESHOLD:
                    self._perform_navigation(target_section)

                previous_words = current_words

            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in Navigator thread: {e}")
                self.shutdown_flag.set()

    def _perform_navigation(self, target_section: Section) -> None:
        with self.section_lock:
            current_slide = self.current_section.section_index
            target_slide = target_section.section_index
            slide_delta = target_slide - current_slide

            if slide_delta != 0:
                key_to_press = Key.right if slide_delta > 0 else Key.left
                for _ in range(abs(slide_delta)):
                    self.keyboard_controller.press(key_to_press)
                    self.keyboard_controller.release(key_to_press)
                    time.sleep(self.KEY_PRESS_DELAY)

            self.current_section = target_section

    def control(self) -> None:
        self.stt_processor_thread.start()
        self.navigator_thread.start()

        blocksize = int(self.SAMPLE_RATE * self.FRAME_DURATION)

        try:
            with sd.InputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=blocksize,
                dtype="float32",
                channels=1,
                callback=self._audio_sampler_callback,
                latency="low",
            ):
                while not self.shutdown_flag.is_set():
                    self.shutdown_flag.wait(timeout=self.SHUTDOWN_CHECK_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\nGracefully shutting down...")
        except Exception as e:
            logger.error(f"\nAn error occurred in the audio stream: {e}")

        finally:
            self.shutdown_flag.set()

            threads_to_join = [self.stt_processor_thread, self.navigator_thread]
            for thread in threads_to_join:
                if thread.is_alive():
                    thread.join(timeout=self.THREAD_JOIN_TIMEOUT)

            logger.info("Shut down successfully\n")
