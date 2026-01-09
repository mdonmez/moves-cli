import asyncio
import threading
import time
from contextlib import suppress
from pathlib import Path
from queue import Empty, Full, Queue
import typer

import sounddevice as sd
from pynput.keyboard import Controller, Key
from sherpa_onnx import OnlineRecognizer, VadModelConfig, VoiceActivityDetector

from moves_cli.config import SIMILARITY_THRESHOLD, WINDOW_SIZE
from moves_cli.core.components import chunk_producer
from moves_cli.core.components.similarity_calculator import SimilarityCalculator
from moves_cli.models import Section, SttModel, VadModel
from moves_cli.utils import model_preparer, text_normalizer


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
    # VAD configuration (optimized for noisy environments like 1000+ person venues)
    VAD_THRESHOLD: float = 0.5  # Higher = less sensitive (filters clicks/noise)
    VAD_MIN_SILENCE: float = 0.3  # Seconds of silence to end speech segment
    VAD_MIN_SPEECH: float = (
        0.15  # Minimum speech duration to detect (filters short noises)
    )
    VAD_WINDOW_SIZE: int = 512  # ~32ms analysis window at 16kHz
    VAD_BUFFER_SIZE: float = 30.0  # Circular buffer size in seconds
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

        # VAD status flag for display (atomic bool via Event for thread-safety)
        self._vad_active = threading.Event()

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

    def _audio_sampler_callback(self, indata, _frames, _time, _status) -> None:
        """VAD-gated audio sampling: only speech passes to STT."""
        samples = indata[:, 0].copy()

        # Feed samples to VAD for speech detection
        self.vad.accept_waveform(samples)

        # Update VAD status flag for display
        is_speech = self.vad.is_speech_detected()
        if is_speech:
            self._vad_active.set()
        else:
            self._vad_active.clear()

        # Print VAD status every 100ms (inline overwrite with \r)
        vad_status = "🎙️ SPEECH" if is_speech else "🔇 SILENT"
        print(f"\r[VAD] {vad_status}  ", end="", flush=True)

        # Only send to STT if speech is detected (filters crowd noise, coughs, applause)
        if is_speech:
            if not self.audio_queue.full():
                with suppress(Full):
                    self.audio_queue.put_nowait(samples)

    def _stt_processor_task(self) -> None:
        stream = self.recognizer.create_stream()
        while not self.shutdown_flag.is_set():
            try:
                audio_chunk = self.audio_queue.get(timeout=self.QUEUE_TIMEOUT)

                stream.accept_waveform(self.SAMPLE_RATE, audio_chunk)
                while self.recognizer.is_ready(stream):
                    self.recognizer.decode_stream(stream)

                if text := self.recognizer.get_result(stream):
                    # we're getting the last window size and process it for real-time app
                    recent_words = text.strip().split()[-self.window_size :]
                    normalized = text_normalizer.normalize_text(" ".join(recent_words))
                    words = normalized.strip().split()

                    if words:
                        # put the words into a queue for processing
                        with suppress(Empty):
                            self.words_queue.get_nowait()
                        with suppress(Full):
                            self.words_queue.put_nowait(words)

            except Empty:
                continue
            except Exception as e:
                typer.echo(f"Error in STT Processor thread: {e}", err=True)
                self.shutdown_flag.set()

    def _navigator_task(self) -> None:
        previous_words = []
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

                slide_position = f"{current_section.section_index}/{len(self.sections)}"
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

                # VAD status indicator
                vad_indicator = "🎙️" if self._vad_active.is_set() else "🔇"

                # Clear inline VAD status line before printing full output
                print("\r" + " " * 20 + "\r", end="", flush=True)
                typer.echo(
                    f"{slide_position} | {similarity_pct} | {status} | {vad_indicator}\n"
                    f"    Speech → ...{speech_preview}\n"
                    f"    Match  → ...{match_preview}\n"
                )

                # if the similarity is above the threshold, then act
                if top_match.score >= self.SIMILARITY_THRESHOLD:
                    self._perform_navigation(target_section)

                previous_words = current_words

            except Empty:
                continue
            except Exception as e:
                typer.echo(f"Error in Navigator thread: {e}", err=True)
                self.shutdown_flag.set()

    def _perform_navigation(self, target_section: Section) -> None:
        with self.section_lock:
            current_slide = self.current_section.section_index
            target_slide = target_section.section_index
            slide_delta = target_slide - current_slide

            if slide_delta != 0:
                # if the slide delta is positive, press right arrow key, otherwise press left arrow key
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
            # some audio config, i should move some of them to the top
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
            typer.echo("\nShutting down...")
        except Exception as e:
            typer.echo(f"\nAn error occurred in the audio stream: {e}", err=True)

        finally:
            self.shutdown_flag.set()

            # gracefully shutdown the threads
            threads_to_join = [self.stt_processor_thread, self.navigator_thread]
            for thread in threads_to_join:
                if thread.is_alive():
                    thread.join(timeout=self.THREAD_JOIN_TIMEOUT)

            typer.echo("Shut down successfully.")
