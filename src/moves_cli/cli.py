import asyncio
import getpass
from typing import Optional

import typer

from moves_cli.config import DEFAULT_API_KEY, DEFAULT_LLM_MODEL, WINDOW_SIZE
from moves_cli.models import Section
from moves_cli.utils.data_handler import DataHandler
from moves_cli.utils.formatters import format_datetime, output


def _safe_echo(message: str | None = None, err: bool = False) -> None:
    """Echo a message safely, handling Windows console errors."""
    try:
        typer.echo(message, err=err)
    except OSError:
        pass


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
            typer.echo(output(f"moves-cli version {version}"))
        except Exception:
            typer.echo(output("Error retrieving version"))
        raise typer.Exit()


# Initialize Typer CLI application
app = typer.Typer(
    help="moves CLI - Presentation control, reimagined.",
    add_completion=False,
)

# Subcommands for speaker and settings management
speaker_app = typer.Typer(help="Manage speaker profiles, files, and processing")
settings_app = typer.Typer(help="Configure system settings (model, API key)")


@speaker_app.command("add")
def speaker_add(
    name: str = typer.Argument(..., help="Speaker's name"),
    source_presentation: str = typer.Argument(
        ..., help="Path or Google URL to presentation file"
    ),
    source_transcript: str = typer.Argument(
        ..., help="Path or Google URL to transcript file"
    ),
):
    """Create a new speaker profile with presentation and transcript files"""
    from moves_cli.utils.google_handler import resolve_source_path

    try:
        # Resolve sources (download if URL, validate if local path)
        presentation_path = resolve_source_path(source_presentation)
        transcript_path = resolve_source_path(source_transcript)

        # Add speaker with original source strings
        speaker_manager = speaker_manager_instance()
        speaker = speaker_manager.add(
            name,
            presentation_path,
            transcript_path,
            source_presentation,
            source_transcript,
        )

        # Display success message
        speaker_dir = speaker_manager.SPEAKERS_PATH / speaker.speaker_id
        typer.echo(
            output(
                f"Speaker {speaker.label} has been successfully added.",
                {
                    "Data directory": speaker_dir,
                    "Presentation source": speaker.presentation_source_display,
                    "Transcript source": speaker.transcript_source_display,
                },
            )
        )

    except typer.Exit:
        raise
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        typer.echo(
            output(f"Could not add speaker '{name}'.", {"Error": str(e)}), err=True
        )
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(
            output(f"Could not add speaker '{name}'.", {"Error": str(e)}), err=True
        )
        raise typer.Exit(1)


