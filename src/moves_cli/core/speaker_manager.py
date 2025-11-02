import asyncio
import json
from dataclasses import asdict
from pathlib import Path

from moves_cli.data.models import Speaker, ProcessResult
from moves_cli.utils import id_generator, data_handler


class SpeakerManager:
    def __init__(self):
        self.SPEAKERS_PATH = data_handler.DATA_FOLDER.resolve() / "speakers"

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
        data_handler.write(speaker_path / "speaker.json", json.dumps(data, indent=4))
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
        data_handler.write(speaker_path / "speaker.json", json.dumps(data, indent=4))
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
                speaker_list = "\n".join(
                    [f"    {s.name} ({s.speaker_id})" for s in matched_speakers]
                )
                raise ValueError(
                    f"Multiple speakers found matching '{speaker_pattern}'. Be more specific:\n{speaker_list}"
                )

        raise ValueError(f"No speaker found matching '{speaker_pattern}'.")

    def process(
        self, speakers: list[Speaker], llm_model: str, llm_api_key: str
    ) -> list[ProcessResult]:
        async def run():
            speaker_paths = [
                self.SPEAKERS_PATH / speaker.speaker_id for speaker in speakers
            ]

            # Validate all speakers' files upfront before starting async processing
            for speaker, speaker_path in zip(speakers, speaker_paths):
                source_presentation = speaker.source_presentation
                source_transcript = speaker.source_transcript
                local_presentation = speaker_path / "presentation.pdf"
                local_transcript = speaker_path / "transcript.pdf"

                # Determine file sources
                presentation_from = None
                transcript_from = None

                # Check presentation file
                if source_presentation.exists():
                    presentation_from = "SOURCE"
                elif local_presentation.exists():
                    presentation_from = "LOCAL"
                else:
                    raise FileNotFoundError(
                        f"Missing presentation file for speaker '{speaker.name}' ({speaker.speaker_id})"
                    )

                # Check transcript file
                if source_transcript.exists():
                    transcript_from = "SOURCE"
                elif local_transcript.exists():
                    transcript_from = "LOCAL"
                else:
                    raise FileNotFoundError(
                        f"Missing transcript file for speaker '{speaker.name}' ({speaker.speaker_id})"
                    )

                # Print file sources for the speaker
                file_sources = (
                    f"{presentation_from} presentation & {transcript_from} transcript"
                )
                if len(speakers) == 1:
                    print(f"Using {file_sources}.")
                else:
                    print(f"'{speaker.name}' ({speaker.speaker_id}) -> {file_sources}")

            async def process_speaker(speaker, speaker_path, delay):
                import time

                # File location checking and moving operations at the top
                source_presentation = speaker.source_presentation
                source_transcript = speaker.source_transcript

                local_presentation = speaker_path / "presentation.pdf"
                local_transcript = speaker_path / "transcript.pdf"

                presentation_path, transcript_path = None, None

                # Handle presentation file
                if source_presentation.exists():
                    data_handler.copy(source_presentation, speaker_path)
                    if source_presentation.name != "presentation.pdf":
                        relative_file_path = (
                            speaker_path / source_presentation.name
                        ).relative_to(data_handler.DATA_FOLDER)
                        data_handler.rename(relative_file_path, "presentation.pdf")
                    presentation_path = speaker_path / "presentation.pdf"
                elif local_presentation.exists():
                    presentation_path = local_presentation
                else:
                    raise FileNotFoundError(
                        f"Missing presentation file for speaker '{speaker.name}' ({speaker.speaker_id})"
                    )

                # Handle transcript file
                if source_transcript.exists():
                    data_handler.copy(source_transcript, speaker_path)
                    if source_transcript.name != "transcript.pdf":
                        relative_file_path = (
                            speaker_path / source_transcript.name
                        ).relative_to(data_handler.DATA_FOLDER)
                        data_handler.rename(relative_file_path, "transcript.pdf")
                    transcript_path = speaker_path / "transcript.pdf"
                elif local_transcript.exists():
                    transcript_path = local_transcript
                else:
                    raise FileNotFoundError(
                        f"Missing transcript file for speaker '{speaker.name}' ({speaker.speaker_id})"
                    )

                # Apply staggered delay before LLM API calls to avoid rate limiting
                await asyncio.sleep(delay)

                # Lazy import - only load when processing is actually needed (after file validation)
                from moves_cli.core.components import section_producer, chunk_producer

                start_time = time.perf_counter()

                sections = await asyncio.to_thread(
                    section_producer.generate_sections,
                    presentation_path=presentation_path,
                    transcript_path=transcript_path,
                    llm_model=llm_model,
                    llm_api_key=llm_api_key,
                )

                data_handler.write(
                    speaker_path / "sections.json",
                    json.dumps(section_producer.convert_to_list(sections), indent=2),
                )

                # Generate chunks to get chunk count
                chunks = chunk_producer.generate_chunks(sections, window_size=12)

                processing_time = time.perf_counter() - start_time

                return ProcessResult(
                    section_count=len(sections),
                    chunk_count=len(chunks),
                    speaker_id=speaker.speaker_id,
                    processing_time_seconds=processing_time,
                )

            tasks = [
                process_speaker(speaker, speaker_path, idx)
                for idx, (speaker, speaker_path) in enumerate(
                    zip(speakers, speaker_paths)
                )
            ]
            results = await asyncio.gather(*tasks)
            return results

        return asyncio.run(run())

    def delete(self, speaker: Speaker) -> bool:
        speaker_path = self.SPEAKERS_PATH / speaker.speaker_id
        return bool(data_handler.delete(speaker_path))

    def list(self) -> list[Speaker]:
        speakers = []
        for folder in data_handler.list(self.SPEAKERS_PATH):
            if folder.is_dir():
                speaker_json = folder / "speaker.json"
                if speaker_json.exists():
                    data = json.loads(data_handler.read(speaker_json))
                    for k, v in data.items():
                        if isinstance(v, str) and ("/" in v or "\\" in v):
                            data[k] = Path(v)
                    speakers.append(Speaker(**data))
        return speakers
