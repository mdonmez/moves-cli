# moves Documentation

## Overview

`moves` is an intelligent presentation control system that enables hands-free, voice-driven slide navigation. By combining offline speech recognition with a hybrid similarity engine, it automatically advances slides based on your spoken words, creating a seamless presentation experience.

The system uses advanced natural language processing to analyze your speech in real-time, matching it against pre-processed presentation content to determine the appropriate slide transitions. All processing happens locally on your machine, ensuring privacy and low latency.

---

## Documentation Structure

### Getting Started

**[CLI Commands](cli_commands.md)** - Complete command-line reference for using `moves`

Learn how to configure the system, manage speaker profiles, process presentation data, and control live presentations. This guide includes practical examples and common workflows for day-to-day usage.

### Understanding the System

**[Architecture](architecture.md)** - High-level system design and component overview

Explore how `moves` is structured, including its dual-phase design (offline preparation and real-time control), major architectural layers, and how components interact to deliver hands-free presentation control.

### Deep Technical Insights

**[Technical Details](about/README.MD)** - In-depth implementation documentation

Dive deep into the internal workings of `moves`, including data processing pipelines, similarity algorithms, speech recognition implementation, data models, and testing infrastructure. Essential reading for contributors and those seeking comprehensive technical understanding.
