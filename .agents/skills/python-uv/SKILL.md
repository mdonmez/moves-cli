---
name: python-uv
description: Manages Python packages, virtual environments, and script execution using the 'uv' tool. Use this whenever working with Python environments, installing dependencies, running python scripts, or executing tools like pytest, instead of using pip, poetry, or python -m venv.
---

# Modern Python Package and Environment Management (uv)

## When to use this skill

Use these instructions whenever you need to execute Python scripts, manage project dependencies, or run Python-based CLI tools.

## Core Rules

- **Always** use `uv` for all package management and script execution tasks.
- **Never** use `pip`, `poetry`, `pip-tools`, or `virtualenv` commands directly.
- **Do not** manually create or activate virtual environments (e.g., no `source .venv/bin/activate` or `python -m venv`). `uv` handles this automatically.

## Command Mappings

When you would normally use standard Python commands, substitute them with the following `uv` equivalents:

| Legacy Command (Don't Use) | Modern `uv` Command (Use) | Description                                                 |
| :------------------------- | :------------------------ | :---------------------------------------------------------- |
| `pip install <pkg>`        | `uv add <pkg>`            | Add a dependency to the project.                            |
| `pip uninstall <pkg>`      | `uv remove <pkg>`         | Remove a dependency from the project.                       |
| `pip install -r req.txt`   | `uv sync`                 | Install dependencies from lockfiles/requirements.           |
| `python -m venv .venv`     | `uv venv`                 | Create a virtual environment.                               |
| `python script.py`         | `uv run script.py`        | Execute a Python script in the correct environment.         |
| `pytest` / `ruff`          | `uv run <tool>`           | Execute a tool ensuring it runs in the correct environment. |

## Examples

**Adding a dependency:**

```bash
# DO NOT: pip install requests
uv add requests
```

````

**Running a script:**

```bash
# DO NOT: python main.py
uv run main.py
```

**Running a test suite:**

```bash
# DO NOT: pytest tests/
uv run pytest tests/
```
````
