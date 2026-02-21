---
name: python-typing
description: Applies modern Python 3.10+ and 3.12+ type annotation standards. Use this when writing new Python code, adding type hints, or refactoring legacy typing (e.g., replacing typing.List with list).
---

# Modern Python Type Annotations

## When to use this skill
Use this skill when writing Python code, specifically when declaring function signatures, class attributes, or variable types. 

## Core Rules
- Always explicitly annotate function return types, including `-> None`.
- Import from the `typing` module **only** for advanced features not available in built-ins (e.g., `Any`, `Callable`, `Self`, `Literal`, `overload`).

## Built-in Collections vs. `typing` Module
Do not use `typing.List`, `typing.Dict`, `typing.Tuple`, or `typing.Type`. Use the built-in lowercase equivalents.

**Incorrect:**
```python
from typing import List, Dict, Type
def process(data: List[int]) -> Dict[str, Type[MyClass]]: ...
```

**Correct:**
```python
def process(data: list[int]) -> dict[str, type[MyClass]]: ...
```

## Unions and Optionals (3.10+)
Use the pipe operator `|` for Unions and Optionals instead of `typing.Union` or `typing.Optional`.

**Incorrect:**
```python
from typing import Optional, Union
def get_user(id: Union[int, str]) -> Optional[User]: ...
```

**Correct:**
```python
def get_user(id: int | str) -> User | None: ...
```

## Type Aliases (3.12+)
Use the `type` keyword for type aliases instead of assigning types to variables directly.

**Incorrect:**
```python
UserID = int | str
```

**Correct:**
```python
type UserID = int | str
```
