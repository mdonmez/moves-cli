---
name: python-best-practices
description: Applies Python ecosystem best practices including Ruff formatting, async programming, FastAPI, and Loguru. Use this when setting up new Python projects, architecting applications, or standardizing codebases.
---

# Python General Best Practices

## When to use this skill
Use these guidelines when making architectural choices, selecting libraries for a project, writing documentation, or handling I/O and logging.

## Code Quality & Formatting
- **Linting/Formatting**: Assume the use of `Ruff`. Write code that complies with standard Ruff rules (e.g., sorted imports, standard whitespace).
- **Documentation**: Use Google-style docstrings for all complex functions and classes.

## Library Selections
- **Web APIs**: Use `FastAPI` for building web APIs. Avoid using Flask or Django for new API projects.
- **Logging**: Use `loguru` for logging instead of the built-in `logging` module.
  ```python
  from loguru import logger
  logger.info("Application started")
  ```

## Performance & Architecture
- **Async Programming**: Use `async` and `await` for I/O-bound operations (e.g., network requests, database queries). Use `asyncio.run()` for the main entry point.
- **Resource Management**: Strictly manage resources (files, sockets, database locks) using `with` statements (context managers) to prevent leaks.
- **Memory Efficiency**: Prefer generators and iterators (using `yield`) over creating large lists in memory for bulk data processing.
  ```python
  # Correct (Generator)
  def process_large_file(path: Path):
      with path.open() as f:
          for line in f:
              yield process(line)
  ```
