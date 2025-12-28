import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from moves_cli.config import DEFAULT_API_KEY, DEFAULT_LLM_MODEL, WINDOW_SIZE
from moves_cli.models import Section
from moves_cli.utils.data_handler import DataHandler
from moves_cli.utils.output_formatter import output


def speaker_manager_instance():
    from moves_cli.core.speaker_manager import SpeakerManager

    data_handler = DataHandler()
    return SpeakerManager(data_handler)


def presentation_controller_instance(sections: list[Section], window_size: int):
    from moves_cli.core.presentation_controller import PresentationController

    controller = PresentationController(
        sections=sections,
        window_size=window_size,
    )
    return controller


def settings_editor_instance():
    from moves_cli.core.settings_editor import SettingsEditor

    data_handler = DataHandler()
    return SettingsEditor(data_handler)


def version_callback(value: bool):
    """Get version from package metadata and display it"""
    if value:
        try:
            import importlib.metadata

            version = importlib.metadata.version("moves-cli")
            typer.echo(f"moves-cli version {version}")
        except Exception:
            typer.echo("Error retrieving version")
        raise typer.Exit()


# Initialize Typer CLI application
app = typer.Typer(
    help="moves CLI - Presentation control, reimagined.",
    add_completion=False,
)

# Subcommands for speaker, presentation, and settings management
speaker_app = typer.Typer(help="Manage speaker profiles, files, and processing")
presentation_app = typer.Typer(help="Live presentation control with voice navigation")
settings_app = typer.Typer(help="Configure system settings (model, API key)")


