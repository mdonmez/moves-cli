# Documentation Index

A complete guide to all documentation for the `moves` presentation control system.

## Quick Navigation

### For Users

**New to moves?**
→ Start here: [Getting Started Guide](GETTING_STARTED.md)

**Want to configure LLM?**
→ See: [Configuration Guide](CONFIGURATION.md)

**Need command documentation?**
→ Reference: [CLI Reference](CLI_REFERENCE.md)

**Curious about how it works?**
→ Read: [Architecture Guide](ARCHITECTURE.md)

### For Developers

**Contributing code?**
→ Start here: [Development Guide](DEVELOPMENT.md)

**Understanding the system?**
→ Read: [Architecture Guide](ARCHITECTURE.md)

---

## Documentation Overview

### [README.md](../README.md)
**Audience**: Everyone  
**Purpose**: Project overview, features, quick start, installation

**Contains**:
- What is `moves` and what does it do
- Key features summary
- Installation instructions
- Quick start (4-step setup)
- Basic troubleshooting
- License information

**Read if**: You're new to the project or need a quick overview

---

### [Getting Started Guide](GETTING_STARTED.md)
**Audience**: End users  
**Purpose**: Step-by-step walkthrough of using `moves`

**Contains**:
- Installation steps (Python, uv, moves)
- Creating your first speaker profile
- Two preparation methods (automatic with LLM, manual)
- Giving your first presentation
- Managing multiple speakers
- Troubleshooting common issues
- FAQ with 15+ common questions

**Read if**: You're setting up `moves` for the first time

**Sections**:
1. Installation
2. Initial Setup
3. Creating Your First Speaker
4. Preparing for Presentation
5. Giving a Presentation
6. Managing Speakers
7. Troubleshooting
8. FAQ

---

### [Architecture Guide](ARCHITECTURE.md)
**Audience**: Developers, technical users  
**Purpose**: Explain how `moves` is designed and how components work

**Contains**:
- High-level flow diagrams (preparation and presentation phases)
- Core component descriptions with responsibilities
- Data flow diagrams
- File organization
- Configuration parameters with explanations
- Model dependencies
- Error handling strategies
- Thread safety considerations
- Performance notes
- Extension points for customization

**Read if**: You want to understand the system design or contribute code

**Key Sections**:
- High-Level Flow
- Core Components (6 major components explained)
- Data Flow (two detailed diagrams)
- File Organization
- Configuration Parameters
- Extension Points

---

### [CLI Reference](CLI_REFERENCE.md)
**Audience**: Users, developers  
**Purpose**: Complete documentation of all commands and options

**Contains**:
- Syntax for every command
- Arguments and options for each command
- Real-world examples
- Sample output
- Error messages explained
- Common patterns and tips
- Speaker resolution behavior

**Organized by**:
- Speaker management (add, edit, list, show, prepare, delete)
- Presentation control (present)
- Settings management (list, set, unset)

**Read if**: You need to know exactly how to use a specific command

**Length**: ~500 lines with extensive examples

---

### [Configuration Guide](CONFIGURATION.md)
**Audience**: End users, developers  
**Purpose**: Setup and tune `moves` for your environment

**Contains**:
- Basic configuration (model, API key)
- 4 recommended LLM providers with setup steps:
  - Google Gemini (free, recommended)
  - OpenAI (paid)
  - Anthropic Claude (paid)
  - Others (Hugging Face, Groq, etc.)
- API key security and storage
- Configuration file locations
- Performance tuning parameters
- Advanced settings
- Troubleshooting configuration issues
- Configuration examples

**Read if**: You need to set up LLM, configure performance, or troubleshoot configuration

**Key Sections**:
- LLM Providers (4 detailed guides)
- API Keys & Security
- Performance Tuning
- Troubleshooting
- Configuration Examples

---

### [Development Guide](DEVELOPMENT.md)
**Audience**: Developers, contributors  
**Purpose**: Setup local development environment and contribute code

**Contains**:
- Project overview for developers
- Prerequisites and setup steps
- Project file structure
- Development environment setup
- Running tests (current status + how to add tests)
- Code style guidelines and standards
- Making changes (step-by-step feature example)
- Debugging techniques
- Building and publishing
- Common development tasks
- Git workflow
- Troubleshooting development issues

**Read if**: You want to contribute code or set up development environment

**Includes**:
- Example: Adding a new similarity unit (complete walkthrough)
- Testing best practices
- Code style examples
- Publication process

---

## Reading Paths

### Path 1: First-Time User
```
README.md (5 min)
  ↓
Getting Started Guide (30 min)
  ↓
Configuration Guide → LLM setup section (10 min)
  ↓
Ready to use!
```

