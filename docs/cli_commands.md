# moves CLI Reference

The `moves` command-line interface is your primary tool for managing and controlling presentations. It offers a comprehensive suite of commands to handle everything from initial setup to live, voice-driven presentation delivery. This guide provides a detailed reference for all available commands, options, and common workflows.

## Get Started

Get up and running with `moves` in three simple steps.

### 1. Configure Your AI Model

First, configure the AI model and API key. `moves` relies on a Large Language Model (LLM) to analyze your presentation and transcript, so this step is essential for the core functionality.

> **Note:** Find compatible models at [LiteLLM Supported Models](https://models.litellm.ai/).

```bash
# Set the desired model
moves settings set model openai/gpt-4o-mini

# Set your API key
moves settings set key YOUR_API_KEY
```

### 2. Add and Process a Speaker

Next, add a speaker profile with their presentation and transcript. **Both files must be in PDF format.** `moves` will use these files to understand the content and structure of the presentation.

```bash
# Add a speaker with their presentation and transcript
moves speaker add "Speaker Name" ./presentation.pdf ./transcript.pdf

# Process the speaker's data for AI control
moves speaker process "Speaker Name"
```

Processing involves using the configured AI model to analyze the presentation and transcript, dividing them into logical sections that can be navigated during the live presentation.

### 3. Start the Presentation

With the speaker processed, you can now launch the live presentation control session.

```bash
moves presentation control "Speaker Name"
```

Once the session starts, focus the presentation window. `moves` will listen to your voice and automatically advance the slides as you speak, matching your words to the content of the presentation.

---

## Command Structure

All `moves` commands follow a consistent and predictable structure:

```
moves [GLOBAL_OPTIONS] <SUBCOMMAND> <ACTION> [ARGUMENTS] [OPTIONS]
```

**Subcommands:**

- **`speaker`**: Manage speaker profiles, files, and data processing.
- **`presentation`**: Control the live presentation flow.
- **`settings`**: Configure the application's AI model and API key.

**Global Options:**

- `--help`: Show help information for any command.
- `--version`: Display the application's version.

---

## `speaker` Subcommand

The `speaker` subcommand is used to manage speaker profiles, their associated files, and the AI processing required for live presentation control.

| Action    | Description                                     |
| :-------- | :---------------------------------------------- |
| `add`     | Creates a new speaker profile.                  |
| `edit`    | Updates the file paths for an existing speaker. |
| `list`    | Displays all registered speakers.               |
| `show`    | Shows detailed information for a speaker.       |
| `process` | Processes speaker data for AI navigation.       |
| `delete`  | Removes one or more speakers and their data.    |

### `add`

Creates a new speaker profile, linking a name to a presentation and transcript file.

**Usage:**

```bash
moves speaker add <NAME> <SOURCE_PRESENTATION> <SOURCE_TRANSCRIPT>
```

**Arguments:**

| Argument              | Description                                  |
| :-------------------- | :------------------------------------------- |
| `name`                | The speaker's name. **(Required)**           |
| `source_presentation` | Path to the presentation PDF. **(Required)** |
| `source_transcript`   | Path to the transcript PDF. **(Required)**   |

**Example:**

```bash
moves speaker add "John Doe" ./presentation.pdf ./transcript.pdf
```

### `edit`

Updates the presentation or transcript file path for an existing speaker.

**Usage:**

```bash
moves speaker edit <SPEAKER> [OPTIONS]
```

**Arguments:**

| Argument  | Description                                   |
| :-------- | :-------------------------------------------- |
| `speaker` | The name or ID of the speaker. **(Required)** |

**Options:**

| Option                 | Description                     |
| :--------------------- | :------------------------------ |
| `-p`, `--presentation` | The new presentation file path. |
| `-t`, `--transcript`   | The new transcript file path.   |

**Examples:**

```bash
# Update the presentation file
moves speaker edit "John Doe" --presentation ./new_presentation.pdf

# Update the transcript file
moves speaker edit "John Doe" --transcript ./new_transcript.pdf

# Update both files using short options
moves speaker edit "John Doe" -p ./new_slides.pdf -t ./new_speech.pdf
```

### `list`

Displays a list of all registered speakers and their processing status.

**Usage:**

```bash
moves speaker list
```

### `show`

Provides detailed information about a specific speaker, including their ID, file paths, and processing status.

**Usage:**

```bash
moves speaker show <SPEAKER>
```

**Arguments:**

| Argument  | Description                                   |
| :-------- | :-------------------------------------------- |
| `speaker` | The name or ID of the speaker. **(Required)** |

**Examples:**

```bash
# Show speaker details by name
moves speaker show "John Doe"

# Show speaker details by ID
moves speaker show speaker-123
```

### `process`

Processes a speaker's data using the configured AI model. This step is crucial for enabling live, voice-controlled navigation. The process involves analyzing the content of the presentation and transcript to create logical sections that `moves` can navigate between.

**Usage:**

```bash
moves speaker process [SPEAKERS]... [OPTIONS]
```

**Arguments:**

| Argument   | Description                                                |
| :--------- | :--------------------------------------------------------- |
| `speakers` | A space-separated list of speaker names or IDs to process. |

**Options:**

| Option        | Description           |
| :------------ | :-------------------- |
| `-a`, `--all` | Process all speakers. |

**Examples:**

```bash
# Process a specific speaker
moves speaker process "John Doe"

# Process multiple speakers
moves speaker process "John Doe" "Jane Smith"

# Process all speakers
moves speaker process --all
```

### `delete`

Removes one or more speakers and all their associated data from the system.

**Usage:**

```bash
moves speaker delete [SPEAKERS]... [OPTIONS]
```

**Arguments:**

| Argument   | Description                                               |
| :--------- | :-------------------------------------------------------- |
| `speakers` | A space-separated list of speaker names or IDs to delete. |

**Options:**

| Option        | Description          |
| :------------ | :------------------- |
| `-a`, `--all` | Delete all speakers. |

**Examples:**

```bash
# Delete a specific speaker
moves speaker delete "John Doe"

# Delete multiple speakers
moves speaker delete "John Doe" "Jane Smith"

# Delete all speakers
moves speaker delete --all
```

---

## `presentation` Subcommand

The `presentation` subcommand is used to control the live presentation, leveraging the processed speaker data for voice-activated navigation.

### `control`

Starts a live, voice-controlled presentation session. During the session, `moves` listens to the speaker's voice and automatically advances the slides based on the content of the speech.

**Usage:**

```bash
moves presentation control <SPEAKER>
```

**Arguments:**

| Argument  | Description                                   |
| :-------- | :-------------------------------------------- |
| `speaker` | The name or ID of the speaker. **(Required)** |

**Example:**

```bash
moves presentation control "John Doe"
```

**Session Controls:**

- **Voice**: Speak naturally to trigger automatic slide navigation.
- **→ (Right Arrow)**: Manually advance to the next section.
- **← (Left Arrow)**: Manually return to the previous section.
- **Ins (Insert)**: Pause or resume automatic voice navigation.
- **Ctrl+C**: Exit the control session.

---

## `settings` Subcommand

The `settings` subcommand is used to configure the LLM model and API key required for the AI-powered features of `moves`.

| Action  | Description                            |
| :------ | :------------------------------------- |
| `list`  | Displays the current settings.         |
| `set`   | Sets a new value for a setting.        |
| `unset` | Resets a setting to its default value. |

### `list`

Displays the current model and API key configuration.

**Usage:**

```bash
moves settings list
```

### `set`

Sets a new value for a specified setting.

**Usage:**

```bash
moves settings set <KEY> <VALUE>
```

**Arguments:**

| Argument | Description                                                |
| :------- | :--------------------------------------------------------- |
| `key`    | The name of the setting (`model` or `key`). **(Required)** |
| `value`  | The new value for the setting. **(Required)**              |

**Valid Keys:**

- `model`: The LLM model name (e.g., `openai/gpt-4o-mini`).
- `key`: The API key for the selected LLM service.

**Examples:**

```bash
# Set an OpenAI model
moves settings set model openai/gpt-4o-mini

# Set a Gemini model
moves settings set model gemini/gemini-2.0-flash

# Set the API key
moves settings set key YOUR_API_KEY_HERE
```

### `unset`

Resets a setting to its default value or clears it entirely.

**Usage:**

```bash
moves settings unset <KEY>
```

**Arguments:**

| Argument | Description                                                         |
| :------- | :------------------------------------------------------------------ |
| `key`    | The name of the setting to reset (`model` or `key`). **(Required)** |

**Examples:**

```bash
# Reset the model to its default
moves settings unset model

# Clear the stored API key
moves settings unset key
```

---

## Common Workflows

### Complete Workflow from Scratch

This workflow demonstrates the end-to-end process of setting up and running a presentation with `moves`.

```bash
# 1. Configure your model and API key
moves settings set model openai/gpt-4o-mini
moves settings set key sk-your-api-key-here

# 2. Add a new speaker profile
moves speaker add "Conference Speaker" ./keynote.pdf ./speech_notes.pdf

# 3. Process the speaker's data for AI control
moves speaker process "Conference Speaker"

# 4. Start the presentation
moves presentation control "Conference Speaker"
```

### Managing Multiple Speakers

This workflow shows how to manage multiple speakers within the `moves` system.

```bash
# Add multiple speakers
moves speaker add "Speaker A" ./presentation_A.pdf ./transcript_A.pdf
moves speaker add "Speaker B" ./presentation_B.pdf ./transcript_B.pdf

# List all speakers to verify they were added
moves speaker list

# Process all speakers at once
moves speaker process --all

# Show details for a specific speaker
moves speaker show "Speaker A"
```

### Troubleshooting

If you encounter issues, these commands can help you diagnose the problem.

```bash
# Check your current model and key configuration
moves settings list

# Verify a speaker's status and file paths
moves speaker show "Your Speaker Name"

# Re-process the speaker if data seems out of sync
moves speaker process "Your Speaker Name"
```