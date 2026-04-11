# Phase 0 — Requirements Analysis + Project Foundation

## Role

You are a **Principal Software Architect** analyzing requirements and producing implementation-ready artifacts. Everything you generate here will be directly consumed by Phase 1 (Backend TDD) and Phase 2 (Frontend + Docker + Docs). Artifacts are not decorative — they are the **single source of truth** that downstream phases read before writing any code.

## Mission

1. Read the assessment requirements
2. Set up the project repository with git, CLAUDE.md, and directory structure
3. Generate precise, implementation-ready artifacts under `./docs/artifacts/`
4. Every artifact must be concrete enough that Phase 1 can implement from it without re-reading the original PDF

## Context

Read the assessment specification (the Wingz Django REST Framework ride management API requirements). The requirements document should be available in the working directory or provided as context.

Assessment criteria (what the reviewers grade):
- **Functionality** — all features work
- **Code Quality** — modular, readable, maintainable
- **Error Handling** — edge cases covered
- **Performance** — minimal SQL queries to the database

Our differentiators (what makes this submission stand out):
- Commit history that tells a story (starts HERE in Phase 0)
- Tests that prove understanding, not just coverage
- A README that reads like an architecture document
- Bonus SQL done thoroughly with edge case handling
- Seed data intentionally designed to test edge cases

---

## Step 1: Initialize Repository + Project Structure

Phase 0 creates ONLY the docs/artifacts directory structure, CLAUDE.md, and .gitignore.
Everything else is created by Phase 1 (backend/) and Phase 2 (frontend/, docker-compose.yml, Makefile, .env.example).

```bash
git init
```

Create the Phase 0 directory structure:
```
./
├── CLAUDE.md                    # Project conventions for Claude Code
├── .gitignore
└── docs/
    └── artifacts/
        ├── analysis/
        │   ├── implementation-plan.yaml
        │   └── architecture-decisions.md
        └── features/
            ├── database-schema/
            │   ├── feature-brief.md
            │   ├── schema-spec.sql
            │   ├── seed-data-spec.md
            │   └── data-models.yaml
            ├── authentication/
            │   ├── feature-brief.md
            │   └── test-scenarios.md
            ├── ride-list-api/
            │   ├── feature-brief.md
            │   ├── api-contract.md
            │   ├── test-scenarios.md
            │   └── error-mapping.md
            ├── performance/
            │   ├── feature-brief.md
            │   ├── query-strategy.md
            │   └── test-scenarios.md
            ├── sorting/
            │   ├── feature-brief.md
            │   ├── distance-calculation.md
            │   └── test-scenarios.md
            └── bonus-sql/
                ├── feature-brief.md
                ├── query.sql
                └── test-scenarios.md
```

Do NOT create `backend/`, `frontend/`, `Makefile`, or `.env.example` — those are created by Phase 1 and Phase 2 respectively.

### `CLAUDE.md`

```markdown
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
```

### `.gitignore`
```gitignore
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
node_modules/
frontend/dist/
.env
.env.local
.vscode/
.idea/
*.swp
.DS_Store
db_data/
.pytest_cache/
.coverage
htmlcov/
*.log
```

**DO NOT COMMIT YET — Steps 1 and 2 are combined into a single commit.**

---

## Step 2: Implementation Plan

### `docs/artifacts/analysis/implementation-plan.yaml`

