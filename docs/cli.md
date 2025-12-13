### moves

Displays help information for the `moves` command-line tool. When run with the `--version` option, it displays the application's version number.

#### `moves --version`

Displays the current installed version of the `moves-cli` package and exits.

##### Success

```
moves-cli version 0.1.0
```

##### Failure

Occurs if the package metadata cannot be read.

```
Error retrieving version
```

---

### moves speaker

Manages speaker profiles, including adding, editing, listing, processing, and deleting them.

#### `moves speaker add`

Creates a new speaker profile by providing a name, a presentation file, and a transcript file. The application copies these source files into its data directory for management.

##### `moves speaker add <name> <presentation_path> <transcript_path>`

##### Success

A new unique ID is generated for the speaker. The success message confirms the creation and displays the speaker's name and generated ID.

```
Speaker john (john-HntIO) has been successfully added.
```

##### Failure: File Not Found

Occurs if either the presentation or transcript file path is invalid or the file does not exist. The command will fail and report which file(s) are missing.

```
Could not add speaker 'john'.
  Presentation file not found: C:\Users\Donmez\Desktop\nonexistent_presentation.pdf
```

---

#### `moves speaker edit`

Updates an existing speaker's profile with a new presentation or transcript file.

##### `moves speaker edit <speaker> --presentation <new_path>`

Updates the presentation file for the specified speaker.

##### Success

```
Speaker john (john-HntIO) has been successfully edited.
  New presentation source:   C:\Users\Donmez\Desktop\presentation_new.pdf
```

##### `moves speaker edit <speaker> --transcript <new_path>`

Updates the transcript file for the specified speaker.

##### Success

```
Speaker john (john-HntIO) has been successfully edited.
  New transcript source:     C:\Users\Donmez\Desktop\transcript_new.pdf
```

##### Failure: Speaker Not Found

Occurs if the provided speaker name or ID does not match any registered speaker.

```
Error: Speaker 'jane' not found.
```

##### Failure: File Not Found

Occurs if the new file path for the presentation or transcript is invalid.

```
Could not update speaker john (john-HntIO).
  Presentation file not found: C:\Users\Donmez\Desktop\nonexistent.pdf
```

##### Failure: No Options Provided

Occurs if the command is run without specifying either a new presentation (`-p`) or a new transcript (`-t`).

```
Error: At least one update parameter (--presentation or --transcript) must be provided
```

---

#### `moves speaker list`

Displays a list of all registered speakers in a tabular format, showing their name, ID, processing status, and the last time they were processed.

##### Success: Speakers Found

```
There are 2 registered speakers.

NAME   ID           STATUS     LAST PROCESSED
────── ──────────── ────────── ────────────────
john   john-HntIO   Ready      2025-12-12 22:19
tom    tom-H4XX0    Not Ready  -
```

- **STATUS**: `Ready` indicates the speaker has been successfully processed and is ready for a presentation control session. `Not Ready` indicates the speaker has been added but not yet processed.
- **LAST PROCESSED**: Shows the date and time of the last successful processing. Displays `-` if never processed.

##### Success: No Speakers Found

```
No speakers are registered.
```

---

#### `moves speaker show`

Displays detailed information for a single specified speaker.

##### `moves speaker show <speaker>`

##### Success

```
Showing details for john (john-HntIO)
  Name:               john
  ID:                 john-HntIO
  Status:             Ready
  Last Processed:     2025-12-12 22:19
  Presentation:       C:\Users\Donmez\.moves\speakers\john-HntIO\presentation.pdf
  Transcript:         C:\Users\Donmez\.moves\speakers\john-HntIO\transcript.pdf
```

##### Failure: Speaker Not Found

Occurs if the provided speaker name or ID does not match any registered speaker.

```
Error: Speaker 'jane' not found.
```

---

#### `moves speaker delete`

Deletes one or more speaker profiles and all associated data, including presentation files, transcripts, and processed section data.

##### `moves speaker delete <speaker>`

Prompts the user for confirmation before deleting a single specified speaker.

##### Confirmation Prompt

```
Are you sure you want to delete the following 1 speaker(s)?
  john-HntIO

Proceed? [Y/n]:
```

##### User Confirms (Yes)

```
Are you sure you want to delete the following 1 speaker(s)?
  john-HntIO

Proceed? [Y/n]: Yes

Speaker(s) deleted.
```

##### User Cancels (No)

```
Are you sure you want to delete the following 1 speaker(s)?
  john-HntIO

Proceed? [Y/n]: No

Cancelled.
```

##### `moves speaker delete <speaker1> <speaker2> --yes`

Deletes multiple specified speakers without a confirmation prompt.

##### Success

```
Speaker john (john-HntIO) deleted.
Speaker tom (tom-H4XX0) deleted.
```

##### Failure: Speaker Not Found

Occurs if any of the provided speaker names or IDs do not match a registered speaker.

```
Error: Speaker 'jane' not found.
```

---

#### `moves speaker process`

Processes speaker data by analyzing the presentation and transcript files with a configured Large Language Model (LLM). This process breaks the presentation into manageable sections, matching transcript text to presentation content, which is required for the `presentation control` command.

##### `moves speaker process <speaker>`

Processes a single speaker.

##### Confirmation Prompt

The system displays the files that will be used for processing and prompts for confirmation.

```
Processing 1 speaker(s): john (john-HntIO)

john (john-HntIO)
  Presentation (BACKUP):   C:\Users\Donmez\.moves\speakers\john-HntIO\presentation.pdf
  Transcript (SOURCE):     C:\Users\Donmez\.moves\speakers\john-HntIO\transcript.pdf

Proceed? [Y/n]:
```

##### User Confirms (Yes) & In Progress

After confirmation, a spinner indicates that the process is running. The status message updates to reflect the current task (e.g., `Extracting Data...`, `Calling LLM...`).