### Path 2: Experienced User (Quick Setup)
```
README.md Quick Start section (5 min)
  ↓
CLI Reference for specific commands (as needed)
  ↓
Ready to use!
```

### Path 3: Troubleshooting
```
README.md → Common Issues (2 min)
  ↓
Getting Started Guide → Troubleshooting section (10 min)
  ↓
Configuration Guide → Troubleshooting section (10 min)
  ↓
Issue resolved!
```

### Path 4: Developer (Contributing)
```
README.md (5 min)
  ↓
Architecture Guide (30 min)
  ↓
Development Guide (20 min)
  ↓
Make your changes
  ↓
Submit PR!
```

### Path 5: Advanced User (Performance Tuning)
```
Architecture Guide → Core Components (15 min)
  ↓
Configuration Guide → Performance Tuning (10 min)
  ↓
Edit config.py and test
```

---

## Documentation Statistics

| Document | Lines | Sections | Audience |
|----------|-------|----------|----------|
| README.md | ~199 | 12 | Everyone |
| GETTING_STARTED.md | ~700 | 8 + FAQ | End Users |
| ARCHITECTURE.md | ~600 | 12 | Developers |
| CLI_REFERENCE.md | ~500 | 15 | Users/Devs |
| CONFIGURATION.md | ~550 | 8 | Users/Devs |
| DEVELOPMENT.md | ~600 | 10 | Developers |
| **TOTAL** | **~3,150** | **65+** | **All** |

---

## Topics Covered

### General Topics
- ✓ Installation (multiple methods)
- ✓ Quick start
- ✓ Features overview
- ✓ License information

### User Guidance
- ✓ Creating speaker profiles
- ✓ Preparing presentations (auto and manual)
- ✓ Running presentations
- ✓ Managing multiple speakers
- ✓ Keyboard shortcuts
- ✓ Troubleshooting (user perspective)

### Configuration
- ✓ LLM provider setup (4 providers)
- ✓ API key management and security
- ✓ Configuration file locations
- ✓ Performance tuning
- ✓ Advanced settings

### Technical/Architecture
- ✓ System design and flow
- ✓ Component descriptions
- ✓ Data flow diagrams
- ✓ File organization
- ✓ Algorithm explanations
- ✓ Performance considerations
- ✓ Error handling

### Development
- ✓ Setup development environment
- ✓ Code style standards
- ✓ Adding features (step-by-step example)
- ✓ Testing
- ✓ Debugging
- ✓ Building and publishing
- ✓ Git workflow

### Commands
- ✓ All CLI commands documented
- ✓ Arguments and options
- ✓ Real-world examples
- ✓ Sample output
- ✓ Error scenarios

---

## Key Features of Documentation

### Clarity
- Clear, plain language for non-technical users
- Technical depth for developers
- Consistent terminology

### Completeness
- Every command documented
- Every feature explained
- Every configuration option described
- FAQ section with 15+ questions

### Examples
- Quick start example
- Real-world command examples
- Code examples (in development guide)
- Configuration examples (in configuration guide)
- Feature addition walkthrough

### Organization
- Logical section structure
- Table of contents in each doc
- Clear headings and subheadings
- Cross-references between documents
- Consistent formatting

### Diagrams
- High-level system flow
- Data flow during preparation
- Data flow during presentation
- File organization tree

---

## How to Keep Documentation Updated

As the project evolves:

1. **New Commands**: Update CLI_REFERENCE.md and add to README quick start if important
2. **New Configuration Options**: Update CONFIGURATION.md and config.py defaults
3. **Architecture Changes**: Update ARCHITECTURE.md data flow diagrams
4. **New Features**: Update README features list, GETTING_STARTED.md, and relevant guides
5. **API Changes**: Update CLI_REFERENCE.md immediately

---

## Notes

- All documentation is in Markdown format for version control and easy collaboration
- All file paths use forward slashes for cross-platform compatibility
- All examples are PowerShell for Windows, but apply to any shell
- All documentation assumes Python 3.13+
- All commands assume `moves` is installed and on PATH

---

## Feedback & Contributions

Documentation improvements are welcome! If you find:
- **Unclear explanations** – Open an issue with suggestion
- **Missing information** – Describe what's needed
- **Outdated content** – Point out the section
- **Better examples** – Share them!

See [DEVELOPMENT.md](DEVELOPMENT.md) for contribution process.

---

**Last Updated**: January 2026  
**Documentation Version**: Complete  
**Status**: Ready for users and contributors
