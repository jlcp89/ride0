# KNOWLEDGE.md — Persistent Insights

Debugging insights, environment quirks, and dependency gotchas that survive across sessions. Updated by `/wrap`, read by `/recover`.

## Troubleshooting Patterns

### SQLite math functions for Haversine tests
- **Context**: Running `pytest -v` with distance sorting tests
- **Problem**: SQLite doesn't have `RADIANS`, `SIN`, `COS`, `ASIN`, `SQRT`, `POWER` functions natively
- **Solution**: `conftest.py` has an `autouse` fixture `_register_sqlite_math` that registers Python `math` module functions into SQLite connection
- **Prevention**: Always check this fixture exists when adding new RawSQL that uses math functions

## Environment Quirks

### Database switching via settings.py
- `pytest` in `sys.modules` → SQLite in-memory (automatic for tests)
- `USE_SQLITE=1` env var → SQLite file-based (for dev/EC2 deployment)
- Neither → MySQL (production default)

## Dependencies & Gotchas

### PyMySQL + cryptography
- `pymysql` requires `cryptography` package for MySQL 8.0 authentication
- Both pinned in `requirements.txt`

### Deploy workflow missing seed data
- **Context**: Deployed API returned "Invalid credentials" for all requests
- **Problem**: `deploy.yaml` ran `migrate` but never loaded seed data — tables were empty
- **Solution**: Created `seed_db` management command (ORM-based, idempotent) and added `python manage.py seed_db` after migrate in both dev/prod deploy jobs
- **Prevention**: Any new data requirements need a corresponding seed command update, not just SQL file changes