```yaml
# Implementation plan: phased approach with clear dependencies
# Each phase produces concrete artifacts consumed by the next

phases:
  - phase: 0
    name: "Analysis & Foundation"
    description: "Generate artifacts, set up repo, establish conventions"
    commits:
      - "init: project structure, conventions, and architecture decisions"
      - "docs: implementation specs and feature artifacts"

  - phase: 1
    name: "Backend TDD"
    depends_on: [0]
    description: "Models → Auth → Serializers → Views (list, filter, sort) → Perf tests → Bonus SQL"
    features:
      - name: Database Schema & Models
        description: "User, Ride, RideEvent models with custom PKs matching spec table definitions"
        criteria: [Functionality, Code Quality]

      - name: Authentication
        description: "Custom BasicAuth + admin-only permission checking user.role == 'admin'"
        criteria: [Functionality, Error Handling]

      - name: Ride List API
        description: "GET /api/rides/ — paginated, nested rider/driver/events, filter by status/rider_email"
        criteria: [Functionality]

      - name: Sorting
        description: "Sort by pickup_time (DB ORDER BY) and distance (Haversine RawSQL annotation)"
        criteria: [Functionality, Performance]
        notes: "Must sort in DB for large tables. Must work with pagination."

      - name: Performance Optimization
        description: "todays_ride_events via Prefetch (last 24h only), 2-3 queries total, assertNumQueries tests"
        criteria: [Performance]
        notes: "Verified by assertNumQueries tests"

      - name: Bonus SQL
        description: "Raw SQL for trips > 1 hour by month and driver"
        criteria: [Functionality]
        notes: "Most candidates skip this. We won't."

    commits:
      - "scaffold: Django project + rides app + test config"
      - "models: User, Ride, RideEvent with custom PKs matching spec"
      - "schema: MySQL DDL + intentional seed data for edge cases"
      - "auth: admin-only permission class + BasicAuth with tests"
      - "serializers: nested rider/driver + todays_ride_events"
      - "api: ride list endpoint with pagination and filtering"
      - "sorting: pickup_time and Haversine distance with DB-level sort"
      - "perf: assertNumQueries tests proving 2-3 query target"
      - "bonus: raw SQL for trips > 1hr with edge case handling"
      - "docker: backend Dockerfile"

  - phase: 2
    name: "Frontend + Docker + Docs"
    depends_on: [1]
    description: "Docker Compose → Frontend → README → Makefile"
    features:
      - name: Docker Orchestration
        description: "Docker Compose with MySQL, backend, frontend + healthchecks"
        criteria: [Functionality]

      - name: Frontend
        description: "React admin dashboard — functional, clean, demonstrates the API"
        criteria: [Functionality]
        notes: "Assessment doesn't require frontend. Keep it minimal — backend is the priority."

      - name: Documentation
        description: "README with architecture decisions, tradeoffs, production considerations"
        criteria: [Code Quality]
        notes: "This is the #1 differentiator. README must read like a senior engineer's arch doc."

    commits:
      - "docker: Compose + backend Dockerfile + healthchecks"
      - "frontend: React app with ride list, filters, pagination"
      - "docs: comprehensive README with architecture decisions and Makefile"
```

### `docs/artifacts/analysis/architecture-decisions.md`

```markdown
# Architecture Decisions

## ADR-1: Django REST Framework
**Decision:** Use DRF with ModelViewSet
**Rationale:** Assessment requirement. ReadOnlyModelViewSet is sufficient since
we only need list/retrieve operations.

## ADR-2: Custom User Model with BasicAuthentication
**Decision:** Create a standalone `User` model in the rides app (NOT extending
Django's `AbstractUser`) with an additional `password` field for authentication.
Use DRF's `BasicAuthentication` so the API can be tested via curl with `-u email:password`.
**Rationale:** The spec defines a custom table structure with `id_user` PK and `role`
field. Mapping this to Django's auth system would add unnecessary complexity. Adding
a `password` field (hashed via Django's `make_password`) is the minimal addition
needed to support real authentication. BasicAuth is simple, works with curl, and
is appropriate for an assessment — production would use Token/JWT auth.
**Tradeoff:** We lose Django admin login, but the spec doesn't require it. BasicAuth
sends credentials in every request (no sessions), which is fine for this scope.

## ADR-3: select_related + Prefetch for Query Performance
**Decision:** Use `select_related('id_rider', 'id_driver')` + `Prefetch('ride_events',
queryset=filtered, to_attr='todays_ride_events')`
**Rationale:** This achieves the 2-3 query target:
  - Query 1: COUNT for pagination
  - Query 2: rides JOIN users (select_related creates a SQL JOIN)
  - Query 3: ride_events filtered to last 24h (Prefetch batches all in one query)
**Why not SerializerMethodField?** A method field like `get_todays_ride_events(obj)`
would execute a query PER RIDE — classic N+1 problem.

## ADR-4: Haversine via RawSQL Annotation
**Decision:** Use `RawSQL` to annotate rides with Haversine distance, then `order_by('distance')`
**Rationale:** The spec assumes a very large ride table. Sorting must happen in the DB
so pagination works correctly. Loading all rides into Python to sort would require
O(n) memory and break pagination.
**Alternatives considered:**
  - `Func/Sin/Cos` expressions: Django doesn't have a built-in Haversine expression.
    Building one from `Func` is verbose and less readable than RawSQL.
  - PostGIS/GeoDjango: Overkill for MySQL and adds a heavy dependency.
  - `ST_Distance_Sphere()`: MySQL-specific, would break SQLite tests.
**Tradeoff:** RawSQL is less portable but works on both MySQL and SQLite (with
registered math functions in tests).

## ADR-5: SQLite for Tests, MySQL for Production
**Decision:** pytest uses SQLite in-memory via settings override
**Rationale:** Fast test execution, no Docker dependency for running tests. SQLite
math functions (RADIANS, SIN, COS, etc.) are registered via a pytest autouse fixture
so the Haversine RawSQL works in tests.

## ADR-6: Bonus SQL with Edge Case Handling
**Decision:** Use subqueries with MIN(pickup)/MAX(dropoff) per ride
**Rationale:** A ride could theoretically have multiple "Status changed to pickup"
events (if status toggled back and forth). Using MIN/MAX captures the full trip
window and avoids double-counting.

## ADR-7: Commit-per-Feature Strategy
**Decision:** One logical feature per commit (~14 commits total)
**Rationale:** The assessment explicitly says "commit history should be clean and
meaningful, showing progression." This is a signal assessors check. A single commit
screams "generated in one shot." But too many micro-commits (20+) looks artificial —
natural groupings like "filtering + pagination" in one commit is fine.
```

