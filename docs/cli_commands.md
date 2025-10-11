# moves CLI Reference

The `moves` command-line interface provides a comprehensive toolset for managing and controlling your presentations directly from the terminal. This guide details all commands, options, and common workflows.

## Get Started

Get up and running with `moves` in three steps.

### 1. Configure Your AI Model

First, configure the AI model and API key.

> **Note:** Find compatible models at [LiteLLM Supported Models](https://models.litellm.ai/).

```bash
# Set the desired model
moves settings set model openai/gpt-4o-mini

# Set your API key
moves settings set key YOUR_API_KEY
```

### 2. Add and Process a Speaker

Next, add a speaker profile using their presentation and transcript files. Both files must be in PDF format.

```bash
# Add a speaker with their presentation and transcript
moves speaker add "Speaker Name" ./presentation.pdf ./transcript.pdf

# Process the speaker's data for AI control
moves speaker process "Speaker Name"
```

### 3. Start the Presentation

Finally, launch the presentation control session.

```bash
moves presentation control "Speaker Name"
```

Focus the presentation window, and `moves` will handle the slide transitions as you speak.

---

## Command Structure

All `moves` commands follow a consistent structure:

```
moves [GLOBAL_OPTIONS] <SUBCOMMAND> <ACTION> [ARGUMENTS] [OPTIONS]
```

**Subcommands:**

- **`speaker`**: Manage speaker profiles, files, and data processing.
- **`presentation`**: Control the live presentation flow.
- **`settings`**: Configure the application's AI model and API key.

**Global Options:**

- `--help`: Show help information for a command.
- `--version`: Display the application's version.

---

## `speaker` Subcommand

Manages speaker profiles, their associated files, and AI processing.

| Action    | Description                                     |
| :-------- | :---------------------------------------------- |
| `add`     | Creates a new speaker profile.                  |
| `edit`    | Updates the file paths for an existing speaker. |
| `list`    | Displays all registered speakers.               |
| `show`    | Shows detailed information for a speaker.       |
| `process` | Processes speaker data for AI navigation.       |
| `delete`  | Removes one or more speakers and their data.    |

### `add`

Creates a new speaker profile.

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

Updates the presentation or transcript file path for a speaker.

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

Displays all registered speakers.

**Usage:**

```bash
moves speaker list
```

### `show`

Provides detailed information about a specific speaker.

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

Processes speaker data using the configured AI model for live control.

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

Removes one or more speakers and their associated data.

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

Controls the live presentation using voice-activated navigation.

### `control`

Starts a live, voice-controlled presentation session.

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

Configures the LLM model and API key.

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

Resets a setting to its default value or clears it.

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

```bash
# Add multiple speakers
moves speaker add "Speaker A" ./presentation_A.pdf ./transcript_A.pdf
moves speaker add "Speaker B" ./presentation_B.pdf ./transcript_B.pdf

# List all speakers to verify
moves speaker list

# Process all speakers at once
moves speaker process --all

# Show details for a specific speaker
moves speaker show "Speaker A"
```

### Troubleshooting

```bash
# Check your current model and key configuration
moves settings list

# Verify a speaker's status and file paths
moves speaker show "Your Speaker Name"

# Re-process the speaker if data seems out of sync
moves speaker process "Your Speaker Name"
```
