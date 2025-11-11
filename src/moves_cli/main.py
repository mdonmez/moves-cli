from typing import Optional
import typer
from pathlib import Path
from moves_cli.data.models import Section
from moves_cli.utils import data_handler


def speaker_manager_instance():
    from moves_cli.core.speaker_manager import SpeakerManager

    return SpeakerManager()


def presentation_controller_instance(sections: list[Section], window_size: int):
    from moves_cli.core.presentation_controller import PresentationController

    controller = PresentationController(
        sections=sections,
        window_size=window_size,
    )
    return controller


def settings_editor_instance():
    from moves_cli.core.settings_editor import SettingsEditor

    return SettingsEditor()


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
        typer.echo(f"Speaker '{speaker.name}' ({speaker.speaker_id}) added.")
        typer.echo(f"    ID -> {speaker.speaker_id}")
        typer.echo(f"    Presentation -> {speaker.source_presentation}")
        typer.echo(f"    Transcript -> {speaker.source_transcript}")

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
    """Update speaker's source files (presentation or transcript paths)"""
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
                f"Could not update speaker '{resolved_speaker.name}' ({resolved_speaker.speaker_id}).",
                err=True,
            )
            typer.echo(
                f"    Presentation file not found: {presentation_path}", err=True
            )
            raise typer.Exit(1)

        if transcript_path and not transcript_path.exists():
            typer.echo(
                f"Could not update speaker '{resolved_speaker.name}' ({resolved_speaker.speaker_id}).",
                err=True,
            )
            typer.echo(f"    Transcript file not found: {transcript_path}", err=True)
            raise typer.Exit(1)

        # Update speaker
        updated_speaker = speaker_manager.edit(
            resolved_speaker, presentation_path, transcript_path
        )

        # Display updated speaker information
        typer.echo(f"Speaker '{updated_speaker.name}' updated.")
        if presentation_path:
            typer.echo(f"    Presentation -> {updated_speaker.source_presentation}")
        if transcript_path:
            typer.echo(f"    Transcript -> {updated_speaker.source_transcript}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("list")
def speaker_list():
    """List all registered speakers with ready status"""
    try:
        # Get all speakers
        speaker_manager = speaker_manager_instance()
        speakers = speaker_manager.list()

        if not speakers:
            typer.echo("No speakers are registered.")
            return

        id_width = max(max(len(s.speaker_id) for s in speakers), len("ID"))
        name_width = max(max(len(s.name) for s in speakers), len("NAME"))
        status_width = max(len("Not Ready"), len("STATUS"))

        typer.echo(f"Registered Speakers ({len(speakers)})")
        typer.echo()
        typer.echo(f"{'ID':<{id_width}} {'NAME':<{name_width}} STATUS")
        typer.echo(f"{'─' * id_width} {'─' * name_width} {'─' * status_width}")

        # Add speaker rows
        for speaker in speakers:
            speaker_path = data_handler.DATA_FOLDER / "speakers" / speaker.speaker_id
            sections_file = speaker_path / "sections.json"
            ready_status = "Ready" if sections_file.exists() else "Not Ready"

            # Format with dynamic spacing to align columns
            typer.echo(
                f"{speaker.speaker_id:<{id_width}} {speaker.name:<{name_width}} {ready_status}"
            )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error accessing speaker data: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("show")
def speaker_show(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
):
    """Display detailed speaker information"""
    try:
        # Resolve speaker
        speaker_manager = speaker_manager_instance()
        resolved_speaker = speaker_manager.resolve(speaker)

        speaker_path = (
            data_handler.DATA_FOLDER / "speakers" / resolved_speaker.speaker_id
        )
        sections_file = speaker_path / "sections.json"
        status = "Ready" if sections_file.exists() else "Not Ready"

        # Display speaker details
        typer.echo(
            f"Showing details for speaker '{resolved_speaker.name}' ({resolved_speaker.speaker_id})"
        )
        typer.echo(f"    ID -> {resolved_speaker.speaker_id}")
        typer.echo(f"    Name -> {resolved_speaker.name}")
        typer.echo(f"    Status -> {status}")
        typer.echo(f"    Presentation -> {resolved_speaker.source_presentation}")
        typer.echo(f"    Transcript -> {resolved_speaker.source_transcript}")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("process")
def speaker_process(
    speakers: Optional[list[str]] = typer.Argument(None, help="Speaker(s) to process"),
    all: bool = typer.Option(False, "--all", "-a", help="Process all speakers"),
):
    """Generate presentation sections using AI for live control (requires model and API key)"""
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
            speaker_list = speaker_manager.list()
            if not speaker_list:
                typer.echo("No speakers found to process.")
                return
        elif speakers:
            # Resolve each speaker from the list
            speaker_list = []

            for speaker_name in speakers:
                resolved = speaker_manager.resolve(speaker_name)
                speaker_list.append(resolved)
        else:
            typer.echo(
                "Error: Either provide speaker names or use --all to process all speakers.",
                err=True,
            )
            raise typer.Exit(1)

        # Display processing message
        if len(speaker_list) == 1:
            typer.echo(
                f"Processing speaker '{speaker_list[0].name}' ({speaker_list[0].speaker_id})..."
            )
        else:
            typer.echo(f"Processing {len(speaker_list)} speakers...")

        # Call speaker_manager.process with resolved speakers
        results = speaker_manager.process(speaker_list, settings.model, settings.key)

        # Display results in Direct Summary format
        if len(speaker_list) == 1:
            result = results[0]
            speaker = speaker_list[0]
            typer.echo(f"Speaker '{speaker.name}' ({speaker.speaker_id}) processed.")
            typer.echo(
                f"{result.section_count} sections have been created and will be split into {result.chunk_count} chunks for control."
            )
            typer.echo(
                f"The processing time took {result.processing_time_seconds:.1f} seconds."
            )
        else:
            typer.echo(f"{len(speaker_list)} speakers processed.")

            # Display detailed results for all speakers
            total_time = sum(result.processing_time_seconds for result in results)
            for i, result in enumerate(results):
                speaker = speaker_list[i]
                typer.echo(
                    f"'{speaker.name}' ({speaker.speaker_id}) -> {result.section_count} sections & {result.chunk_count} chunks ({result.processing_time_seconds:.1f}s)"
                )

            typer.echo(f"The processing time took {total_time:.1f} seconds for total.")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Processing error: {str(e)}", err=True)
        raise typer.Exit(1)


@speaker_app.command("delete")
def speaker_delete(
    speakers: Optional[list[str]] = typer.Argument(None, help="Speaker(s) to delete"),
    all: bool = typer.Option(False, "--all", "-a", help="Delete all speakers"),
):
    """Remove speakers and their data"""
    try:
        # Get speaker manager instance
        speaker_manager = speaker_manager_instance()

        # Resolve speakers
        if all:
            # Get all speakers
            speaker_list = speaker_manager.list()
            if not speaker_list:
                typer.echo("No speakers found to delete.")
                return
        elif speakers:
            # Resolve each speaker from the list
            speaker_list = []

            for speaker_name in speakers:
                resolved = speaker_manager.resolve(speaker_name)
                speaker_list.append(resolved)
        else:
            typer.echo(
                "Error: Either provide speaker names or use --all to delete all speakers.",
                err=True,
            )
            raise typer.Exit(1)

        # Display deletion message
        typer.echo(f"Deleting {len(speaker_list)} speaker(s)...\n")

        # Delete speakers using for loop and display results immediately
        deleted_count = 0
        failed_count = 0

        for speaker in speaker_list:
            success = speaker_manager.delete(speaker)
            if success:
                typer.echo(f"Speaker '{speaker.name}' ({speaker.speaker_id}) deleted.")
                deleted_count += 1
            else:
                typer.echo(f"Could not delete speaker '{speaker.name}'.", err=True)
                typer.echo("    Failed to delete speaker data.", err=True)
                failed_count += 1

        # Exit with error if any deletions failed
        if failed_count > 0:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {str(e)}", err=True)
        raise typer.Exit(1)


@presentation_app.command("control")
def presentation_control(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
):
    """Start live voice-controlled presentation navigation (requires processed speaker)"""
    try:
        typer.echo("Starting control session...")
        import json
        from moves_cli.core.components import section_producer

        # Get speaker manager
        speaker_manager = speaker_manager_instance()

        # Resolve speaker
        resolved_speaker = speaker_manager.resolve(speaker)

        # Check for processed sections data
        speaker_path = (
            data_handler.DATA_FOLDER / "speakers" / resolved_speaker.speaker_id
        )
        sections_file = speaker_path / "sections.json"

        if not sections_file.exists():
            typer.echo(
                f"Error: Speaker '{resolved_speaker.name}' ({resolved_speaker.speaker_id}) has not been processed yet.",
                err=True,
            )
            typer.echo(
                f"Please run 'moves speaker process {resolved_speaker.speaker_id}' first to generate sections.",
                err=True,
            )
            raise typer.Exit(1)

        # Load sections data
        sections_data = json.loads(data_handler.read(sections_file))
        sections = section_producer.convert_to_objects(sections_data)

        if not sections:
            typer.echo("Error: No sections found in processed data.", err=True)
            raise typer.Exit(1)

        window_size = 12

        controller = presentation_controller_instance(sections, window_size=window_size)

        typer.echo(
            f"\nPresentation control started for '{resolved_speaker.name}' ({resolved_speaker.speaker_id})."
        )
        typer.echo("    [←/→] Previous/Next | [Ins] Pause/Resume | [Ctrl+C] Exit\n")

        controller.control()

        typer.echo("\nControl session ended.\n")

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Presentation control error: {str(e)}", err=True)
        raise typer.Exit(1)


@settings_app.command("list")
def settings_list():
    """Display current system configuration (model, API key status)"""
    try:
        # Create settings editor instance
        settings_editor = settings_editor_instance()
        settings = settings_editor.list()

        # Display settings in Direct Summary format
        typer.echo("Application Settings.")

        # Display model setting
        model_value = settings.model if settings.model else "Not configured"
        typer.echo(f"    model (LLM Model) -> {model_value}")

        # Display API key setting
        if settings.key:
            typer.echo(f"    key (API Key) -> {settings.key}")
        else:
            typer.echo("    key (API Key) -> Not configured")

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
            typer.echo(f"Setting '{key}' updated.")
            typer.echo(f"    New Value -> {value}")
        else:
            typer.echo(f"Could not update setting '{key}'.", err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Unexpected error: {str(e)}", err=True)
        raise typer.Exit(1)


@settings_app.command("unset")
def settings_unset(
    key: str = typer.Argument(..., help="Setting name to reset"),
):
    """Reset a setting to its default value (model: gemini/gemini-2.0-flash, key: null)"""
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
            # Display confirmation in Direct Summary format
            if key in settings_editor._template_defaults:
                display_value = (
                    "Not configured" if template_value is None else str(template_value)
                )
                typer.echo(f"Setting '{key}' reset to default.")
                typer.echo(f"    New Value -> {display_value}")
            else:
                # Key was removed (not in template)
                typer.echo(f"Setting '{key}' reset to default.")
                typer.echo("    New Value -> Not configured")
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