**COMMIT NOW:** `git add -A && git commit -m "init: project structure, conventions, and architecture decisions"`

---

## Step 3: Database Schema Artifacts

**This step is part of Commit 2: "docs: implementation specs and feature artifacts"**

### `docs/artifacts/features/database-schema/feature-brief.md`

```markdown
# Feature: Database Schema & Models

## Summary
Define the MySQL schema and Django ORM models for the three tables specified
in the assessment: User, Ride, and RideEvent. All primary keys, foreign keys,
field types, and table names must match the spec exactly.

## Requirements
- REQ-1: User table with id_user PK, role, first_name, last_name, email, phone_number, password
- REQ-2: Ride table with id_ride PK, status, id_rider FK, id_driver FK, GPS coords, pickup_time
- REQ-3: RideEvent table with id_ride_event PK, id_ride FK, description, created_at
- REQ-4: All Django models use custom PKs (AutoField with primary_key=True)
- REQ-5: FK columns use db_column to match spec names exactly
- REQ-6: Indexes on ride_events.created_at (for 24h filter), rides.status, rides.pickup_time

## Dependencies
- Depends on: nothing
- Depended by: ALL other features

## Acceptance Criteria
- [ ] `User._meta.db_table == "users"` and PK is `id_user`
- [ ] `Ride._meta.db_table == "rides"` and PK is `id_ride`
- [ ] `RideEvent._meta.db_table == "ride_events"` and PK is `id_ride_event`
- [ ] Two FKs on Ride to User have distinct related_names
- [ ] `db_column` matches spec column names
- [ ] Index on `ride_events.created_at` exists

## Technical Notes
- Django appends `_id` to FK attributes internally. Use `db_column="id_rider"` etc.
- Two FKs to the same model MUST have different `related_name` or Django errors
- Use `models.AutoField(primary_key=True)` for custom PKs, not default `id`
```

### `docs/artifacts/features/database-schema/schema-spec.sql`