@speaker_app.command("add")
def speaker_add(
    name: str = typer.Argument(..., help="Speaker's name"),
    source_presentation: Path = typer.Argument(..., help="Path to presentation file"),
    source_transcript: Path = typer.Argument(..., help="Path to transcript file"),
):
    """Create a new speaker profile with presentation and transcript files"""
    # Validate file paths exist
    if not source_presentation.exists() or not source_transcript.exists():
        typer.echo(f"Could not add speaker '{name}'.", err=True)
        if not source_presentation.exists():
            typer.echo(
                f"    Presentation file not found: {source_presentation}", err=True
            )
        if not source_transcript.exists():
            typer.echo(f"    Transcript file not found: {source_transcript}", err=True)
        raise typer.Exit(1)

    try:
        # Add speaker
        speaker_manager = speaker_manager_instance()
        speaker = speaker_manager.add(name, source_presentation, source_transcript)

        # Display success message
        typer.echo(f"Speaker {speaker.label} has been successfully added.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Could not add speaker '{name}'.", err=True)
        typer.echo(f"    {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("edit")
def speaker_edit(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
    source_presentation: Optional[str] = typer.Option(
        None, "--presentation", "-p", help="New presentation file path"
    ),
    source_transcript: Optional[str] = typer.Option(
        None, "--transcript", "-t", help="New transcript file path"
    ),
):
    """Update speaker's presentation and/or transcript files"""
    # Validate at least one parameter is provided
    if not source_presentation and not source_transcript:
        typer.echo(
            "Error: At least one update parameter (--presentation or --transcript) must be provided",
            err=True,
        )
        raise typer.Exit(1)

    try:
        # Resolve speaker
        speaker_manager = speaker_manager_instance()
        resolved_speaker = speaker_manager.resolve(speaker)

        # Validate and convert paths
        presentation_path = Path(source_presentation) if source_presentation else None
        transcript_path = Path(source_transcript) if source_transcript else None

        if presentation_path and not presentation_path.exists():
            typer.echo(
                f"Could not update speaker {resolved_speaker.label}.",
                err=True,
            )
            typer.echo(
                f"    Presentation file not found: {presentation_path}", err=True
            )
            raise typer.Exit(1)

        if transcript_path and not transcript_path.exists():
            typer.echo(
                f"Could not update speaker {resolved_speaker.label}.",
                err=True,
            )
            typer.echo(f"    Transcript file not found: {transcript_path}", err=True)
            raise typer.Exit(1)

        # Update speaker
        updated_speaker = speaker_manager.edit(
            resolved_speaker, presentation_path, transcript_path
        )

        # Display updated speaker information
        updates = {}
        if presentation_path:
            updates["New presentation source"] = updated_speaker.source_presentation
        if transcript_path:
            updates["New transcript source"] = updated_speaker.source_transcript
        typer.echo(
            output(
                f"Speaker {updated_speaker.label} has been successfully edited.",
                updates,
            )
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("list")
def speaker_list():
    """List all registered speakers with their status"""
    try:
        data_handler = DataHandler()
        # Get all speakers
        speaker_manager = speaker_manager_instance()
        speakers = speaker_manager.list()

        if not speakers:
            typer.echo("No speakers are registered.")
            return

        # Build table rows
        rows: list[dict[str, str]] = []
        for speaker in speakers:
            speaker_path = data_handler.DATA_FOLDER / "speakers" / speaker.speaker_id
            sections_file = speaker_path / "sections.yaml"
            ready_status = "Ready" if sections_file.exists() else "Not Ready"

            last_processed_str = "N/A"
            if speaker.last_processed:
                try:
                    dt = datetime.fromisoformat(speaker.last_processed)
                    last_processed_str = dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    last_processed_str = "Invalid Date"

            rows.append(
                {
                    "NAME": speaker.name,
                    "ID": speaker.speaker_id,
                    "STATUS": ready_status,
                    "LAST PROCESSED": last_processed_str,
                }
            )

        typer.echo(output(f"There are {len(speakers)} registered speaker(s).", rows))

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error accessing speaker data: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("show")
def speaker_show(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
):
    """Show detailed information about a speaker"""
    try:
        data_handler = DataHandler()
        # Resolve speaker
        speaker_manager = speaker_manager_instance()
        resolved_speaker = speaker_manager.resolve(speaker)

        speaker_path = (
            data_handler.DATA_FOLDER / "speakers" / resolved_speaker.speaker_id
        )
        sections_file = speaker_path / "sections.yaml"
        status = "Ready" if sections_file.exists() else "Not Ready"

        # Display speaker details
        last_processed_str = "N/A"
        if resolved_speaker.last_processed:
            try:
                dt = datetime.fromisoformat(resolved_speaker.last_processed)
                last_processed_str = dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                last_processed_str = "Invalid Date"

        typer.echo(
            output(
                f"Showing details for {resolved_speaker.label}",
                {
                    "Name": resolved_speaker.name,
                    "ID": resolved_speaker.speaker_id,
                    "Status": status,
                    "Last Processed": last_processed_str,
                    "Presentation": resolved_speaker.source_presentation,
                    "Transcript": resolved_speaker.source_transcript,
                },
            )
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("process")
def speaker_process(
    speakers: Optional[list[str]] = typer.Argument(None, help="Speaker(s) to process"),
    all: bool = typer.Option(False, "--all", "-a", help="Process all speakers"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Process the speaker to get ready for the control (requires LLM model and API key)"""
    try:
        # Get instances
        speaker_manager = speaker_manager_instance()
        settings_editor = settings_editor_instance()

        # Get LLM configuration
        settings = settings_editor.list()

        # Validate LLM settings
        if not settings.model:
            typer.echo(
                "Error: LLM model not configured. Use 'moves settings set model <model>' to configure.",
                err=True,
            )
            raise typer.Exit(1)

        if not settings.key:
            typer.echo(
                "Error: LLM API key not configured. Use 'moves settings set key <key>' to configure.",
                err=True,
            )
            raise typer.Exit(1)

        # Resolve speakers
        if all:
            # Get all speakers
            resolved_speakers = speaker_manager.list()
            if not resolved_speakers:
                typer.echo("No speakers found to process.")
                return
        elif speakers:
            # Resolve each speaker from the list
            resolved_speakers = []

            for pattern in speakers:
                resolved = speaker_manager.resolve(pattern)
                resolved_speakers.append(resolved)
        else:
            typer.echo(
                "Error: Either provide speaker names or use --all to process all speakers.",
                err=True,
            )
            raise typer.Exit(1)

        # Call speaker_manager.process with resolved speakers
        results = asyncio.run(
            speaker_manager.process(
                resolved_speakers, settings.model, settings.key, skip_confirmation=yes
            )
        )

        # Display results in Direct Summary format
        if len(resolved_speakers) == 1:
            result = results[0]
            speaker = resolved_speakers[0]
            typer.echo(f"Speaker {speaker.label} processed.")
            typer.echo()
            typer.echo(
                f"{result.section_count} sections have been created in {result.processing_time_seconds:.1f} seconds."
            )
        else:
            typer.echo(f"{len(resolved_speakers)} speakers processed.")

            # Display detailed results for all speakers
            total_time = sum(result.processing_time_seconds for result in results)
            results_dict = {}
            for i, result in enumerate(results):
                speaker = resolved_speakers[i]
                results_dict[speaker.label] = (
                    f"{result.section_count} sections ({result.processing_time_seconds:.1f}s)"
                )

            typer.echo(output(None, results_dict))

            typer.echo()
            typer.echo(f"Processing time took {total_time:.1f} seconds in total.")

    except typer.Exit:
        raise
    except typer.Abort:
        typer.echo("Aborted.")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"Processing error: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("delete")
def speaker_delete(
    speakers: Optional[list[str]] = typer.Argument(None, help="Speaker(s) to delete"),
    all: bool = typer.Option(False, "--all", "-a", help="Delete all speakers"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
):
    """Delete speaker(s) and their data"""
    try:
        # Get speaker manager instance
        speaker_manager = speaker_manager_instance()

        # Resolve speakers
        if all:
            # Get all speakers
            resolved_speakers = speaker_manager.list()
            if not resolved_speakers:
                typer.echo("No speakers found to delete.")
                return
        elif speakers:
            # Resolve each speaker from the list
            resolved_speakers = []

            for pattern in speakers:
                resolved = speaker_manager.resolve(pattern)
                resolved_speakers.append(resolved)
        else:
            typer.echo(
                "Error: Either provide speaker names or use --all to delete all speakers.",
                err=True,
            )
            raise typer.Exit(1)

        # Display deletion plan
        typer.echo(
            f"Are you sure you want to delete the following {len(resolved_speakers)} speaker(s)?"
        )
        for speaker in resolved_speakers:
            typer.echo(f"  {speaker.speaker_id}")
        typer.echo()

        if not yes:
            typer.confirm("Proceed?", default=True, abort=True)
            typer.echo("Yes")
            typer.echo()

        # Delete speakers using for loop and display results immediately
        deleted_count = 0
        failed_count = 0

        for speaker in resolved_speakers:
            success = speaker_manager.delete(speaker)
            if success:
                if yes:
                    typer.echo(f"Speaker {speaker.label} deleted.")
                deleted_count += 1
            else:
                typer.echo(f"Could not delete speaker '{speaker.name}'.", err=True)
                typer.echo("    Failed to delete speaker data.", err=True)
                failed_count += 1

        if not yes and deleted_count > 0:
            typer.echo("Speaker(s) deleted.")

        # Exit with error if any deletions failed
        if failed_count > 0:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except typer.Abort:
        typer.echo("Aborted.")
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@presentation_app.command("control")
def presentation_control(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
):
    """Start live voice-controlled presentation navigation (requires processed speaker)"""
    try:
        from rich.progress import Progress, SpinnerColumn, TextColumn

        # Get speaker manager
        speaker_manager = speaker_manager_instance()
        data_handler = DataHandler()

        # Resolve speaker
        resolved_speaker = speaker_manager.resolve(speaker)

        # Check for processed sections data
        speaker_path = (
            data_handler.DATA_FOLDER / "speakers" / resolved_speaker.speaker_id
        )
        sections_file = speaker_path / "sections.yaml"

        if not sections_file.exists():
            typer.echo(
                f"Error: Speaker {resolved_speaker.label} has not been processed yet.",
                err=True,
            )
            typer.echo(
                f"Please run 'moves speaker process {resolved_speaker.speaker_id}' first to generate sections.",
                err=True,
            )
            raise typer.Exit(1)

        # Load sections data from YAML
        from moves_cli.core.components.section_producer import SectionProducer

        sec_producer = SectionProducer()
        sections = sec_producer.load_from_yaml(data_handler.read(sections_file))

        if not sections:
            typer.echo("Error: No sections found in processed data.", err=True)
            raise typer.Exit(1)

        window_size = WINDOW_SIZE

        # Initialize controller with loading spinner
        with Progress(
            SpinnerColumn(style=""),
            TextColumn("{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description="Starting control session...", total=None)
            controller = presentation_controller_instance(
                sections, window_size=window_size
            )

        typer.echo(f"Live control session started for {resolved_speaker.label}.")
        typer.echo("  [←/→] Previous/Next | [Ins] Pause/Resume | [Ctrl+C] Exit\n")

        controller.control()

        typer.echo("\nControl session ended.\n")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Presentation control error: {str(e)}", err=True)
        raise typer.Exit(1)


@settings_app.command("list")
def settings_list(
    show: bool = typer.Option(False, "--show", "-s", help="Reveal full API key"),
):
    """Display current system configuration (model, API key status)"""
    try:
        # Create settings editor instance
        settings_editor = settings_editor_instance()
        settings = settings_editor.list()

        # Display settings
        model_value = settings.model if settings.model else "Not configured"

        if settings.key:
            display_key = settings.key
            if not show:
                if len(settings.key) > 8:
                    display_key = f"{settings.key[:4]}{'*' * (len(settings.key) - 8)}{settings.key[-4:]}"
                else:
                    display_key = "*" * len(settings.key)
        else:
            display_key = "Not configured"

        typer.echo(
            output(
                f"moves settings (see: {settings_editor.data_handler.DATA_FOLDER / 'settings.toml'})",
                {"model (LLM Model)": model_value, "key (API Key)": display_key},
            )
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error accessing settings: {str(e)}", err=True)
        raise typer.Exit(1)


@settings_app.command("set")
def settings_set(
    key: str = typer.Argument(..., help="Setting name to update"),
    value: str = typer.Argument(..., help="New setting value"),
):
    """Configure system settings: model (LLM model name) or key (API key)"""
    try:
        # Create settings editor instance
        settings_editor = settings_editor_instance()

        # Valid setting keys
        valid_keys = ["model", "key"]

        if key not in valid_keys:
            typer.echo(f"Error: Invalid setting key '{key}'", err=True)
            typer.echo(f"Valid keys: {', '.join(valid_keys)}", err=True)
            raise typer.Exit(1)

        # Update setting
        success = settings_editor.set(key, value)

        if success:
            typer.echo(output(f"Setting '{key}' updated.", {"New Value": value}))
        else:
            typer.echo(f"Could not update setting '{key}'.", err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Unexpected error: {str(e)}", err=True)
        raise typer.Exit(1)


@settings_app.command(
    "unset",
    help=f"Reset a setting to its default value (model: {DEFAULT_LLM_MODEL}, key: {DEFAULT_API_KEY})",
)
def settings_unset(
    key: str = typer.Argument(..., help="Setting name to reset"),
):
    try:
        # Create settings editor instance
        settings_editor = settings_editor_instance()

        # Check if key exists in template
        valid_keys = ["model", "key"]
        if key not in valid_keys:
            typer.echo(f"Error: Invalid setting key '{key}'", err=True)
            typer.echo(f"Valid keys: {', '.join(valid_keys)}", err=True)
            raise typer.Exit(1)

        # Get the template value to show what it will be reset to
        template_value = settings_editor._template_defaults.get(key)

        # Reset setting
        success = settings_editor.unset(key)

        if success:
            # Display confirmation
            if key in settings_editor._template_defaults:
                display_value = (
                    "Not configured" if template_value is None else str(template_value)
                )
            else:
                display_value = "Not configured"
            typer.echo(
                output(
                    f"Setting '{key}' reset to default.", {"New Value": display_value}
                )
            )
        else:
            typer.echo(f"Could not reset setting '{key}'.", err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Unexpected error: {str(e)}", err=True)
        raise typer.Exit(1)


# Register subcommands
app.add_typer(speaker_app, name="speaker")
app.add_typer(presentation_app, name="presentation")
app.add_typer(settings_app, name="settings")


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, help="Show version and exit"
    ),
):
    """moves CLI - Presentation control, reimagined."""
    pass


if __name__ == "__main__":
    app()