```
Processing 1 speaker(s): john (john-HntIO)

john (john-HntIO)
  Presentation (BACKUP):   C:\Users\Donmez\.moves\speakers\john-HntIO\presentation.pdf
  Transcript (SOURCE):     C:\Users\Donmez\.moves\speakers\john-HntIO\transcript.pdf

Proceed? [Y/n]: Yes

⠼ john (john-HntIO): Calling LLM... 3.6s
```

##### User Cancels (No)

```
Processing 1 speaker(s): john (john-HntIO)

john (john-HntIO)
  Presentation (BACKUP):   C:\Users\Donmez\.moves\speakers\john-HntIO\presentation.pdf
  Transcript (SOURCE):     C:\Users\Donmez\.moves\speakers\john-HntIO\transcript.pdf

Proceed? [Y/n]: No

Cancelled.
```

##### Completion: Success

Upon successful completion, a summary is displayed showing the number of sections created and the total processing time.

```
Speaker john (john-HntIO) processed.

34 sections have been created in 7.2 seconds.
```

##### `moves speaker process -a`

Processes all registered speakers.

##### In Progress (Multiple Speakers)

When processing multiple speakers, each speaker gets a dedicated line with a spinner and a status message.

```
Processing 2 speaker(s): john (john-HntIO), tom (tom-H4XX0)

...
...

Proceed? [Y/n]: Yes

⠼ john (john-HntIO): Calling LLM... 3.6s
⠼ tom (tom-H4XX0):   Extracting Data... 2.6s
```

##### Completion: Success (Multiple Speakers)

A summary report is shown for all speakers, detailing the section count and processing time for each, followed by a total processing time.

```
2 speakers processed.
john (john-HntIO):      57 sections (11.2s)
tom (tom-H4XX0):        34 sections (4.6s)

Processing time took 15.8 seconds in total.
```

##### Failure: LLM Not Configured

Occurs if the LLM model or API key has not been set via `moves settings`.

```
Error: LLM model not configured. Use 'moves settings set model <model>' to configure.
```

---

### moves presentation

Manages the live presentation control session.

#### `moves presentation control`

Starts an interactive, voice-controlled presentation session for a speaker who has already been processed. The system listens to the microphone and automatically navigates the presentation based on the spoken words matching the transcript.

##### `moves presentation control <speaker>`

##### Initial State

A spinner is displayed while the session is being initialized.

```
⠋ Starting control session...
```

##### Running State

Once started, a live dashboard is displayed.

```
Live control session started for john (john-HntIO).
  [←/→] Previous/Next | [Ins] Pause/Resume | [Ctrl+C] Exit

1/34 | %23 | ✖
  Speech:  ...have
  Match:   ...you ever struggled when you tried to

1/34 | %75 | ■
  Speech:  ...have you ever struggled when you tried
  Match:   ...have you ever struggled when you tried

1/34 | %99 | ▶ 1
  Speech:  ...have you ever struggled when you tried
  Match:   ...have you ever struggled when you tried

2/34 | %84 | ◀ 1
  Speech:  ...have you ever struggled when you tried
  Match:   ...have you ever struggled when you tried
```

- **`1/34`**: The current section number out of the total.
- **`%23`**: The percentage of the current section's text that has been matched against the live speech.
- **Icon**:
  - `✖`: Low match confidence.
  - `■`: High match confidence, ready to advance.
  - `▶ 1`: Automatically advanced to the next section. The `1` indicates the number of sections advanced.
  - `◀ 1`: Automatically moved back to the previous section.
- **Speech**: A snippet of the most recently detected speech.
- **Match**: The corresponding text from the transcript section being matched against.
- **User Controls**:
  - `←`/`→`: Manually navigate to the previous or next section.
  - `Ins`: Pause or resume the live matching.
  - `Ctrl+C`: Exit the control session.

##### Completion State

When the user exits the session with `Ctrl+C`, a shutdown message is displayed.

```
Shutting down...

Control session ended.
```

##### Failure: Speaker Not Processed

Occurs if the `control` command is run on a speaker who has not yet been processed with `moves speaker process`.

```
Error: Speaker john (john-HntIO) has not been processed yet.
Please run 'moves speaker process john-HntIO' first to generate sections.
```

---

### moves settings

Manages application-level settings, such as the LLM model and API key.

#### `moves settings list`

Displays the current configuration settings. By default, the API key is masked for security.

##### Success

```
moves settings (see: C:\Users\Donmez\.moves\settings.toml)
  model (LLM Model) -> gemini/gemini-2.5-flash-lite
  key (API Key) -> AIza*******************************7RlM
```

##### Success: Show Full API Key

Using the `--show` or `-s` flag reveals the entire API key.

```
moves settings (see: C:\Users\Donmez\.moves\settings.toml)
  model (LLM Model) -> gemini/gemini-2.5-flash-lite
  key (API Key) -> AIzaSyB...long...api...key...string...7RlM
```

---

#### `moves settings set`

Sets or updates a configuration value.

##### `moves settings set <key> <value>`

##### Success

```
Setting(s) updated: model
  model: gemini/gemini-2.5-flash-lite
```

##### Failure: Invalid Key

Occurs if the setting key is not one of the valid options (e.g., `model`, `key`).

```
Error: Invalid setting key 'api_url'
Valid keys: model, key
```

---

#### `moves settings unset`

Resets a configuration setting to its default value.

##### `moves settings unset <key>`

##### Success

Resets the specified key and confirms the new (default) value.

```
Setting 'model' reset to default.
  New Value -> gemini-1.5-flash
```

##### Success: Resetting Key

If the key is reset, its value becomes `Not configured`.

```
Setting 'key' reset to default.
  New Value -> Not configured
```
