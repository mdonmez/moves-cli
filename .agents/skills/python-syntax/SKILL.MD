---
name: python-syntax
description: Implements modern Python 3.10+ syntax features. Use this when writing or updating Python code to use structural pattern matching, pathlib, f-strings, and modern enums.
---

# Modern Python Syntax (3.10+)

## When to use this skill
Apply these rules when writing new Python code or refactoring existing scripts to ensure the codebase utilizes modern Python syntactic sugar and standard libraries.

## Core Rules

### 1. File System Interactions (`pathlib`)
Use `pathlib.Path` for all file system interactions. Avoid `os.path` and `os.walk`.
```python
from pathlib import Path

# Correct
config_path = Path("config") / "settings.json"
if config_path.exists():
    text = config_path.read_text()
```

### 2. Structural Pattern Matching (`match` / `case`)
Use `match` and `case` statements over complex `if/elif/else` chains or `isinstance` checks.
```python
match response.status_code:
    case 200:
        return handle_success()
    case 404 | 403:
        return handle_error()
    case _:
        return handle_unknown()
```

### 3. String Formatting
Use f-strings for all string formatting. Never use `%` formatting or `.format()`.
```python
# Correct
print(f"User {user_id} logged in from {ip_address}")
```

### 4. Assignment Expressions (Walrus Operator)
Use the walrus operator `:=` for assignment expressions inside conditions to improve conciseness.
```python
if (n := len(items)) > 10:
    print(f"List is too long ({n} elements)")
```

### 5. Classes and Data Structures
- Use `@dataclass` (with `slots=True` when possible) for classes that primarily store data.
- Use `enum.StrEnum` or `enum.IntEnum` for constant enumerations.
```python
from dataclasses import dataclass
from enum import StrEnum

class Status(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

@dataclass(slots=True)
class UserData:
    id: int
    status: Status
```