```sql
-- Schema for Wingz Ride Management API
-- MySQL 8.0, InnoDB, utf8mb4

CREATE TABLE IF NOT EXISTS users (
    id_user INT AUTO_INCREMENT PRIMARY KEY,
    role VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone_number VARCHAR(50) NOT NULL,
    password VARCHAR(128) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS rides (
    id_ride INT AUTO_INCREMENT PRIMARY KEY,
    status VARCHAR(50) NOT NULL,
    id_rider INT NOT NULL,
    id_driver INT NOT NULL,
    pickup_latitude FLOAT NOT NULL,
    pickup_longitude FLOAT NOT NULL,
    dropoff_latitude FLOAT NOT NULL,
    dropoff_longitude FLOAT NOT NULL,
    pickup_time DATETIME NOT NULL,
    FOREIGN KEY (id_rider) REFERENCES users(id_user),
    FOREIGN KEY (id_driver) REFERENCES users(id_user),
    INDEX idx_ride_status (status),
    INDEX idx_ride_pickup_time (pickup_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS ride_events (
    id_ride_event INT AUTO_INCREMENT PRIMARY KEY,
    id_ride INT NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (id_ride) REFERENCES rides(id_ride),
    INDEX idx_rideevent_created (created_at),
    INDEX idx_rideevent_ride_id (id_ride)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### `docs/artifacts/features/database-schema/data-models.yaml`

```yaml
models:
  - name: User
    django_class: User
    table: users
    fields:
      - name: id_user
        type: INT AUTO_INCREMENT
        django: AutoField(primary_key=True)
        description: "Custom PK — not Django's default 'id'"
      - name: role
        type: VARCHAR(50)
        django: CharField(max_length=50)
        description: "'admin', 'driver', 'rider', etc."
      - name: first_name
        type: VARCHAR(100)
        django: CharField(max_length=100)
      - name: last_name
        type: VARCHAR(100)
        django: CharField(max_length=100)
      - name: email
        type: VARCHAR(255)
        django: CharField(max_length=255)
      - name: phone_number
        type: VARCHAR(50)
        django: CharField(max_length=50)
      - name: password
        type: VARCHAR(128)
        django: CharField(max_length=128)
        description: "Hashed via Django's make_password(). Verified via check_password()."

  - name: Ride
    django_class: Ride
    table: rides
    fields:
      - name: id_ride
        type: INT AUTO_INCREMENT
        django: AutoField(primary_key=True)
      - name: status
        type: VARCHAR(50)
        django: CharField(max_length=50)
        description: "'en-route', 'to-pickup', 'dropoff'"
      - name: id_rider
        type: INT FK → users.id_user
        django: "ForeignKey(User, on_delete=CASCADE, related_name='rides_as_rider', db_column='id_rider')"
      - name: id_driver
        type: INT FK → users.id_user
        django: "ForeignKey(User, on_delete=CASCADE, related_name='rides_as_driver', db_column='id_driver')"
      - name: pickup_latitude
        type: FLOAT
        django: FloatField()
      - name: pickup_longitude
        type: FLOAT
        django: FloatField()
      - name: dropoff_latitude
        type: FLOAT
        django: FloatField()
      - name: dropoff_longitude
        type: FLOAT
        django: FloatField()
      - name: pickup_time
        type: DATETIME
        django: DateTimeField()

  - name: RideEvent
    django_class: RideEvent
    table: ride_events
    fields:
      - name: id_ride_event
        type: INT AUTO_INCREMENT
        django: AutoField(primary_key=True)
      - name: id_ride
        type: INT FK → rides.id_ride
        django: "ForeignKey(Ride, on_delete=CASCADE, related_name='ride_events', db_column='id_ride')"
      - name: description
        type: VARCHAR(255)
        django: CharField(max_length=255)
      - name: created_at
        type: DATETIME
        django: DateTimeField()
    indexes:
      - fields: [created_at]
        name: idx_rideevent_created
        reason: "Performance — filtered Prefetch for todays_ride_events"
```

### `docs/artifacts/features/database-schema/seed-data-spec.md`

```markdown
# Seed Data Specification

## Design Principle
Every row exists to test something specific. This is NOT random data.

## Users (7 total)

All users seeded with password hashed via Django's `make_password('adminpass123')` for the admin, and `make_password('userpass123')` for others.

| id | first_name | last_name | email | role | Purpose |
|----|-----------|-----------|-------|------|---------|
| 1 | Admin | User | admin@wingz.com | admin | Auth test — can access API (password: adminpass123) |
| 2 | Chris | H | chris@wingz.com | driver | Bonus SQL sample driver |
| 3 | Howard | Y | howard@wingz.com | driver | Bonus SQL sample driver |
| 4 | Randy | W | randy@wingz.com | driver | Bonus SQL sample driver |
| 5 | Alice | Rider | alice@wingz.com | rider | Filtering by rider email |
| 6 | Bob | Rider | bob@wingz.com | rider | Second rider for filter tests |
| 7 | Carol | Rider | carol@wingz.com | rider | Third rider |

**Note:** Driver names match the bonus SQL sample output (Chris H, Howard Y, Randy W).

## Rides (20+ total)

Design requirements:
- At least 5 per status (en-route, to-pickup, dropoff) — tests status filtering
- Multiple drivers and riders — tests email filtering
- GPS coords at KNOWN distances from reference point (14.5995, -90.5131 = Zone 10, Guatemala City):
  - 2-3 rides AT reference point (~0 km) — distance sort first position
  - 2-3 rides at Zone 14 (14.5880, -90.4800 ≈ 3.5 km) — middle
  - 2-3 rides at Antigua (14.5586, -90.7295 ≈ 25 km) — distance sort last position
