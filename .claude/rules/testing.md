---
paths:
  - "**/test_*"
  - "**/*_test.py"
  - "**/tests/**"
  - "**/conftest.py"
---

# Pytest Testing Rules

## File Naming
- Test files: `test_<module>.py`
- Conftest: `conftest.py` for shared fixtures (at `backend/tests/` level)

## Patterns
- Use fixtures for setup/teardown (`@pytest.fixture`)
- Factory fixtures: `make_ride()`, `make_event()` with overridable defaults
- Use `conftest.py` for shared fixtures
- Class-based test grouping (`TestRideList`) with `@pytest.mark.django_db`
- Test docstrings with IDs: `"""T-NNN: description."""`
- Use `force_authenticate` for view tests (test auth separately in `test_permissions.py`)

## Assertions
- Use plain `assert` statements — pytest rewrites them for good output
- For exceptions: `with pytest.raises(ValueError, match="expected msg")`
- Compare complex objects with `==` — pytest shows diffs

## Performance
- Use `assertNumQueries` to verify query count contracts
- Every endpoint test should verify query budget

## Fixtures
- Scope appropriately: `function` (default) for most tests
- `_register_sqlite_math` is `autouse=True` — registers math functions for Haversine in SQLite
- Use `yield` fixtures for cleanup
