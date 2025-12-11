import asyncio
import json
import signal
import sys
import threading
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import typer
from rich.progress import (
    Progress,
    ProgressColumn,
    SpinnerColumn,
    Task,
    TextColumn,
)
from rich.text import Text

from moves_cli.models import ProcessResult, Speaker
from moves_cli.utils import id_generator
from moves_cli.utils.data_handler import DataHandler


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

        if name in speaker_ids:
            raise ValueError(
                f"Given name '{name}' can't be a same with one of the existing speakers' IDs."
            )

        speaker_id = id_generator.generate_speaker_id(name)
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
        speaker_ids = [speaker.speaker_id for speaker in speakers]

        if speaker_pattern in speaker_ids:
            return speakers[speaker_ids.index(speaker_pattern)]

        matched_speakers = [
            speaker for speaker in speakers if speaker.name == speaker_pattern
        ]
        if matched_speakers:
            if len(matched_speakers) == 1:
                return matched_speakers[0]
            else:
                speaker_list = "\n".join([f"    {s.label}" for s in matched_speakers])
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

        typer.echo(f"Processing Plan for {len(speakers)} speaker(s):\n")

        for speaker, speaker_path in zip(speakers, speaker_paths):
            source_presentation = speaker.source_presentation
            source_transcript = speaker.source_transcript
            local_presentation = speaker_path / "presentation.pdf"
            local_transcript = speaker_path / "transcript.pdf"

            presentation_from = None
            transcript_from = None

            if source_presentation.exists():
                presentation_from = "SOURCE"
                pres_path_display = source_presentation
            elif local_presentation.exists():
                presentation_from = "LOCAL"
                pres_path_display = local_presentation
            else:
                raise FileNotFoundError(
                    f"Missing presentation file for speaker {speaker.label}"
                )

            if source_transcript.exists():
                transcript_from = "SOURCE"
                trans_path_display = source_transcript
            elif local_transcript.exists():
                transcript_from = "LOCAL"
                trans_path_display = local_transcript
            else:
                raise FileNotFoundError(
                    f"Missing transcript file for speaker {speaker.label}"
                )

            typer.echo(speaker.label)
            typer.echo(f"    Presentation ({presentation_from}) -> {pres_path_display}")
            typer.echo(f"    Transcript ({transcript_from}) -> {trans_path_display}")
            typer.echo()

        typer.echo()

        if not skip_confirmation:
            typer.confirm("Do you want to proceed?", default=True, abort=True)
            typer.echo("Yes")
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

            def sigint_handler(signum, frame):
                progress.stop()
                typer.echo("\nCancelled.")
                sys.exit(130)  # 128 + SIGINT(2)

            signal.signal(signal.SIGINT, sigint_handler)

            async def process_speaker(speaker, speaker_path, delay, task_id):
                import time

                source_presentation = speaker.source_presentation
                source_transcript = speaker.source_transcript

                def progress_callback(msg: str):
                    progress.update(
                        task_id,
                        description=f"{speaker.label}: {msg}",
                    )

                progress_callback("Waiting...")
                await asyncio.sleep(delay)

                progress.start_task(task_id)
                start_time = time.perf_counter()
                progress_callback("Starting...")

                local_presentation = speaker_path / "presentation.pdf"
                local_transcript = speaker_path / "transcript.pdf"

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
                elif local_presentation.exists():
                    presentation_path = local_presentation
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
                elif local_transcript.exists():
                    transcript_path = local_transcript
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

                def run_generation():
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