@speaker_app.command("edit")
def speaker_edit(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
    source_presentation: Optional[str] = typer.Option(
        None, "--presentation", "-p", help="New presentation file path or Google URL"
    ),
    source_transcript: Optional[str] = typer.Option(
        None, "--transcript", "-t", help="New transcript file path or Google URL"
    ),
):
    """Update speaker's presentation and/or transcript files"""
    from moves_cli.utils.google_handler import resolve_source_path

    # Validate at least one parameter is provided
    if not source_presentation and not source_transcript:
        typer.echo(
            output(
                "Error: At least one update parameter (--presentation or --transcript) must be provided"
            ),
            err=True,
        )
        raise typer.Exit(1)

    try:
        # Resolve speaker
        speaker_manager = speaker_manager_instance()
        resolved_speaker = speaker_manager.resolve(speaker)

        # Resolve sources (download if URL, validate if local path)
        presentation_path = None
        transcript_path = None

        if source_presentation:
            presentation_path = resolve_source_path(source_presentation)
        if source_transcript:
            transcript_path = resolve_source_path(source_transcript)

        # Update speaker with original source strings
        updated_speaker = speaker_manager.edit(
            resolved_speaker,
            presentation_path,
            transcript_path,
            source_presentation,
            source_transcript,
        )

        # Display updated speaker information
        speaker_dir = speaker_manager.SPEAKERS_PATH / updated_speaker.speaker_id
        updates = {"Data directory": speaker_dir}
        if presentation_path:
            updates["New presentation source"] = updated_speaker.presentation_source_display
        if transcript_path:
            updates["New transcript source"] = updated_speaker.transcript_source_display
        typer.echo(
            output(
                f"Speaker {updated_speaker.label} has been successfully edited.",
                updates,
            )
        )

    except typer.Exit:
        raise
    except (ValueError, FileNotFoundError, RuntimeError) as e:
        typer.echo(output(f"Error: {str(e)}"), err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(output(f"Error: {str(e)}"), err=True)
        raise typer.Exit(1)


@speaker_app.command("list")
def speaker_list():
    """List all registered speakers with their status"""
    try:
        # Get all speakers
        speaker_manager = speaker_manager_instance()
        speakers = speaker_manager.list()

        if not speakers:
            speakers_dir = speaker_manager.SPEAKERS_PATH
            typer.echo(
                output(
                    "No speakers are registered.",
                    {"Data directory": speakers_dir},
                )
            )
            return

        # Build table rows
        rows: list[dict[str, str]] = []
        for speaker in speakers:
            ready_status = "Ready" if speaker.sections_file.exists() else "Not Ready"
            last_processed_str = format_datetime(speaker.last_processed)

            rows.append(
                {
                    "NAME": speaker.name,
                    "ID": speaker.speaker_id,
                    "STATUS": ready_status,
                    "LAST PROCESSED": last_processed_str,
                }
            )

        speakers_dir = speaker_manager.SPEAKERS_PATH
        typer.echo(
            output(
                f"There are {len(speakers)} registered speaker(s).",
                rows,
            )
        )
        typer.echo()
        typer.echo(output(f"Data directory: {speakers_dir}"))

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(output(f"Error accessing speaker data: {str(e)}"), err=True)
        raise typer.Exit(1)


@speaker_app.command("show")
def speaker_show(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
):
    """Show detailed information about a speaker"""
    try:
        # Resolve speaker
        speaker_manager = speaker_manager_instance()
        resolved_speaker = speaker_manager.resolve(speaker)

        status = "Ready" if resolved_speaker.sections_file.exists() else "Not Ready"
        last_processed_str = format_datetime(resolved_speaker.last_processed)
        speaker_dir = speaker_manager.SPEAKERS_PATH / resolved_speaker.speaker_id

        typer.echo(
            output(
                f"Showing details for {resolved_speaker.label}",
                {
                    "Name": resolved_speaker.name,
                    "ID": resolved_speaker.speaker_id,
                    "Status": status,
                    "Last Processed": last_processed_str,
                    "Data directory": speaker_dir,
                    "Sections file": resolved_speaker.sections_file,
                    "Presentation source": resolved_speaker.presentation_source_display,
                    "Transcript source": resolved_speaker.transcript_source_display,
                },
            )
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(output(f"Error: {str(e)}"), err=True)
        raise typer.Exit(1)


@speaker_app.command("prepare")
def speaker_prepare(
    speakers: Optional[list[str]] = typer.Argument(None, help="Speaker(s) to prepare"),
    all: bool = typer.Option(False, "--all", "-a", help="Prepare all speakers"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
    manual: bool = typer.Option(
        False,
        "--manual",
        "-m",
        help="Generate empty template without LLM (offline mode)",
    ),
):
    """Prepare the speaker for presentation control (use --manual for offline template generation)"""
    try:
        # Get instances
        speaker_manager = speaker_manager_instance()
        settings_editor = settings_editor_instance()

        # Get LLM configuration (only required in auto mode)
        settings = settings_editor.list()
        llm_model = None
        llm_api_key = None

        if not manual:
            # Validate LLM settings (auto mode only)
            if not settings.model:
                typer.echo(
                    output(
                        "Error: LLM model not configured. Use 'moves settings set model <model>' to configure."
                    ),
                    err=True,
                )
                typer.echo(
                    output(
                        "Tip: Use --manual flag to generate a template without LLM."
                    ),
                    err=True,
                )
                raise typer.Exit(1)

            if not settings.key:
                typer.echo(
                    output(
                        "Error: LLM API key not configured. Use 'moves settings set key' to configure."
                    ),
                    err=True,
                )
                typer.echo(
                    output(
                        "Tip: Use --manual flag to generate a template without LLM."
                    ),
                    err=True,
                )
                raise typer.Exit(1)

            llm_model = settings.model
            llm_api_key = settings.key

        # Resolve speakers
        if all:
            # Get all speakers
            resolved_speakers = speaker_manager.list()
            if not resolved_speakers:
                typer.echo(output("No speakers found to prepare."))
                return
        elif speakers:
            # Resolve each speaker from the list
            resolved_speakers = []

            for pattern in speakers:
                resolved = speaker_manager.resolve(pattern)
                resolved_speakers.append(resolved)
        else:
            typer.echo(
                output(
                    "Error: Either provide speaker names or use --all to prepare all speakers."
                ),
                err=True,
            )
            raise typer.Exit(1)

        # Call speaker_manager.process with resolved speakers
        results = asyncio.run(
            speaker_manager.process(
                resolved_speakers,
                llm_model=llm_model,
                llm_api_key=llm_api_key,
                skip_confirmation=yes,
                manual_mode=manual,
            )
        )

        # Display results
        if len(resolved_speakers) == 1:
            result = results[0]
            speaker = resolved_speakers[0]
            speaker_dir = speaker_manager.SPEAKERS_PATH / speaker.speaker_id

            if manual:
                typer.echo(
                    output(
                        f"Speaker {speaker.label} prepared.",
                        {
                            "Sections created": result.section_count,
                            "Sections file": speaker.sections_file,
                            "Data directory": speaker_dir,
                            "Next step": "Edit sections.md to add speech content for each slide",
                        },
                    )
                )
            else:
                typer.echo(
                    output(
                        f"Speaker {speaker.label} prepared.",
                        {
                            "Sections created": result.section_count,
                            "Processing time": f"{result.processing_time_seconds:.1f}s",
                            "Sections file": speaker.sections_file,
                            "Data directory": speaker_dir,
                        },
                    )
                )
        else:
            typer.echo(output(f"{len(resolved_speakers)} speakers prepared."))
            typer.echo()

            if manual:
                # Manual mode: show section counts and file paths
                manual_results = {}
                for i, result in enumerate(results):
                    speaker = resolved_speakers[i]
                    manual_results[speaker.label] = (
                        f"{result.section_count} empty sections → {speaker.sections_file}"
                    )

                typer.echo(output(manual_results))
                typer.echo()
                typer.echo(output("Edit sections.md files to add speech content."))
            else:
                # Auto mode: show section counts with timing
                total_time = sum(result.processing_time_seconds for result in results)
                results_dict = {}
                for i, result in enumerate(results):
                    speaker = resolved_speakers[i]
                    results_dict[speaker.label] = (
                        f"{result.section_count} sections ({result.processing_time_seconds:.1f}s)"
                    )

                typer.echo(output(results_dict))
                typer.echo()
                typer.echo(output(f"Total preparation time: {total_time:.1f} seconds."))

    except typer.Exit:
        raise
    except typer.Abort:
        typer.echo(output("Aborted."))
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(output(f"Preparation error: {str(e)}"), err=True)
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
                typer.echo(output("No speakers found to delete."))
                return
        elif speakers:
            # Resolve each speaker from the list
            resolved_speakers = []

            for pattern in speakers:
                resolved = speaker_manager.resolve(pattern)
                resolved_speakers.append(resolved)
        else:
            typer.echo(
                output(
                    "Error: Either provide speaker names or use --all to delete all speakers."
                ),
                err=True,
            )
            raise typer.Exit(1)

        # Display deletion plan
        speakers_to_delete = {s.speaker_id: s.name for s in resolved_speakers}
        typer.echo(
            output(
                f"Are you sure you want to delete the following {len(resolved_speakers)} speaker(s)?",
                speakers_to_delete,
            )
        )
        typer.echo()

        if not yes:
            typer.confirm("Proceed?", default=True, abort=True)
            typer.echo(output("Yes"))
            typer.echo()

        # Delete speakers using for loop and display results immediately
        deleted_count = 0
        failed_count = 0

        for speaker in resolved_speakers:
            try:
                speaker_dir = speaker_manager.SPEAKERS_PATH / speaker.speaker_id
                speaker_manager.delete(speaker)
                if yes:
                    typer.echo(
                        output(
                            f"Speaker {speaker.label} deleted.",
                            {"Data directory removed": speaker_dir},
                        )
                    )
                deleted_count += 1
            except Exception as e:
                typer.echo(
                    output(
                        f"Could not delete speaker '{speaker.name}'.",
                        {"Reason": str(e)},
                    ),
                    err=True,
                )
                failed_count += 1

        if not yes and deleted_count > 0:
            typer.echo(output("Speaker(s) deleted."))

        # Exit with error if any deletions failed
        if failed_count > 0:
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except typer.Abort:
        typer.echo(output("Aborted."))
        raise typer.Exit(0)
    except Exception as e:
        typer.echo(output(f"Error: {str(e)}"), err=True)
        raise typer.Exit(1)


@app.command("present")
def present(
    speaker: str = typer.Argument(..., help="Speaker name or ID"),
):
    """Start live voice-controlled presentation navigation (requires prepared speaker)"""
    try:
        # Get speaker manager
        speaker_manager = speaker_manager_instance()
        data_handler = DataHandler()

        # Resolve speaker
        resolved_speaker = speaker_manager.resolve(speaker)

        # Check for processed sections data
        if not resolved_speaker.sections_file.exists():
            typer.echo(
                output(
                    f"Error: Speaker {resolved_speaker.label} has not been prepared yet."
                ),
                err=True,
            )
            typer.echo(
                output(
                    f"Please run 'moves speaker prepare {resolved_speaker.speaker_id}' first to generate sections."
                ),
                err=True,
            )
            raise typer.Exit(1)

        # Validate source files exist (no silent fallback to stale data)
        missing_files = []
        if not resolved_speaker.source_presentation.exists():
            missing_files.append(
                f"Presentation: {resolved_speaker.source_presentation}"
            )
        if not resolved_speaker.source_transcript.exists():
            missing_files.append(f"Transcript: {resolved_speaker.source_transcript}")

        if missing_files:
            missing_dict = {}
            for f in missing_files:
                key, val = f.split(": ", 1)
                missing_dict[key] = val
            typer.echo(
                output(
                    f"Error: Missing source files for speaker {resolved_speaker.label}.",
                    missing_dict,
                    "Please update file paths with 'moves speaker edit' command.",
                ),
                err=True,
            )
            raise typer.Exit(1)

        # Check if source files have changed since last processing (hash comparison)
        from moves_cli.core.speaker_manager import SpeakerManager

        files_changed = []
        if resolved_speaker.presentation_hash:
            current_pres_hash = SpeakerManager.compute_file_hash(
                resolved_speaker.source_presentation
            )
            if current_pres_hash != resolved_speaker.presentation_hash:
                files_changed.append("Presentation")

        if resolved_speaker.transcript_hash:
            current_trans_hash = SpeakerManager.compute_file_hash(
                resolved_speaker.source_transcript
            )
            if current_trans_hash != resolved_speaker.transcript_hash:
                files_changed.append("Transcript")

        if files_changed:
            typer.echo(
                output(
                    "Warning: The following source files have changed since last processing.",
                    {f: "Changed" for f in files_changed},
                    "You may be using outdated section data.",
                    {
                        "Re-process": f"moves speaker prepare {resolved_speaker.speaker_id}"
                    },
                )
            )
            typer.echo()
            if not typer.confirm(
                "Do you want to continue with potentially outdated data?", default=False
            ):
                raise typer.Abort()
            typer.echo()

        # Check if sections.md has been manually modified since last process/control
        if resolved_speaker.sections_hash:
            current_sections_hash = SpeakerManager.compute_normalized_sections_hash(
                resolved_speaker.sections_file
            )
            if current_sections_hash != resolved_speaker.sections_hash:
                typer.echo(
                    output(
                        "Warning: sections.md has been modified since last processing.",
                        "This may be intentional (manual edits) or accidental.",
                    ),
                    err=True,
                )
                typer.echo()

                choice = typer.prompt(
                    "Continue? (Save as current, Yes, No)", default="N"
                ).lower()

                if choice == "n":
                    raise typer.Abort()
                elif choice == "s":
                    # Update sections hash in speaker metadata
                    resolved_speaker.sections_hash = current_sections_hash
                    speaker_manager._write_speaker_yaml(
                        resolved_speaker.speaker_file, resolved_speaker
                    )
                    typer.echo(output("Hash updated.\n"))
                elif choice == "y":
                    typer.echo()  # Just continue
                else:
                    typer.echo(output("Invalid choice. Aborting."), err=True)
                    raise typer.Abort()

        # Load sections data from YAML
        from moves_cli.core.components.section_producer import SectionProducer

        sec_producer = SectionProducer()
        sections = sec_producer.load_from_markdown(
            data_handler.read(resolved_speaker.sections_file)
        )

        if not sections:
            typer.echo(output("Error: No sections found in processed data."), err=True)
            raise typer.Exit(1)

        # Load models early (before section checks for faster feedback)
        window_size = WINDOW_SIZE
        controller = presentation_controller_instance(sections, window_size=window_size)

        # Check for empty sections (unfilled template from manual mode)
        empty_sections = [s for s in sections if not s.content.strip()]
        if empty_sections:
            _safe_echo(
                output(
                    f"Warning: {len(empty_sections)} of {len(sections)} sections have empty content."
                )
            )
            _safe_echo(output("These slides will not respond to voice navigation."))
            _safe_echo()
            if not typer.confirm("Continue anyway?", default=False):
                raise typer.Abort()
            _safe_echo()

        _safe_echo(
            output(
                f"Presentation started for {resolved_speaker.label}.",
                "[←/→] Previous/Next | [Ins] Pause/Resume | [Ctrl+C] Exit",
            )
        )

        controller.control()

        _safe_echo(output("\nPresentation ended.\n"))

    except typer.Exit:
        raise
    except Exception as e:
        _safe_echo(output(f"Presentation error: {str(e)}"), err=True)
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

        settings_file = settings_editor.data_handler.DATA_FOLDER / "settings.toml"
        typer.echo(
            output(
                "moves CLI Configuration",
                {
                    "Configuration file": settings_file,
                    "model (LLM Model)": model_value,
                    "key (API Key)": display_key,
                    "Note": "API keys are stored in Windows Credential Manager (keyring)",
                },
            )
        )

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(output(f"Error accessing settings: {str(e)}"), err=True)
        raise typer.Exit(1)


@settings_app.command("set")
def settings_set(
    key: str = typer.Argument(..., help="Setting name to update: 'model' or 'key'"),
    value: str | None = typer.Argument(None, help="Setting value (only for 'model')"),
):
    """Configure system settings: model (LLM model name) or key (API key)"""
    try:
        # Create settings editor instance
        settings_editor = settings_editor_instance()

        # Valid setting keys
        valid_keys = ["model", "key"]

        if key not in valid_keys:
            typer.echo(output(f"Error: Invalid setting key '{key}'"), err=True)
            typer.echo(output(f"Valid keys: {', '.join(valid_keys)}"), err=True)
            raise typer.Exit(1)

        # Handle API key with interactive masked input only
        if key == "key":
            if value is not None:
                typer.echo(
                    output(
                        "Error: API key cannot be passed as argument for security reasons."
                    ),
                    err=True,
                )
                typer.echo(
                    output(
                        "Usage: moves settings set key (interactive prompt will appear)"
                    ),
                    err=True,
                )
                raise typer.Exit(1)

            # Interactive masked input
            import sys

            typer.echo("Note: Your input will not be shown on screen.", err=True)
            value = getpass.getpass("Enter API key: ", stream=sys.stderr)
            if not value or not value.strip():
                typer.echo(output("Error: API key cannot be empty."), err=True)
                raise typer.Exit(1)
            value = value.strip()

        # Check if value is provided for model setting
        if key == "model" and value is None:
            typer.echo(
                output("Error: value argument is required for 'model' setting"),
                err=True,
            )
            typer.echo(output("Usage: moves settings set model <model-name>"), err=True)
            raise typer.Exit(1)

        # Update setting
        success = settings_editor.set(key, value)

        if success:
            if key == "key":
                display_value = (
                    f"{value[:4]}{'*' * (len(value) - 8)}{value[-4:]}"
                    if len(value) > 8
                    else ("*" * len(value))
                )
                storage_location = "Windows Credential Manager"
            else:
                display_value = value
                storage_location = str(
                    settings_editor.data_handler.DATA_FOLDER / "settings.toml"
                )

            typer.echo(
                output(
                    f"Setting '{key}' updated.",
                    {"New value": display_value, "Storage": storage_location},
                )
            )
        else:
            typer.echo(output(f"Could not update setting '{key}'."), err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(output(f"Unexpected error: {str(e)}"), err=True)
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
            typer.echo(output(f"Error: Invalid setting key '{key}'"), err=True)
            typer.echo(output(f"Valid keys: {', '.join(valid_keys)}"), err=True)
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

            storage_location = (
                "Windows Credential Manager"
                if key == "key"
                else (settings_editor.data_handler.DATA_FOLDER / "settings.toml")
            )
            typer.echo(
                output(
                    f"Setting '{key}' reset to default.",
                    {"New Value": display_value, "Removed from": storage_location},
                )
            )
        else:
            typer.echo(output(f"Could not reset setting '{key}'."), err=True)
            raise typer.Exit(1)

    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(output(f"Unexpected error: {str(e)}"), err=True)
        raise typer.Exit(1)


# Register subcommands
app.add_typer(speaker_app, name="speaker")
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
