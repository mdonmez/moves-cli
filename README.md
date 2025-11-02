# moves

_Presentation control, reimagined._

[![moves](https://img.shields.io/badge/moves-003399?style=flat-square&color=003399&logoColor=ffffff)](https://github.com/mdonmez/moves-cli)
[![Python](https://img.shields.io/badge/python-3.13-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-d32f2f?style=flat-square&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0)

`moves` is a presentation control system that uses offline speech recognition and a hybrid similarity engine to advance slides automatically based on your speech. This enables a hands-free presentation experience.

---

### Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Quick Start](#quick-start)
  - [Command Overview](#command-overview)
- [Documentation](#documentation)
- [Tests](#tests)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Hands-Free:** Automatically advances slides based on your speech for a seamless, hands-free presentation.
- **Intelligent:** Utilizes an LLM to analyze and segment transcripts, mapping them accurately to presentation slides.
- **Private:** Performs all speech-to-text and similarity matching locally. No internet connection is required, ensuring data privacy and low latency.
- **Accurate:** A hybrid similarity engine combines semantic and phonetic analysis for precise speech-to-slide alignment, accommodating variations in speech.
- **Controlled:** Provides full manual override via keyboard controls to pause, resume, or navigate slides at any time.
- **Configurable:** A command-line interface for managing speaker profiles, processing presentation data, and configuring system settings.

## Installation

To install `moves`, use `uv` to install it as a tool:

#### Prerequisites

- [Python 3.13+](https://www.python.org/)
- [uv](https://github.com/astral-sh/uv) a fast Python package installer and resolver.

#### Install with uv

Install `moves-cli` using `uv tool install`:

```bash
uv tool install moves-cli --python 3.13
```

This will install `moves` and make it available as a command-line tool.

## Usage

Using `moves` consists of three main steps: configuring the AI model, processing the presentation data, and starting the control session.

### Quick Start

#### 1\. Configure the LLM

Configure `moves` with the desired Large Language Model (LLM) and provide an API key.

> **Note:** A list of compatible models is available at [LiteLLM Supported Models](https://models.litellm.ai/).

```bash
# Set the desired model (e.g., Gemini's Gemini-2.5-Flash-Lite)
moves settings set model gemini/gemini-2.5-flash-lite

# Set your API key
moves settings set key YOUR_API_KEY_HERE
```

#### 2\. Create and Process a Speaker Profile

Create a speaker profile by providing a presentation and its corresponding transcript (both in PDF format). Then, process the data to align the transcript with the slides.

```bash
# Add a speaker with their presentation and transcript
moves speaker add "John Doe" ./path/to/presentation.pdf ./path/to/transcript.pdf

# Process the speaker's data
moves speaker process "John Doe"
```

This step uses the configured LLM and may take a few moments to complete.

#### 3\. Start the Control Session

Open the presentation file in fullscreen mode and execute the `control` command.

```bash
moves presentation control "John Doe"
```

Once started, `moves` listens for your speech and sends `Right Arrow` key presses to advance the slides at the appropriate times.

### Command Overview

`moves` provides a command-line interface for managing presentations.

| Command              | Description                                          |
| -------------------- | ---------------------------------------------------- |
| `moves speaker`      | Manage speaker profiles, files, and AI processing.   |
| `moves presentation` | Start a live, voice-controlled presentation session. |
| `moves settings`     | Configure the LLM model and API key.                 |

For more details, please refer to the [CLI Commands](./docs/cli_commands.md).

## Documentation

For a detailed explanation of the system's architecture, components, and design, please refer to the [Documentation](./docs/README.MD), which covers:

- **[Architecture](./docs/architecture.md):** A high-level overview of the system's structure.
- **[Technical Details](./docs/about/README.md):** In-depth explanations of key components like the similarity engine, data models, and STT pipeline.

## Tests

`moves` includes a test suite. The test system uses `pytest`.

### Running Tests

```bash
uv run pytest
```

### Test Coverage

The test suite covers:

- **CLI Integration** - Essential command-line operations and error handling
- **Core Modules** - Settings editor, speaker manager, and presentation controller
- **Components** - Chunk generation, section extraction, and similarity calculation
- **Utilities** - Data handling, ID generation, model downloading, and text normalization

**Current Status:** 55/55 tests passing

For detailed information about the test structure, see the [Test System Documentation](./docs/about/tests.md).

## Contributing

Contributions are welcome. To contribute to the project, please follow these steps:

1.  **Fork** the repository on GitHub.
2.  **Clone** your fork locally.
3.  **Create a new branch** for your feature or bug fix (`git checkout -b feature/my-new-feature`).
4.  **Set up the environment** using `uv venv` and `uv sync`.
5.  **Make your changes** and commit them with a clear message.
6.  **Push** your branch to your fork (`git push origin feature/my-new-feature`).
7.  **Open a pull request** to the main repository.

## License

This project is licensed under the terms of the GNU General Public License v3.0. For more details, see the [LICENSE](./LICENSE) file.
