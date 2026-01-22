# Documentation Index

Complete documentation for the `moves` CLI presentation control system.

## Quick Navigation

| I want to... | Go to |
|--------------|-------|
| Get started with moves | [Getting Started Guide](GETTING_STARTED.md) |
| Configure LLM and API keys | [Configuration Guide](CONFIGURATION.md) |
| Look up a command | [CLI Reference](CLI_REFERENCE.md) |
| Understand how it works | [Architecture Guide](ARCHITECTURE.md) |
| Contribute code | [Development Guide](DEVELOPMENT.md) |
| Get a project overview | [README](../README.md) |

---

## Documentation Overview

### [README.md](../README.md)

**Audience**: Everyone

Quick project introduction covering:
- What moves does and key features
- Installation instructions
- 4-step quick start guide
- System architecture overview
- Supported file formats and LLM providers
- Common troubleshooting

### [Getting Started Guide](GETTING_STARTED.md)

**Audience**: End users

Step-by-step walkthrough:
1. Installation (Python, uv/pip, moves-cli)
2. Understanding the data directory structure
3. Creating speaker profiles (local files + Google Drive)
4. Preparing presentations (auto LLM mode vs manual mode)
5. Running presentations with keyboard controls
6. Managing multiple speakers
7. Troubleshooting common issues
8. FAQ with 15+ questions

### [Architecture Guide](ARCHITECTURE.md)

**Audience**: Developers, technical users

System internals:
- High-level preparation and presentation flow
- Core components (SpeakerManager, PresentationController, SimilarityCalculator, etc.)
- Data flow diagrams for both phases
- File organization and project structure
- Configuration parameters explained
- Model dependencies (STT, VAD, embeddings)
- Thread model and safety considerations
- Extension points for customization

### [CLI Reference](CLI_REFERENCE.md)

**Audience**: All users

Complete command documentation:
- Speaker commands: `add`, `edit`, `list`, `show`, `prepare`, `delete`
- Presentation: `present` with keyboard shortcuts
- Settings: `list`, `set`, `unset`
- Examples, sample output, and error messages
- Speaker resolution (by name or ID)
- Common patterns and tips

### [Configuration Guide](CONFIGURATION.md)

**Audience**: All users

Setup and tuning:
- LLM provider setup (Gemini, OpenAI, Anthropic, others)
- API key security (Windows Credential Manager, keyring)
- Configuration file locations
- Performance tuning parameters (similarity, VAD, chunking)
- Advanced settings and customization
- Troubleshooting configuration issues

### [Development Guide](DEVELOPMENT.md)

**Audience**: Contributors

Development setup:
- Prerequisites and environment setup
- Project structure walkthrough
- Code style and standards (type hints, docstrings)
- Adding new features (example: new similarity unit)
- Testing approach
- Debugging techniques
- Building and publishing to PyPI
- Git workflow and contribution guidelines

---

## Reading Paths

### First-Time User
```
README.md → Getting Started Guide → Configuration Guide (LLM setup)
```

### Quick Setup
```
README.md (Quick Start section) → CLI Reference (as needed)
```

### Troubleshooting
```
README.md (Common Issues) → Getting Started (Troubleshooting) → Configuration (Troubleshooting)
```

### Developer/Contributor
```
README.md → Architecture Guide → Development Guide → Submit PR
```

### Performance Tuning
```
Architecture Guide (Core Components) → Configuration Guide (Performance Tuning)
```

---

## Key Topics

### For Users
- ✓ Installation (uv and pip methods)
- ✓ Speaker profile management (add, edit, list, show, delete)
- ✓ Preparation (automatic with LLM, manual without)
- ✓ Presentation controls (keyboard shortcuts, states)
- ✓ Multi-format support (PDF, DOCX, PPTX, TXT)
- ✓ Google Drive integration
- ✓ Troubleshooting

### For Configuration
- ✓ LLM providers (Gemini, OpenAI, Anthropic, Groq, etc.)
- ✓ API key management (secure storage via keyring)
- ✓ Similarity tuning (weights, thresholds)
- ✓ VAD tuning (sensitivity, silence detection)
- ✓ Chunk configuration (window size, candidate range)

### For Developers
- ✓ Project structure and file organization
- ✓ Core components and responsibilities
- ✓ Data flow and threading model
- ✓ Code style (Python 3.13+, type hints)
- ✓ Adding new features
- ✓ Building and publishing

---

## Notes

- All documentation uses Markdown format
- Examples work on Windows, macOS, and Linux
- Python 3.13+ required
- Commands assume `moves` is installed and on PATH

---

## Feedback

Found an issue? [Open an issue](https://github.com/mdonmez/moves-cli/issues) or see [Development Guide](DEVELOPMENT.md) for contribution process.