- pickup_time spread across Jan-Apr 2024 — tests time sorting
- 2-3 rides with pickup_time = NOW() — tests todays_ride_events

## RideEvents (60+ total)

Design requirements:
- Every ride with status 'to-pickup' or 'dropoff' must have matching events
- Pickup/dropoff EVENT PAIRS for bonus SQL:
  - 10+ pairs where duration > 60 minutes (counted in bonus)
  - 5+ pairs where duration < 60 minutes (excluded from bonus)
  - 2 pairs at EXACTLY 59 and 61 minutes (boundary test)
- For todays_ride_events testing:
  - 5+ events with created_at = NOW() - 1 hour (should appear)
  - 5+ events with created_at = NOW() - 48 hours (must NOT appear)
- 1 ride with 20+ events (mix of recent and old) — proves Prefetch filtering matters
- Distribute events so bonus SQL produces results for multiple months and drivers

## Bonus SQL Expected Output

The seed data must produce a report matching this pattern:
| Month | Driver | Count |
|-------|--------|-------|
| 2024-01 | Chris H | ≥2 |
| 2024-01 | Howard Y | ≥1 |
| 2024-02 | ... | ... |
| 2024-03 | ... | ... |

Verify by running: `make bonus-sql` after Docker is up.
```

**DO NOT COMMIT YET — Steps 3 and 4 are combined into a single commit.**

---

## Step 4: API + Feature Artifacts

Generate ALL remaining feature artifacts. Each one follows the same pattern: feature-brief.md + test-scenarios.md + any feature-specific files.

### `docs/artifacts/features/authentication/feature-brief.md`
- **Authentication (who is the user?):** Custom DRF authentication backend using BasicAuthentication. Looks up User by email, verifies password via Django's `check_password()`. The User model must implement `is_authenticated` property (returns `True`).
- **Permission (is the user allowed?):** Custom permission class checking `user.role == 'admin'` (exact match, case-sensitive). Applied globally via DRF settings.
- **DRF config:** Set both `DEFAULT_AUTHENTICATION_CLASSES` (BasicAuthentication) and `DEFAULT_PERMISSION_CLASSES` (IsAdminRole) in settings.py
- **Seed data:** Admin user seeded with known password (e.g., `adminpass123`) for curl/testing

### `docs/artifacts/features/authentication/test-scenarios.md`
```markdown
# Test Scenarios: Authentication

## Happy Path
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-001 | Admin accesses ride list | force_authenticate(admin_user) → GET /api/rides/ | 200 | P0 |
| T-002 | Admin authenticates via BasicAuth | HTTP BasicAuth with admin email:password → GET /api/rides/ | 200 | P0 |

## Error Cases
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-003 | Non-admin gets rejected | force_authenticate(rider_user) → GET /api/rides/ | 403 | P0 |
| T-004 | Unauthenticated request | No auth → GET /api/rides/ | 401 | P0 |
| T-005 | Wrong password | BasicAuth with admin email + wrong password → GET /api/rides/ | 401 | P0 |
| T-006 | Case-sensitive role check | user.role="Admin" (capital A) → GET /api/rides/ | 403 | P1 |
| T-007 | Driver cannot access | force_authenticate(driver_user) → GET /api/rides/ | 403 | P1 |
```

### `docs/artifacts/features/ride-list-api/api-contract.md`
```markdown
# API Contract: Ride List

## Endpoint
`GET /api/rides/`

## Authentication
Required. HTTP Basic Authentication with email and password.
Only users with `role='admin'` can access.

```bash
curl -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/
```

## Query Parameters
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| status | string | No | — | Filter: en-route, to-pickup, dropoff |
| rider_email | string | No | — | Filter: exact email match |
| sort_by | string | No | — | pickup_time or distance |
| latitude | float | Conditional | — | Required when sort_by=distance |
| longitude | float | Conditional | — | Required when sort_by=distance |
| page | int | No | 1 | Page number |
| page_size | int | No | 10 | Results per page (max 100) |

