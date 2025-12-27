import asyncio
import json
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

from moves_cli.models import ProcessResult, Speaker
from moves_cli.utils import id_generator
from moves_cli.utils.data_handler import DataHandler
from moves_cli.utils.output_formatter import output


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

    def add(
        self, name: str, source_presentation: Path, source_transcript: Path
    ) -> Speaker:
        current_speakers = self.list()
        speaker_ids = [speaker.speaker_id for speaker in current_speakers]

        # Check 1: Prevent name collision with existing IDs (security/UX)
        if name in speaker_ids:
            raise ValueError(
                f"Speaker name '{name}' conflicts with an existing speaker ID. "
                f"Please choose a different name."
            )

        # Check 2: Generate unique speaker ID with collision detection
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
                f"This is extremely rare - please try again."
            )

        speaker_path = self.SPEAKERS_PATH / speaker_id
        speaker = Speaker(
            name=name,
            speaker_id=speaker_id,
            source_presentation=source_presentation.resolve(),
            source_transcript=source_transcript.resolve(),
        )

        data = {
            k: str(v) if isinstance(v, Path) else v for k, v in asdict(speaker).items()
        }
        self.data_handler.write(
            speaker_path / "speaker.json", json.dumps(data, indent=4)
        )
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

        data = {
            k: str(v) if isinstance(v, Path) else v for k, v in asdict(speaker).items()
        }
        self.data_handler.write(
            speaker_path / "speaker.json", json.dumps(data, indent=4)
        )
        return speaker

    def resolve(self, speaker_pattern: str) -> Speaker:
        speakers = self.list()

        # Build lookup dicts - O(n) once
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

        for speaker, speaker_path in zip(speakers, speaker_paths):
            source_presentation = speaker.source_presentation
            source_transcript = speaker.source_transcript
            backup_presentation = speaker_path / "presentation.pdf"
            backup_transcript = speaker_path / "transcript.pdf"

            presentation_from = None
            transcript_from = None

            if source_presentation.exists():
                presentation_from = "SOURCE"
                pres_path_display = source_presentation
            elif backup_presentation.exists():
                presentation_from = "BACKUP"
                pres_path_display = backup_presentation
            else:
                raise FileNotFoundError(
                    f"Missing presentation file for speaker {speaker.label}"
                )

            if source_transcript.exists():
                transcript_from = "SOURCE"
                trans_path_display = source_transcript
            elif backup_transcript.exists():
                transcript_from = "BACKUP"
                trans_path_display = backup_transcript
            else:
                raise FileNotFoundError(
                    f"Missing transcript file for speaker {speaker.label}"
                )

            typer.echo(
                output(
                    speaker.label,
                    {
                        f"Presentation ({presentation_from})": pres_path_display,
                        f"Transcript ({transcript_from})": trans_path_display,
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

                backup_presentation = speaker_path / "presentation.pdf"
                backup_transcript = speaker_path / "transcript.pdf"

                presentation_path, transcript_path = None, None

                if source_presentation.exists():
                    progress_callback("Copying presentation...")
                    await asyncio.to_thread(
                        self.data_handler.copy, source_presentation, speaker_path
                    )
                    if source_presentation.name != "presentation.pdf":
                        relative_file_path = (
                            speaker_path / source_presentation.name
                        ).relative_to(self.data_handler.DATA_FOLDER)
                        await asyncio.to_thread(
                            self.data_handler.rename,
                            relative_file_path,
                            "presentation.pdf",
                        )
                    presentation_path = speaker_path / "presentation.pdf"
                elif backup_presentation.exists():
                    presentation_path = backup_presentation
                else:
                    raise FileNotFoundError(
                        f"Missing presentation file for speaker {speaker.label}"
                    )

                if source_transcript.exists():
                    progress_callback("Copying transcript...")
                    await asyncio.to_thread(
                        self.data_handler.copy, source_transcript, speaker_path
                    )
                    if source_transcript.name != "transcript.pdf":
                        relative_file_path = (
                            speaker_path / source_transcript.name
                        ).relative_to(self.data_handler.DATA_FOLDER)
                        await asyncio.to_thread(
                            self.data_handler.rename,
                            relative_file_path,
                            "transcript.pdf",
                        )
                    transcript_path = speaker_path / "transcript.pdf"
                elif backup_transcript.exists():
                    transcript_path = backup_transcript
                else:
                    raise FileNotFoundError(
                        f"Missing transcript file for speaker {speaker.label}"
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
                    speaker_path / "sections.json",
                    json.dumps(section_producer.convert_to_list(sections), indent=2),
                )

                processing_time = time.perf_counter() - start_time

                # Update progress to show Done and freeze timer
                progress.update(
                    task_id,
                    description=f"Processing {speaker.label}... Done",
                )
                progress.stop_task(task_id)

                # Update speaker last_processed timestamp
                speaker.last_processed = datetime.now().isoformat()
                data = {
                    k: str(v) if isinstance(v, Path) else v
                    for k, v in asdict(speaker).items()
                }
                self.data_handler.write(
                    speaker_path / "speaker.json", json.dumps(data, indent=4)
                )

                return ProcessResult(
                    section_count=len(sections),
                    speaker_id=speaker.speaker_id,
                    processing_time_seconds=processing_time,
                )

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
        speaker_path = self.SPEAKERS_PATH / speaker.speaker_id
        result = bool(self.data_handler.delete(speaker_path))
        return result

    def list(self) -> list[Speaker]:
        speakers = []
        for folder in self.data_handler.list(self.SPEAKERS_PATH):
            if folder.is_dir():
                speaker_json = folder / "speaker.json"
                if speaker_json.exists():
                    data = json.loads(self.data_handler.read(speaker_json))
                    for k, v in data.items():
                        if isinstance(v, str) and ("/" in v or "\\" in v):
                            data[k] = Path(v)
                    speakers.append(Speaker(**data))
        return speakers
