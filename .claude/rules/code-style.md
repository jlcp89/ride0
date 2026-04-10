---
paths:
  - "**/*.py"
---

# Python Code Style

## Naming
- Files/modules: snake_case (`user_service.py`, `auth_handler.py`)
- Classes: PascalCase (`UserService`, `EventHandler`)
- Functions/variables: snake_case (`get_user`, `auth_token`)
- Constants: UPPER_SNAKE_CASE (`MAX_RETRIES`, `DEFAULT_TIMEOUT`)
- Private: single underscore prefix (`_internal_helper`)
- Type variables: PascalCase (`T`, `ResponseT`)

## Imports
- Group: stdlib → third-party (django, rest_framework) → local (rides)
- Use absolute imports over relative
- Avoid wildcard imports (`from module import *`)

## Patterns
- Use context managers (`with`) for resource management
- Avoid mutable default arguments (`def f(items=None)` not `def f(items=[])`)

## Limits
- Functions: 40 lines max, 5 params max, nesting depth 3
- Files: 300 lines max
- See `quality.md` for full table

## Formatting
- Follow project's ruff config
- Double quotes for strings (match project formatter)