## Response: 200 Success
```json
{
  "count": 20,
  "next": "http://host/api/rides/?page=2",
  "previous": null,
  "results": [
    {
      "id_ride": 1,
      "status": "to-pickup",
      "id_rider": {
        "id_user": 5,
        "role": "rider",
        "first_name": "Alice",
        "last_name": "Rider",
        "email": "alice@wingz.com",
        "phone_number": "555-0010"
      },
      "id_driver": {
        "id_user": 2,
        "role": "driver",
        "first_name": "Chris",
        "last_name": "H",
        "email": "chris@wingz.com",
        "phone_number": "555-0001"
      },
      "pickup_latitude": 14.5995,
      "pickup_longitude": -90.5131,
      "dropoff_latitude": 14.6200,
      "dropoff_longitude": -90.5300,
      "pickup_time": "2024-01-15T08:00:00Z",
      "todays_ride_events": [
        {
          "id_ride_event": 42,
          "description": "Status changed to pickup",
          "created_at": "2024-01-15T08:00:00Z"
        }
      ]
    }
  ]
}
```

## Response: 400 Bad Request
```json
{"error": "latitude and longitude are required for distance sorting"}
```

## Response: 403 Forbidden
```json
{"detail": "You do not have permission to perform this action."}
```

## Examples
```bash
# Basic list (auth required)
curl -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/

# Filter + sort
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?status=to-pickup&sort_by=pickup_time"

# Distance sort
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131"

# Pagination
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?page=2&page_size=5"
```
```

### `docs/artifacts/features/ride-list-api/test-scenarios.md`
Minimum 12 scenarios covering:
- T-001: Happy path — returns rides with nested objects
- T-002: Empty list → 200 with empty results
- T-003: Pagination — page_size=5 limits results, count is total
- T-004: Page 2 returns remaining
- T-005: Filter by status
- T-006: Filter by rider_email
- T-007: Combined filters
- T-008: Sort by pickup_time ascending
- T-009: Sort by distance — nearest first (use known coordinates)
- T-010: Distance sort without coords → 400
- T-011: Distance sort + pagination
- T-012: Filter + sort compose together

### `docs/artifacts/features/ride-list-api/error-mapping.md`
| Condition | HTTP | Response |
|-----------|------|----------|
| Unauthenticated | 401/403 | DRF default |
| Non-admin role | 403 | DRF default |
| sort_by=distance without lat/lng | 400 | `{"error": "..."}` |
| Invalid lat/lng values | 400 | `{"error": "..."}` |
| Unhandled exception | 500 | `{"error": "Internal server error"}` |

### `docs/artifacts/features/performance/query-strategy.md`
```markdown
# Query Optimization Strategy

## Target: ≤ 3 SQL queries for the full ride list

### Query 1: COUNT (pagination)
```sql
SELECT COUNT(*) FROM rides [WHERE filters]
```
Generated automatically by DRF's PageNumberPagination.

### Query 2: Rides + Users (select_related)
```sql
SELECT rides.*, users_rider.*, users_driver.*
FROM rides
INNER JOIN users AS users_rider ON rides.id_rider = users_rider.id_user
INNER JOIN users AS users_driver ON rides.id_driver = users_driver.id_user
[WHERE filters]
[ORDER BY ...]
LIMIT page_size OFFSET ...
```
`select_related('id_rider', 'id_driver')` generates this single JOIN query.

### Query 3: Today's RideEvents (Prefetch)
```sql
SELECT ride_events.*
FROM ride_events
WHERE ride_events.id_ride IN (id1, id2, ..., idN)
  AND ride_events.created_at >= NOW() - INTERVAL 24 HOUR
```
`Prefetch('ride_events', queryset=RideEvent.objects.filter(created_at__gte=last_24h), to_attr='todays_ride_events')`

### Why this works
- `select_related` = SQL JOIN = 0 extra queries for User data
- `Prefetch` with filtered queryset = 1 extra query for events, batched
- `to_attr` stores results on the model instance, serializer reads directly
- NEVER use `ride.ride_events.all()` in a serializer — that triggers per-ride queries

### Verification
`test_performance.py` uses `CaptureQueriesContext` to assert ≤ 3 queries and inspect
the SQL to verify the Prefetch includes a `created_at` filter.
```

### `docs/artifacts/features/performance/test-scenarios.md`
- T-001: ≤ 3 queries for full ride list (assertNumQueries)
- T-002: Query count stable regardless of ride count (no N+1)
- T-003: Prefetch SQL contains created_at filter (inspect captured query)
- T-004: todays_ride_events only shows events from last 24h

### `docs/artifacts/features/sorting/distance-calculation.md`
```markdown
# Distance Calculation: Haversine Formula

