# Wingz Ride Management API — Project Conventions

## Overview
Django REST Framework API for ride management. Take-home assessment.

## Tech Stack
- **Backend**: Python 3.11+, Django 5.1, DRF 3.15, MySQL 8.0
- **Frontend**: React (Vite), nginx reverse proxy
- **Testing**: pytest + pytest-django, ruff for linting
- **Infrastructure**: Docker Compose (MySQL + Backend + Frontend)

## Architecture
- Single Django app: `rides` (models, views, serializers, permissions, authentication)
- Custom User model with `role` + `password` fields (NOT Django's built-in auth User)
- Custom `EmailBasicAuthentication` for HTTP Basic Auth via email:password
- Custom primary keys matching spec: `id_user`, `id_ride`, `id_ride_event`
- SQLite for tests, MySQL for production/Docker

## Key Constraints
- Ride table is assumed VERY LARGE — sorting must happen in DB, not Python
- RideEvent table is assumed VERY LARGE — never load all events, filter to last 24h
- Ride list API: maximum 3 DB queries (COUNT + rides JOIN users + filtered events)
- Cannot modify table structure (per spec)

## Conventions
- TDD: Red → Green → Refactor for every module
- One feature per commit, meaningful commit messages
- Comments only on non-obvious "why" decisions, never on "what"
- `ruff check .` must pass before every commit
- `pytest -v` must pass before every commit

## Commit Message Format
```
<scope>: <description>

Examples:
scaffold: Django project + rides app + test config
models: User, Ride, RideEvent with custom PKs matching spec
auth: admin-only permission class + BasicAuth with tests
perf: assertNumQueries tests proving query count
```

## Verification Loop (run before every commit)
```bash
cd backend && pytest -v && ruff check . && cd ..
git add -A && git commit -m "<message>"
```

## Artifacts Location
Implementation specs: `./docs/artifacts/`
Phase 1 reads these before writing any code.
