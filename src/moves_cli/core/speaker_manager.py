import asyncio
import signal
import sys
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from types import FrameType

import typer
from rich.progress import (
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TaskID,
    TextColumn,
)
from rich.text import Text

from moves_cli.config import SECTIONS_FILENAME, SPEAKER_FILENAME
from moves_cli.models import ProcessResult, Speaker
from moves_cli.utils import id_generator
from moves_cli.utils.data_handler import DataHandler
from moves_cli.utils.output_formatter import output


# for just better ui
class MsecondsElapsedColumn(ProgressColumn):
    def render(self, task: "Task") -> Text:
        elapsed = task.elapsed
        if elapsed is None:
            return Text("-.-s")
        return Text(f"{elapsed:.1f}s")


class SpeakerManager:
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler
        self.SPEAKERS_PATH = self.data_handler.DATA_FOLDER.resolve() / "speakers"

    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """Compute xxh3_64 hash of a file. Returns hex string."""
        import xxhash

        hasher = xxhash.xxh3_64()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _write_speaker_yaml(self, path: Path, speaker: Speaker) -> None:
        from io import StringIO

        from ruamel.yaml import YAML

        data = {
            k: str(v) if isinstance(v, Path) else v for k, v in asdict(speaker).items()
        }
        yaml = YAML()
        yaml.default_flow_style = False
        output = StringIO()
        yaml.dump(data, output)
        self.data_handler.write(path, output.getvalue())

    def _read_speaker_yaml(self, path: Path) -> Speaker:
        from io import StringIO

        from ruamel.yaml import YAML

        yaml = YAML()
        data = yaml.load(StringIO(self.data_handler.read(path)))

        # Path string'lerini Path objesine dönüştür
        for k, v in data.items():
            if isinstance(v, str) and ("/" in v or "\\" in v):
                data[k] = Path(v)

        return Speaker(**data)

    def add(
        self, name: str, source_presentation: Path, source_transcript: Path
    ) -> Speaker:
        current_speakers = self.list()
        speaker_ids = [speaker.speaker_id for speaker in current_speakers]

        # revent name collision with existing ids
        if name in speaker_ids:
            raise ValueError(
                f"Speaker name '{name}' conflicts with an existing speaker ID. "
                f"Please choose a different name."
            )

        # generate unique speaker id with collision detection. maybe it needs
        # very long iterations to conflict but idk, just few more lines
        from moves_cli.config import SPEAKER_ID_GENERATION_MAX_RETRIES

        speaker_id = None
        for attempt in range(SPEAKER_ID_GENERATION_MAX_RETRIES):
            candidate_id = id_generator.generate_speaker_id(name)
            if candidate_id not in speaker_ids:
                speaker_id = candidate_id
                break

        if speaker_id is None:
            raise RuntimeError(
                f"Failed to generate unique speaker ID after {SPEAKER_ID_GENERATION_MAX_RETRIES} attempts. "
                f"This is extremely rare - please try again."  # ohhh, yes, the line that probably will never be reached
            )

        speaker_path = self.SPEAKERS_PATH / speaker_id
        speaker = Speaker(
            name=name,
            speaker_id=speaker_id,
            source_presentation=source_presentation.resolve(),
            source_transcript=source_transcript.resolve(),
        )

        # very understandable i think

        self._write_speaker_yaml(speaker_path / SPEAKER_FILENAME, speaker)
        return speaker

    def edit(
        self,
        speaker: Speaker,
        source_presentation: Path | None = None,
        source_transcript: Path | None = None,
    ) -> Speaker:
        speaker_path = self.SPEAKERS_PATH / speaker.speaker_id

        if source_presentation:
            speaker.source_presentation = source_presentation.resolve()
        if source_transcript:
            speaker.source_transcript = source_transcript.resolve()

        self._write_speaker_yaml(speaker_path / SPEAKER_FILENAME, speaker)
        return speaker

    def resolve(self, speaker_pattern: str) -> Speaker:
        speakers = self.list()

        # the optimization is made with llm in here
        # O(n) once
        by_id: dict[str, Speaker] = {}
        by_name: dict[str, list[Speaker]] = {}
        for speaker in speakers:
            by_id[speaker.speaker_id] = speaker
            by_name.setdefault(speaker.name, []).append(speaker)

        # O(1) lookup by ID
        if speaker := by_id.get(speaker_pattern):
            return speaker

        # O(1) lookup by name
        if matches := by_name.get(speaker_pattern):
            if len(matches) == 1:
                return matches[0]
            speaker_list = "\n".join([f"    {s.label}" for s in matches])
            raise ValueError(
                f"Multiple speakers found matching '{speaker_pattern}'. Be more specific:\n{speaker_list}"
            )

        raise ValueError(f"No speaker found matching '{speaker_pattern}'.")

    async def process(
        self,
        speakers: list[Speaker],
        llm_model: str,
        llm_api_key: str,
        skip_confirmation: bool = False,
    ) -> list[ProcessResult]:
        speaker_paths = [
            self.SPEAKERS_PATH / speaker.speaker_id for speaker in speakers
        ]

        typer.echo(f"Processing {len(speakers)} speaker(s).")
        typer.echo()

        for speaker in speakers:
            source_presentation = speaker.source_presentation
            source_transcript = speaker.source_transcript

            # Validate source files exist (no backup fallback)
            missing_files = []
            if not source_presentation.exists():
                missing_files.append(f"Presentation: {source_presentation}")
            if not source_transcript.exists():
                missing_files.append(f"Transcript: {source_transcript}")

            if missing_files:
                raise FileNotFoundError(
                    f"Missing source files for speaker {speaker.label}:\n"
                    + "\n".join(f"  - {f}" for f in missing_files)
                    + "\n\nPlease update file paths with 'moves speaker edit' command."
                )

            typer.echo(
                output(
                    speaker.label,
                    {
                        "Presentation": source_presentation,
                        "Transcript": source_transcript,
                    },
                )
            )

        typer.echo()

        if not skip_confirmation:
            typer.confirm("Proceed?", default=True, abort=True)
            typer.echo()

        # Use rich progress for dynamic feedback
        with Progress(
            SpinnerColumn(style=""),
            TextColumn("{task.description}"),
            MsecondsElapsedColumn(),
            transient=True,
        ) as progress:
            # i have no idea what is sigint but i know its for direct stop the llm generation
            # maybe there is built-in solution in litellm or instructor, look into it
            # Install SIGINT handler to force exit on Ctrl+C
            original_sigint = signal.getsignal(signal.SIGINT)

            def sigint_handler(signum: int, frame: FrameType | None) -> None:
                progress.stop()
                typer.echo("\nCancelled.")
                sys.exit(130)  # 128 + SIGINT(2)

            signal.signal(signal.SIGINT, sigint_handler)

            async def process_speaker(
                speaker: Speaker, speaker_path: Path, delay: int, task_id: TaskID
            ) -> ProcessResult:
                import time

                source_presentation = speaker.source_presentation
                source_transcript = speaker.source_transcript

                def progress_callback(msg: str) -> None:
                    progress.update(
                        task_id,
                        description=f"{speaker.label}: {msg}",
                    )

                progress_callback("Waiting...")
                await asyncio.sleep(delay)

                progress.start_task(task_id)
                start_time = time.perf_counter()
                progress_callback("Starting...")

                # Compute hashes before copying (for change detection)
                progress_callback("Computing file hashes...")
                presentation_hash = await asyncio.to_thread(
                    self.compute_file_hash, source_presentation
                )
                transcript_hash = await asyncio.to_thread(
                    self.compute_file_hash, source_transcript
                )

                # Copy to temp directory for atomic/safe processing
                import shutil
                import tempfile

                temp_dir = Path(tempfile.mkdtemp(prefix="moves_"))
                try:
                    progress_callback("Copying files to temp...")
                    presentation_path = temp_dir / "presentation.pdf"
                    transcript_path = temp_dir / "transcript.pdf"

                    await asyncio.to_thread(
                        shutil.copy2, source_presentation, presentation_path
                    )
                    await asyncio.to_thread(
                        shutil.copy2, source_transcript, transcript_path
                    )

                    from moves_cli.core.components.section_producer import (
                        SectionProducer,
                    )

                    section_producer = SectionProducer()

                    # Run generation in a daemon thread so it doesn't block sys.exit()
                    loop = asyncio.get_running_loop()
                    future = loop.create_future()

                    def run_generation() -> None:
                        try:
                            result = section_producer.generate_sections(
                                presentation_path=presentation_path,
                                transcript_path=transcript_path,
                                llm_model=llm_model,
                                llm_api_key=llm_api_key,
                                callback=progress_callback,
                            )
                            loop.call_soon_threadsafe(future.set_result, result)
                        except Exception as e:
                            loop.call_soon_threadsafe(future.set_exception, e)

                    # Daemon thread dies when main process exits
                    thread = threading.Thread(target=run_generation, daemon=True)
                    thread.start()

                    sections = await future

                    progress_callback("Writing to file...")
                    self.data_handler.write(
                        speaker_path / SECTIONS_FILENAME,
                        section_producer.convert_to_yaml(sections),
                    )

                    processing_time = time.perf_counter() - start_time

                    # Update progress to show Done and freeze timer
                    progress.update(
                        task_id,
                        description=f"Processing {speaker.label}... Done",
                    )
                    progress.stop_task(task_id)

                    # Update speaker metadata with timestamp and hashes
                    speaker.last_processed = datetime.now().isoformat()
                    speaker.presentation_hash = presentation_hash
                    speaker.transcript_hash = transcript_hash
                    # Compute sections hash after writing
                    sections_hash = self.compute_file_hash(
                        speaker_path / SECTIONS_FILENAME
                    )
                    speaker.sections_hash = sections_hash
                    self._write_speaker_yaml(speaker_path / SPEAKER_FILENAME, speaker)

                    return ProcessResult(
                        section_count=len(sections),
                        speaker_id=speaker.speaker_id,
                        processing_time_seconds=processing_time,
                    )
                finally:
                    # Clean up temp directory
                    await asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)

            tasks = []
            try:
                for idx, (speaker, speaker_path) in enumerate(
                    zip(speakers, speaker_paths)
                ):
                    task_id = progress.add_task(
                        description=f"Processing {speaker.label}...",
                        total=None,
                        start=False,
                    )
                    tasks.append(process_speaker(speaker, speaker_path, idx, task_id))

                results = await asyncio.gather(*tasks)
                return results
            finally:
                # Restore original signal handler
                signal.signal(signal.SIGINT, original_sigint)

    def delete(self, speaker: Speaker) -> bool:
        # the most minimal thing
        speaker_path = self.SPEAKERS_PATH / speaker.speaker_id
        result = bool(self.data_handler.delete(speaker_path))
        return result

    def list(self) -> list[Speaker]:
        speakers = []
        for folder in self.data_handler.list(self.SPEAKERS_PATH):
            if folder.is_dir():
                speaker_yaml = folder / SPEAKER_FILENAME
                if speaker_yaml.exists():
                    speakers.append(self._read_speaker_yaml(speaker_yaml))
        return speakers