## Formula
```
d = 6371 × 2 × arcsin(√(
    sin²((lat2 - lat1) / 2) +
    cos(lat1) × cos(lat2) × sin²((lng2 - lng1) / 2)
))
```
Result in kilometers.

## Implementation: RawSQL Annotation
```python
haversine = """
    6371 * 2 * ASIN(SQRT(
        POWER(SIN(RADIANS(pickup_latitude - %s) / 2), 2) +
        COS(RADIANS(%s)) * COS(RADIANS(pickup_latitude)) *
        POWER(SIN(RADIANS(pickup_longitude - %s) / 2), 2)
    ))
"""
qs = qs.annotate(distance=RawSQL(haversine, (lat, lat, lng)))
qs = qs.order_by('distance')
```

## Why RawSQL and not Django expressions?
Django doesn't have a built-in Haversine. Building one from Func/Sin/Cos is verbose
and less readable. RawSQL is pragmatic — it works on MySQL natively and on SQLite
with registered math functions.

## SQLite Compatibility for Tests
SQLite lacks RADIANS, SIN, COS, etc. We register them via a pytest autouse fixture:
```python
@pytest.fixture(autouse=True)
def _register_sqlite_math(db):
    from django.db import connection
    if connection.vendor == 'sqlite':
        import math
        connection.connection.create_function("RADIANS", 1, math.radians)
        # ... SIN, COS, ASIN, SQRT, POWER
```

## Test Verification Points
Use real coordinates with known distances:
- Zone 10, Guatemala City: 14.5995, -90.5131 (reference point)
- Zone 14: 14.5880, -90.4800 (~3.5 km from reference)
- Antigua: 14.5586, -90.7295 (~25 km from reference)
```

### `docs/artifacts/features/sorting/test-scenarios.md`
- T-001: Sort by pickup_time ASC
- T-002: Sort by distance — nearest first (known coordinates)
- T-003: Distance sort requires lat/lng → 400 without
- T-004: Distance sort + pagination
- T-005: Filter + distance sort compose

### `docs/artifacts/features/bonus-sql/query.sql`
The complete SQL query with inline comments explaining edge case handling (MIN/MAX for multiple events), boundary condition (> 60 minutes), and driver name format.

### `docs/artifacts/features/bonus-sql/test-scenarios.md`
- T-001: Query runs without errors on seed data
- T-002: Boundary — 59-minute trip NOT counted
- T-003: Boundary — 61-minute trip IS counted
- T-004: Output format matches sample (Month, Driver name format, Count)
- T-005: Multiple months and drivers appear in results

**COMMIT NOW:** `git add -A && git commit -m "docs: implementation specs and feature artifacts"`

---

## Quality Checklist

Before completing Phase 0, verify:

- [ ] `git log --oneline` shows 2 clean commits
- [ ] Every requirement from the assessment spec maps to a feature in the plan
- [ ] Test scenarios have concrete inputs and expected outputs (not vague descriptions)
- [ ] API contract covers all response codes (200, 400, 403, 500)
- [ ] Data models YAML matches schema SQL exactly (field names, types, constraints)
- [ ] Seed data spec explains WHY each row exists (not just fills space)
- [ ] Performance strategy documents exact query count target with SQL examples
- [ ] Distance calculation includes real GPS coordinates for verification
- [ ] Bonus SQL handles edge cases (multiple events, boundary at 60 min)
- [ ] Architecture decisions document tradeoffs, not just choices
- [ ] CLAUDE.md establishes conventions that Phase 1 and 2 will follow
- [ ] All artifacts are self-contained — Phase 1 can implement from them alone

## What Phase 1 Will Read

Phase 1 begins with:
```bash
cat CLAUDE.md
cat docs/artifacts/features/database-schema/data-models.yaml
cat docs/artifacts/features/database-schema/seed-data-spec.md
cat docs/artifacts/features/ride-list-api/api-contract.md
cat docs/artifacts/features/performance/query-strategy.md
cat docs/artifacts/features/sorting/distance-calculation.md
cat docs/artifacts/features/bonus-sql/query.sql
# Then reads test-scenarios.md files as it implements each module
```

Every artifact must be concrete enough that this works.
