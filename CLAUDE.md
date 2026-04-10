# CLAUDE.md

## Project Overview

> RESTful API using Django REST Framework for managing ride information. Take-home assessment for AI Solutions Engineer (Full Stack) role at Wingz.

| Attribute | Value |
|-----------|-------|
| **Type** | Django Backend API |
| **Status** | Active development |
| **Language** | Python 3.11+ |
| **Framework** | Django 5.1 + DRF 3.15 |

<!-- AUTO-MANAGED: tech-stack -->
## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.11+ |
| Framework | Django 5.1 |
| API | Django REST Framework 3.15 |
| Database | MySQL 8.0 (prod), SQLite (tests/dev) |
| Testing | pytest 8.3 + pytest-django 4.9 |
| Linter | ruff 0.9 |
| WSGI | gunicorn 23 |
| Package Manager | pip + requirements.txt |
<!-- /AUTO-MANAGED: tech-stack -->

<!-- AUTO-MANAGED: commands -->
## Essential Commands

```bash
# All commands run from backend/
cd backend

# Development
python manage.py runserver              # Dev server (port 8000)
USE_SQLITE=1 python manage.py migrate   # Apply migrations (SQLite dev mode)

# Verification loop (run before every commit)
pytest -v                               # Run all tests
ruff check .                            # Lint check

# Migrations
python manage.py makemigrations         # Generate migrations
python manage.py migrate                # Apply migrations
```
<!-- /AUTO-MANAGED: commands -->

## Project Structure

```
ride0/
  backend/
    manage.py
    wingz/                        # Django project module
      settings.py                 # Single settings file (env-driven)
      urls.py                     # Root URL config
      wsgi.py                     # WSGI entry point
    rides/                        # Single Django app
      models.py                   # User, Ride, RideEvent (custom PKs)
      views.py                    # RideViewSet (ReadOnly)
      serializers.py              # Nested User/RideEvent serializers
      authentication.py           # EmailBasicAuthentication (HTTP Basic)
      permissions.py              # IsAdminRole
      pagination.py               # StandardPagination
      exceptions.py               # Custom exception handler
      urls.py                     # DRF router
    tests/
      conftest.py                 # Fixtures: admin_user, make_ride, make_event
      test_models.py
      test_views.py
      test_serializers.py
      test_permissions.py
      test_performance.py         # assertNumQueries tests
    sql/
      bonus_report.sql            # Trips >1hr by month/driver
      schema.sql
      seed_data.sql
  docs/
    requirement/                  # Original spec
    artifacts/                    # Implementation specs
  .github/workflows/deploy.yaml  # CI: lint + test + deploy to EC2
```

## Architecture Patterns

### Custom User Model (NOT Django auth)
The `User` model is a plain `models.Model` — not `AbstractUser` or `AbstractBaseUser`. It has `role` + `password` fields and a custom `is_authenticated` property. Authentication uses `EmailBasicAuthentication` (HTTP Basic with email:password against this custom model).

### Query Optimization Pattern
- `select_related("id_rider", "id_driver")` — JOIN users in single query
- `Prefetch("ride_events", queryset=...filter(created_at__gte=last_24h), to_attr="todays_ride_events")` — filtered prefetch for last-24h events only
- Target: 2-3 DB queries total (COUNT + rides+users JOIN + filtered events)

### Haversine Distance Sorting
- DB-level RawSQL annotation for distance calculation
- Enables ORDER BY + LIMIT pagination on full dataset
- SQLite tests register math functions (RADIANS, SIN, COS, etc.) via conftest fixture

### MTV Pattern (API variant)
```
URL → ViewSet → Model → Database
                  ↓
              Serializer → JSON Response
```

## Key Conventions

- **Naming:** snake_case (functions/variables), PascalCase (classes) — Python standard
- **Errors:** DRF exception_handler pattern + explicit `Response({"error": ...}, status=4xx)`
- **Imports:** stdlib → django → rest_framework → local app (grouped)
- **Structure:** Single app (`rides/`) + separate `tests/` dir at backend root
- **Tests:** pytest-django, class-based (`TestRideList`), fixtures as factories (`make_ride`, `make_event`), docstrings with test IDs (T-001...), `force_authenticate` for auth, `@pytest.mark.django_db`

### Additional Conventions
- TDD: Red → Green → Refactor for every module
- One feature per commit, meaningful commit messages (`<scope>: <description>`)
- Comments only on non-obvious "why" decisions, never on "what"
- `ruff check .` and `pytest -v` must pass before every commit
- Cannot modify table structure (per spec)

## Proof Cycle

Think before editing (SAIV — `.claude/rules/thinking-protocol.md`). After EVERY code change, run the proof cycle: lint → test. Completion claims require evidence — see `.claude/rules/verification.md`.

## Known Gotchas

- **Custom User model is NOT Django auth** — don't use `django.contrib.auth.models.User`, `AbstractUser`, or `authenticate()`. Use `rides.models.User` directly.
- **Custom primary keys** — `id_user`, `id_ride`, `id_ride_event` (NOT `id` or `pk`). ForeignKey fields use `db_column` to match spec table definitions.
- **Authentication is email:password** — HTTP Basic Auth via `EmailBasicAuthentication`, not username-based. Passwords stored with `make_password`/`check_password`.
- **SQLite for tests, MySQL for prod** — `settings.py` switches DB engine based on `pytest` in `sys.modules` or `USE_SQLITE` env var.
- **Haversine in SQLite tests** — `conftest.py` registers math functions (`RADIANS`, `SIN`, `COS`, `ASIN`, `SQRT`, `POWER`) so RawSQL works in test DB.
- **RideEvent table assumed VERY LARGE** — never load all events. Always filter to last 24h via `Prefetch` with `to_attr="todays_ride_events"`.
- **Ride table assumed VERY LARGE** — sorting must happen in DB (not Python). Distance sorting uses Haversine RawSQL annotation to support ORDER BY + LIMIT pagination.
- **N+1 queries** — use `select_related()` for ForeignKey, `prefetch_related()` for reverse relations.

## Context Budget

Details in `.claude/rules/`. Persist context to `HANDOFF.md` and `CONTEXT.md` before compacting — see `.claude/rules/context-management.md`.

## Knowledge Graph

If `graphify-out/GRAPH_REPORT.md` exists, read it before answering architecture or codebase questions — it contains god nodes, community clusters, and cross-file dependency analysis that saves significant token budget vs raw file scanning.

Setup: `pip install graphifyy && graphify install`, then `/graphify .` to build.

## Autonomous Mode

When running with `--dangerously-skip-permissions` (no tool approval prompts):
- **Hooks are your safety net** — they still run. Do not bypass or work around them.
- **Commit early and often** — small atomic commits after each logical change. You cannot ask for confirmation, so make changes reversible.
- **Update HANDOFF.md frequently** — after each milestone, not just at session end. Context loss is more costly without a human watching.
- **Stay conservative in scope** — do exactly what was asked. No opportunistic refactors, no "while I'm here" changes.
- **Verify harder** — run the full proof cycle after every change, not just at the end.

<!-- Generated by c2 v0.2.0 on 2026-04-10 -->
