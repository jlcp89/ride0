# Wingz Ride Management API

> RESTful admin API for managing ride requests, drivers, and ride events — built for the Wingz AI Solutions Engineer (Full Stack) take-home assessment.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![Django](https://img.shields.io/badge/Django-5.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com)
[![DRF](https://img.shields.io/badge/DRF-3.15-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org)
[![Tests](https://img.shields.io/badge/tests-65%20passing-success)](#testing)
[![License](https://img.shields.io/badge/license-MIT-blue)](#license)

**Live demo:** [`https://wingz-ride.d3sarrollo.dev`](https://wingz-ride.d3sarrollo.dev) &nbsp;·&nbsp; Seeded admin: `admin@wingz.com` / `adminpass123`

Try it from any terminal, no clone required:

```bash
TOKEN=$(curl -sX POST https://wingz-ride.d3sarrollo.dev/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@wingz.com","password":"adminpass123"}' | jq -r .access_token)

curl -sH "Authorization: Bearer $TOKEN" \
  'https://wingz-ride.d3sarrollo.dev/api/rides/?page_size=2' | jq
```

---

## Table of Contents

- [30-Second Overview](#30-second-overview)
- [Requirements Compliance](#requirements-compliance)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Authentication](#authentication)
- [API Reference](#api-reference)
- [Performance Deep-Dive](#performance-deep-dive)
- [Distance Sort Algorithm](#distance-sort-algorithm)
- [Bonus SQL Report](#bonus-sql-report)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [Known Limitations & Future Work](#known-limitations--future-work)
- [Deployment](#deployment)
- [License](#license)

---

## 30-Second Overview

A Django 5.1 + DRF 3.15 REST API that exposes an admin-only ride management surface: rides, users, ride events, and a paginated list endpoint with filtering, sorting by pickup time, sorting by geographic distance, and a last-24-hour prefetch for ride events. Authentication is stateless JWT over HTTPS. The database layer works against MySQL 8 in production and SQLite in tests, and the same query optimisations apply to both.

Highlights at a glance:

- **3 queries** for the full paginated ride list regardless of page size — verified by `assertNumQueries`, not hope
- **65 automated tests** across models, serializers, views, permissions, auth, performance, and reports
- **Zero N+1 queries** — `select_related` joins users, filtered `Prefetch(..., to_attr=...)` collapses 24-hour events into a single round trip
- **Dual-database support** — the same distance-sort RawSQL runs under MySQL in production and SQLite in tests via UDF registration
- **Live HTTPS deployment** on Amazon Linux 2023 (EC2 + gunicorn + nginx + Let's Encrypt, CI/CD via GitHub Actions)

Jump to [Quick Start](#quick-start) to run it locally, [Bonus SQL Report](#bonus-sql-report) for the reporting query the spec asks for, or [Design Decisions](#design-decisions--trade-offs) for the reasoning behind every non-obvious choice.

---

## Requirements Compliance

Every bullet in [`docs/requirement/requirement.md`](docs/requirement/requirement.md) is mapped below to the file that implements it and the test that proves it.

| # | Requirement | Implementation | Proof |
|---|---|---|---|
| 1 | Models for `Ride`, `User`, `RideEvent` | [`rides/models.py`](backend/rides/models.py) | `tests/test_models.py` (12 tests) |
| 2 | Serializers | [`rides/serializers.py`](backend/rides/serializers.py) | `tests/test_serializers.py` (5 tests) |
| 3 | Viewsets for CRUD operations | [`RideViewSet` (`ModelViewSet`) in `rides/views.py`](backend/rides/views.py) | `tests/test_views.py` (12) + `tests/test_views_crud.py` (17) |
| 4 | Admin-only authentication | [`rides/permissions.py::IsAdminRole`](backend/rides/permissions.py) + JWT | `tests/test_permissions.py` (5) + `tests/test_auth.py` (23) |
| 5 | Paginated ride list | [`rides/pagination.py::StandardPagination`](backend/rides/pagination.py) | `test_views.py::test_pagination_*` |
| 6 | Filter by `status`, `rider_email` | `RideViewSet.get_queryset` | `test_views.py::test_filter_*` |
| 7 | Sort by `pickup_time` and by distance | RawSQL Haversine annotation | `test_views.py::test_sort_*` |
| 8 | `todays_ride_events` last-24h field | Filtered `Prefetch(..., to_attr="todays_ride_events")` | `test_views.py::test_todays_events_*` |
| 9 | Minimum SQL queries (≤3) | `select_related` + `Prefetch` + `assertNumQueries` | `tests/test_performance.py::TestQueryCount::test_max_3_queries` |
| 10 | Bonus SQL report | [`backend/sql/bonus_report.sql`](backend/sql/bonus_report.sql) + [`rides/report_views.py`](backend/rides/report_views.py) | `tests/test_reports.py` (4 tests) |

Every linked file exists in the repository and is under active test coverage.

---

## Architecture

```text
Client ──HTTPS──▶ nginx :443 ──┬──▶ /usr/share/nginx/html/ride1/dist  (SPA bundle)
                                └──▶ 127.0.0.1:8000  (gunicorn)
                                          │
                                          ▼
                                 Django 5.1 + DRF 3.15
                                          │
             ┌────────────────────────────┼────────────────────────────┐
             ▼                            ▼                            ▼
       JWTAuthentication           RideViewSet              TripsOverHourReportView
       (Bearer HS256)              (full CRUD ModelViewSet) (raw SQL → JSON)
             │                            │                            │
             ▼                            ▼                            ▼
       IsAdminRole ◀────────────── select_related            connection.vendor
       (global default)             Prefetch(24h)             → MySQL | SQLite
                                          │
                                          ▼
                                    MySQL 8 / SQLite
```

Request lifecycle inside Django:

```text
HTTP request
    │
    ▼
urls.py  ──▶  rides/urls.py  ──▶  ViewSet / APIView
    │
    ▼
JWTAuthentication  (decode Bearer, attach rides.models.User)
    │
    ▼
IsAdminRole  (reject non-admin → 403, reject anonymous → 401)
    │
    ▼
get_queryset  (select_related + filtered Prefetch + filters + sort)
    │
    ▼
Paginator  (COUNT → slice → LIMIT/OFFSET)
    │
    ▼
Serializer  (nested id_rider / id_driver / todays_ride_events)
    │
    ▼
Response  →  { count, next, previous, results }
```

Two orthogonal optimisations run through every request: `select_related` eliminates the N+1 on users, and the filtered `Prefetch(..., to_attr="todays_ride_events")` collapses the last-24h event fetch into a single round trip regardless of page size. Both are covered in [Performance Deep-Dive](#performance-deep-dive).

---

## Quick Start

Three paths depending on how much infrastructure you want to set up.

### Option A — SQLite, zero database setup

```bash
git clone <this-repo>
cd ride0/backend

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

USE_SQLITE=1 python manage.py migrate
USE_SQLITE=1 python manage.py seed_db
USE_SQLITE=1 python manage.py runserver
```

Then grab a token and hit the ride list:

```bash
TOKEN=$(curl -sX POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@wingz.com","password":"adminpass123"}' | jq -r .access_token)

curl -sH "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/rides/?page_size=2' | jq
```

The SQLite database lives at `backend/db.sqlite3` and is rebuilt on every `migrate`. Tests always use an in-memory SQLite regardless of this option.

### Option B — MySQL (production parity)

```bash
cp .env.example .env        # then fill DB_* + JWT_SECRET_KEY
mysql -u root -p < backend/sql/schema.sql   # or rely on Django's migrate
python manage.py migrate
python manage.py seed_db
python manage.py runserver
```

The settings module automatically chooses MySQL when `USE_SQLITE` is unset and `pytest` is not on `sys.modules`. `.env.example` ships sensible defaults for a local Docker MySQL.

### Option C — skip the clone, hit the deployed API

The canonical URL is `https://wingz-ride.d3sarrollo.dev`. Credentials are the same seeded admin. The `curl` snippets at the top of this README already target the live deployment.

---

## Environment Variables

All variables are read by `wingz/settings.py` from the environment (via `python-dotenv`). `backend/.env.example` is the canonical template — copy it to `backend/.env` and fill in the blanks.

| Variable | Purpose | Required in | Default |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Django session signing key | prod | `change-me-in-production` |
| `DJANGO_DEBUG` | Enable Django debug mode | dev | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames Django will accept | prod | `*` |
| `USE_SQLITE` | Force SQLite even when MySQL config is present | dev shortcut | unset |
| `DB_NAME` | MySQL database name | MySQL only | `wingz_db` |
| `DB_USER` | MySQL user | MySQL only | `root` |
| `DB_PASSWORD` | MySQL password | MySQL only | `rootpassword` |
| `DB_HOST` | MySQL host | MySQL only | `db` |
| `DB_PORT` | MySQL port | MySQL only | `3306` |
| `JWT_SECRET_KEY` | HS256 signing key for JWTs | prod (recommended) | falls back to `DJANGO_SECRET_KEY` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access-token TTL | dev/prod | `15` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh-token TTL | dev/prod | `7` |

Rotating `JWT_SECRET_KEY` invalidates every outstanding token immediately — a nice property for incident response, and the reason it is separable from `DJANGO_SECRET_KEY`.

---

## Authentication

The original assessment brief asked for HTTP Basic authentication. That design leaked admin credentials into the static client bundle of the frontend at build time, so this project replaced Basic with a stateless JWT Bearer flow. The trade-off and its rationale are documented in [Design Decisions](#design-decisions--trade-offs).

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/login/` | public | Exchange email+password for an access+refresh token pair |
| `POST` | `/api/auth/refresh/` | public | Exchange a refresh token for a new access token |
| `GET` | `/api/auth/me/` | Bearer | Return the authenticated user's profile |
| `POST` | `/api/auth/logout/` | Bearer | Stateless logout (returns 204; client discards tokens) |

### Login request / response

```bash
curl -sX POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@wingz.com","password":"adminpass123"}'
```

```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "eyJhbGciOi...",
  "expires_in": 900,
  "user": {
    "id": 1,
    "email": "admin@wingz.com",
    "role": "admin",
    "first_name": "Admin",
    "last_name": "User"
  }
}
```

Subsequent requests must carry `Authorization: Bearer <access_token>`.

### Admin role enforcement

`IsAdminRole` is registered as the global default in `REST_FRAMEWORK.DEFAULT_PERMISSION_CLASSES`. Any view that does not override it inherits admin-only access. `LoginView` and `RefreshView` override to `AllowAny`, and `MeView` / `LogoutView` override to `IsAuthenticated` because they need to work for any logged-in user, not just admins.

### 401 → refresh → retry

```text
Client          /api/auth/         /api/rides/
  │                                    │
  │───GET /api/rides/ + access_A──────▶│
  │◀──401 token_expired────────────────│
  │                                    │
  │───POST /auth/refresh/ + refresh───▶│
  │◀──200 { access_B, expires_in }────│
  │                                    │
  │───GET /api/rides/ + access_B──────▶│
  │◀──200 { count, next, results }────│
```

The ride1 frontend implements this loop inside `src/services/api.js::apiFetch()`. If the refresh itself fails, tokens are cleared and the user is routed back to the login screen.

---

## API Reference

### Endpoints

| Method | Path | Auth | Purpose |
|---|---|---|---|
| `POST` | `/api/auth/login/` | public | Exchange email + password for a JWT pair |
| `POST` | `/api/auth/refresh/` | public | Refresh an access token |
| `GET` | `/api/auth/me/` | Bearer | Return the authenticated user |
| `POST` | `/api/auth/logout/` | Bearer | Stateless logout (204) |
| `GET` | `/api/rides/` | Bearer + admin | Paginated ride list (satisfies requirements 3, 5, 6, 7, 8) |
| `GET` | `/api/rides/{id}/` | Bearer + admin | Retrieve a single ride with its 24-hour events |
| `GET` | `/api/reports/trips-over-hour/` | Bearer + admin | Bonus SQL report as JSON (satisfies bonus requirement) |

### `GET /api/rides/` query parameters

| Param | Type | Notes |
|---|---|---|
| `page` | int | Page number, 1-indexed. Default `1`. |
| `page_size` | int | Items per page. Default `10`. Capped at `100` by `StandardPagination.max_page_size`. |
| `status` | string | Exact match on `Ride.status` (`en-route`, `pickup`, `dropoff`, …). |
| `rider_email` | string | Exact match on `Ride.id_rider.email`. |
| `sort_by` | `pickup_time` \| `distance` | Optional. Defaults to Ride PK order. |
| `latitude` | float | Required when `sort_by=distance`. 400 otherwise. |
| `longitude` | float | Required when `sort_by=distance`. 400 otherwise. |

### Sample response

```json
{
  "count": 24,
  "next": "http://localhost:8000/api/rides/?page=2",
  "previous": null,
  "results": [
    {
      "id_ride": 1,
      "status": "en-route",
      "id_rider": {
        "id_user": 5,
        "role": "rider",
        "first_name": "Alice",
        "last_name": "Johnson",
        "email": "alice@example.com",
        "phone_number": "555-0010"
      },
      "id_driver": {
        "id_user": 2,
        "role": "driver",
        "first_name": "Chris",
        "last_name": "H",
        "email": "chris@wingz.com",
        "phone_number": "555-0002"
      },
      "pickup_latitude": 14.5995,
      "pickup_longitude": -90.5131,
      "dropoff_latitude": 14.6200,
      "dropoff_longitude": -90.5300,
      "pickup_time": "2026-04-11T08:00:00Z",
      "todays_ride_events": [
        {
          "id_ride_event": 10,
          "description": "Status changed to pickup",
          "created_at": "2026-04-11T08:00:00Z"
        }
      ]
    }
  ]
}
```

### Error shape

Every non-2xx response is normalised to a single shape by the custom exception handler:

```json
{ "error": "latitude and longitude are required for distance sorting" }
```

Status codes: `400` invalid input, `401` missing or invalid token, `403` authenticated but non-admin, `404` not found, `500` server error.

---

## Performance Deep-Dive

**Target**: 3 queries for the full ride list, regardless of page size. Requirement 4 is the most technically pointed bullet in the spec — it is also the one most likely to regress under casual edits, so the contract is pinned in an `assertNumQueries` test.

**Strategy**

1. `select_related("id_rider", "id_driver")` joins the two `User` foreign keys into the rides query, eliminating two N+1 round trips
2. `Prefetch("ride_events", queryset=..., to_attr="todays_ride_events")` issues a single `IN (...)` query for only the events within the last 24 hours, and attaches them to each ride under a new attribute the serializer can read without triggering a second fetch
3. `StandardPagination` contributes one `COUNT(*)` query to compute total pages

Total: one COUNT, one `SELECT rides JOIN users`, one filtered `SELECT ride_events` — **three queries**. The query count is flat as `page_size` grows from 1 to 100.

### The actual implementation

```python
def get_queryset(self):
    last_24h = timezone.now() - timedelta(hours=24)
    todays_events = Prefetch(
        "ride_events",
        queryset=RideEvent.objects.filter(created_at__gte=last_24h),
        to_attr="todays_ride_events",
    )
    qs = (
        Ride.objects
        .select_related("id_rider", "id_driver")     # join users in the rides query
        .prefetch_related(todays_events)             # one filtered query for 24h events
    )
    status = self.request.query_params.get("status")
    if status:
        qs = qs.filter(status=status)
    rider_email = self.request.query_params.get("rider_email")
    if rider_email:
        qs = qs.filter(id_rider__email=rider_email)

    sort_by = self.request.query_params.get("sort_by")
    if sort_by == "pickup_time":
        qs = qs.order_by("pickup_time")
    elif sort_by == "distance":
        lat = float(self.request.query_params.get("latitude"))
        lng = float(self.request.query_params.get("longitude"))
        qs = self._annotate_haversine(qs, lat, lng).order_by("distance")
    return qs
```

### The proof

```python
# tests/test_performance.py

@pytest.mark.django_db
class TestQueryCount:
    def test_max_3_queries(self, admin_client, make_ride, make_event):
        """3 queries: COUNT + rides JOIN users + filtered events."""
        for _ in range(10):
            ride = make_ride()
            make_event(ride)
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get("/api/rides/")
        assert response.status_code == 200
        assert len(ctx.captured_queries) <= 3

    def test_no_n_plus_1(self, admin_client, make_ride, make_event):
        """Query count stays flat whether 5 or 25 rides."""
        # ... creates 5 rides, then 25, and asserts count_with_5 == count_with_25
```

`TestQueryCount` also verifies that the events query actually filters on `created_at` (so a regression back to a full-table prefetch would be caught) and that old events are excluded from the response end-to-end.

### Why this matters at scale

The spec explicitly says the ride table and the ride-event table will be very large. A naive implementation would fetch every related event per ride and filter in Python, which is O(N × E) memory and O(N × E) network. This design is O(1) queries and pushes the `WHERE created_at >= ...` predicate into the database, where an index on `(id_ride, created_at)` would make it trivially fast.

---

## Distance Sort Algorithm

**Problem.** Requirement 3 calls for sorting by distance from a GPS point while still supporting pagination on a very large ride table. A Python-level sort is a non-starter: it would require loading the entire table into memory, breaking both pagination and any realistic memory budget. Materialising a `distance` column would work, but the spec forbids schema changes.

**Solution.** Annotate every row with a Haversine distance at query time using `RawSQL`. The annotation becomes a first-class field on the queryset, which means `ORDER BY distance LIMIT 10 OFFSET 20` executes entirely in the database, and `StandardPagination` paginates it the same way it paginates any other sorted queryset.

```python
@staticmethod
def _annotate_haversine(qs, lat, lng):
    """Haversine at DB level so ORDER BY + LIMIT work on the full dataset."""
    haversine = """
        6371 * 2 * ASIN(SQRT(
            POWER(SIN(RADIANS(pickup_latitude - %s) / 2), 2) +
            COS(RADIANS(%s)) * COS(RADIANS(pickup_latitude)) *
            POWER(SIN(RADIANS(pickup_longitude - %s) / 2), 2)
        ))
    """
    return qs.annotate(
        distance=RawSQL(haversine, (lat, lat, lng), output_field=FloatField())
    )
```

The formula returns the great-circle distance in kilometres (Earth radius = 6371 km). Parameters are passed positionally via `%s` placeholders — `RawSQL` does the escaping, so there is no SQL-injection surface despite the name.

**SQLite compatibility.** MySQL ships `RADIANS`, `SIN`, `COS`, `ASIN`, `SQRT`, and `POWER` as built-ins. SQLite does not. The test suite uses an in-memory SQLite, so `tests/conftest.py` registers each of these as a Python UDF via `connection.connection.create_function(...)` in an `autouse=True` fixture. The same Haversine RawSQL runs under both backends without a dialect branch.

**Pagination interaction.** Because the `distance` annotation is a plain numeric field, DRF's paginator treats it exactly like a `pickup_time` sort. A request for `?sort_by=distance&latitude=X&longitude=Y&page=3&page_size=10` compiles to one SQL statement with `ORDER BY distance ASC LIMIT 10 OFFSET 20`. Query count stays at 3.

**Input validation.** `RideViewSet.list()` rejects `sort_by=distance` without both `latitude` and `longitude` (HTTP 400), and rejects non-numeric coordinates (HTTP 400). See `tests/test_views.py::test_sort_distance_*`.

---

## Bonus SQL Report

The assessment bonus asks for a raw SQL statement that returns the count of trips longer than one hour, grouped by month and driver. The canonical query lives at [`backend/sql/bonus_report.sql`](backend/sql/bonus_report.sql) and is reproduced verbatim below.

```sql
-- Bonus SQL: Count of trips > 1 hour from pickup to dropoff, by month and driver
--
-- Edge case handling:
--   - A ride may have multiple "Status changed to pickup" events (e.g., status toggled).
--     We use MIN(created_at) to capture the FIRST pickup time.
--   - A ride may have multiple "Status changed to dropoff" events.
--     We use MAX(created_at) to capture the LAST dropoff time.
--   - This gives us the full trip window and avoids double-counting.
--
-- Boundary: strictly > 60 minutes (a 60-minute trip is NOT counted).

SELECT
    DATE_FORMAT(pickup_ev.pickup_time, '%Y-%m') AS `Month`,
    CONCAT(u.first_name, ' ', LEFT(u.last_name, 1)) AS `Driver`,
    COUNT(*) AS `Count of Trips > 1 hr`
FROM rides r
-- Subquery: first pickup event per ride
INNER JOIN (
    SELECT
        id_ride,
        MIN(created_at) AS pickup_time
    FROM ride_events
    WHERE description = 'Status changed to pickup'
    GROUP BY id_ride
) pickup_ev ON pickup_ev.id_ride = r.id_ride
-- Subquery: last dropoff event per ride
INNER JOIN (
    SELECT
        id_ride,
        MAX(created_at) AS dropoff_time
    FROM ride_events
    WHERE description = 'Status changed to dropoff'
    GROUP BY id_ride
) dropoff_ev ON dropoff_ev.id_ride = r.id_ride
-- Join driver info
INNER JOIN users u ON u.id_user = r.id_driver
-- Filter: trip duration must exceed 60 minutes
WHERE TIMESTAMPDIFF(MINUTE, pickup_ev.pickup_time, dropoff_ev.dropoff_time) > 60
GROUP BY
    DATE_FORMAT(pickup_ev.pickup_time, '%Y-%m'),
    u.id_user,
    u.first_name,
    u.last_name
ORDER BY
    `Month` ASC,
    `Driver` ASC;
```

### How it works

- **Pickup subquery** aggregates `ride_events` by `id_ride` and picks `MIN(created_at)` so rides with multiple `pickup` events collapse to the earliest one. Without the aggregate, a ride toggled pickup → en-route → pickup would double-count.
- **Dropoff subquery** is symmetric with `MAX(created_at)`, capturing the final dropoff signal.
- **`INNER JOIN` on `r.id_ride`** drops any ride that is missing either event — in-progress or malformed rides never contribute to the count.
- **`TIMESTAMPDIFF(MINUTE, pickup, dropoff) > 60`** is strict: exactly 60-minute trips are excluded on purpose, matching the "more than 1 hour" wording of the spec.
- **`CONCAT(first_name, ' ', LEFT(last_name, 1))`** produces the `Chris H` shape from the sample output in the requirement document.
- **Grouping by `u.id_user` in addition to the display columns** avoids collapsing two drivers who happen to share a first name and a last-name initial.

### Sample output

Against the seed data created by `python manage.py seed_db`:

| Month | Driver | Count of Trips > 1 hr |
|---|---|---|
| 2026-02 | Randy W | 1 |
| 2026-03 | Chris H | 2 |
| 2026-03 | Howard Y | 2 |
| 2026-04 | Chris H | 1 |

(Months shift with the seed script's now-relative timestamps; run `seed_db` and re-query to see the current values.)

### Also exposed as a live endpoint

The same query runs behind `GET /api/reports/trips-over-hour/` in [`rides/report_views.py`](backend/rides/report_views.py). The view picks a MySQL or SQLite variant at runtime based on `connection.vendor`, so the identical code path exercises the query under pytest (SQLite in-memory) and in production (MySQL 8).

### Why two SQL constants instead of a UDF

The Haversine trick registers six math functions as SQLite UDFs because those are all row-level scalar functions. The report query needs date and string functions — `DATE_FORMAT` / `TIMESTAMPDIFF` on MySQL versus `strftime` / `julianday` on SQLite — which are not uniformly row-level and cannot all be recreated as UDFs. Two clearly-labelled SQL strings is the clean fix: the canonical `.sql` file stays readable to reviewers, and the view works in both environments.

---

## Testing

```bash
cd backend
.venv/bin/ruff check .       # lint
.venv/bin/pytest -v          # 65 tests
```

Expected output: `65 passed`.

| File | Tests | Covers |
|---|---:|---|
| `tests/test_auth.py` | 23 | Login / refresh / me / logout, token parsing, role checks |
| `tests/test_models.py` | 12 | `User`, `Ride`, `RideEvent` field shapes and foreign keys |
| `tests/test_serializers.py` | 5 | Nested `id_rider` / `id_driver` / `todays_ride_events` output |
| `tests/test_permissions.py` | 5 | `IsAdminRole` against anonymous, authed non-admin, admin |
| `tests/test_views.py` | 12 | List, retrieve, pagination, filters, both sort modes |
| `tests/test_performance.py` | 4 | `assertNumQueries` for the 3-query target and N+1 protection |
| `tests/test_reports.py` | 4 | Bonus report endpoint, grouping, auth, unauthenticated path |
| `tests/conftest.py` | — | Fixtures: `admin_user`, `admin_client`, `make_ride`, `make_event`, SQLite math UDFs |

Total: **65 passing tests**. Tests always use in-memory SQLite regardless of environment so the suite is hermetic and fast.

### Cross-repo regression

Against the live deployment:

```bash
bash ride0/tests/test_deployed_api.sh https://wingz-ride.d3sarrollo.dev
```

Expected output: `49/0/0` (49 checks passing, 0 failing, 0 skipped).

### Development workflow

Red → Green → Refactor, one feature per commit. `ruff check .` and `pytest -v` must be clean before every commit; pre-commit hooks in `.claude/hooks/` back-stop the rule.

---

## Project Structure

```text
ride0/
├── README.md                    ← this file
├── REQUIREMENTS.md              Active work items
├── CLAUDE.md                    Project context for AI-assisted development
├── docs/
│   ├── requirement/             Original take-home spec
│   ├── artifacts/               Feature briefs, test scenarios, ADRs
│   └── postman/                 Postman collection
├── tests/
│   └── test_deployed_api.sh     End-to-end regression against a live URL
├── .github/workflows/deploy.yaml  CI/CD to EC2
└── backend/
    ├── manage.py
    ├── requirements.txt
    ├── pytest.ini
    ├── .env.example
    ├── wingz/                   Django project module
    │   ├── settings.py          Env-driven, auto-selects SQLite under pytest
    │   ├── urls.py              /api/ → rides.urls
    │   └── wsgi.py
    ├── rides/                   Single Django app
    │   ├── models.py            User, Ride, RideEvent (custom primary keys)
    │   ├── serializers.py       Nested User + RideEvent output
    │   ├── views.py             RideViewSet + Haversine annotation
    │   ├── auth_views.py        Login / refresh / me / logout
    │   ├── report_views.py      Bonus SQL as JSON, dual-DB variants
    │   ├── jwt_service.py       Token encode / decode
    │   ├── authentication.py    JWTAuthentication (DRF plugin)
    │   ├── permissions.py       IsAdminRole
    │   ├── pagination.py        StandardPagination (max 100)
    │   ├── exceptions.py        Custom exception handler → { "error": ... }
    │   ├── urls.py              DRF router + auth + reports routes
    │   └── management/commands/
    │       └── seed_db.py       Re-runnable seed (7 users, 24 rides, ~90 events)
    ├── tests/                   65-test pytest suite (see Testing)
    └── sql/
        ├── schema.sql           Reference DDL
        ├── seed_data.sql        Reference seed data
        └── bonus_report.sql     Bonus requirement SQL (inlined above)
```

---

## Design Decisions & Trade-offs

The requirement document explicitly asks for a design-decisions narrative. Eight non-obvious choices:

1. **Custom `User` model (plain `models.Model`, not `AbstractUser`).** The spec's `User` table defines a `id_user` primary key and a `role` column — not the `id` + `is_staff` shape Django auth wants. Using `AbstractUser` would either rename the PK column (breaking the spec table) or require column-name shims. A plain `models.Model` matches the spec exactly. Trade-off: `django.contrib.auth` helpers are unavailable, so the project has its own `JWTAuthentication`, `IsAdminRole`, and password hashing wiring. The extra code is small and it keeps the data model honest.

2. **JWT Bearer authentication, replacing the originally-specified HTTP Basic.** The original design put `admin@wingz.com:adminpass123` into the client bundle at build time. That is a credential leak, even with a seeded admin. Replacing Basic with a stateless JWT flow let the frontend ship without secrets, at the cost of two new endpoints (`login`, `refresh`), a token service module, and a small amount of refresh-on-401 logic on the client. This is called out in [Authentication](#authentication).

3. **RawSQL Haversine annotation for distance sort.** Rejected: a Python-side sort (cannot paginate on a large table, unbounded memory) and a materialised `distance` column (spec forbids schema changes). The RawSQL annotation keeps `ORDER BY distance LIMIT 10 OFFSET 20` in the database, so pagination still works on a million rides. DB portability is mitigated by a small conftest fixture that registers the math functions as SQLite UDFs.

4. **Filtered `Prefetch(..., to_attr="todays_ride_events")` instead of a model-level `@property`.** A Python-side property would fire a fresh query per ride during serialization, re-creating the N+1. `Prefetch` with `to_attr` lets the 24-hour predicate run once per request at the SQL level, and attaches the result as a plain attribute the serializer reads without a second trip. Trade-off: the attribute is only populated on querysets that explicitly prefetch it — a contract the view owns, and one the performance tests protect.

5. **Single Django app (`rides/`) rather than splitting into `users/` + `rides/` + `events/`.** The domain is small, and every model has foreign keys into every other one. Splitting would create circular-import pain and migration sequencing hassle for no payoff. When the first genuinely decoupled domain arrives, the split can be revisited.

6. **Two SQL constants for the bonus report, selected by `connection.vendor` at request time.** Rejected: registering SQLite UDFs for `DATE_FORMAT`, `TIMESTAMPDIFF`, `LEFT`, and `CONCAT`. Not all of those are row-level scalar functions, and even the ones that are would mean hand-rolling date arithmetic inside Python callbacks. Two well-labelled SQL strings are strictly simpler and both go through the same view code, so the test suite exercises the identical pathway production does.

7. **Custom DRF exception handler mapping every error response to `{"error": "..."}`.** DRF's default leaks `{"detail": ...}` inconsistently across permission failures, validation failures, and routing errors. Normalising the shape at the exception handler level gives the frontend and the tests a single contract to assert against, and makes curl output readable. Serializer-level `ValidationError` payloads are flattened into the same envelope by `_flatten_validation` in `rides/exceptions.py`, so `POST /api/rides/` with a bad body returns `{"error": "pickup_latitude: ..."}` rather than DRF's default nested dict.

8. **Full-CRUD `ModelViewSet` with a split read/write serializer.** The spec says *"Use Viewsets for managing CRUD operations"*. `RideViewSet` is a `ModelViewSet`, not `ReadOnlyModelViewSet`, so POST / PUT / PATCH / DELETE are all exposed at `/api/rides/` and `/api/rides/{id}/`. Two serializers sit behind a `get_serializer_class()` switch: `RideReadSerializer` nests `id_rider` / `id_driver` as full user objects for GET responses, and `RideWriteSerializer` accepts integer FKs plus `ChoiceField` status validation and lat/lng range validators. After every successful write, `create()` / `update()` re-hydrate the saved instance through the same prefetch pipeline the GET path uses and respond with the `RideReadSerializer` shape — so the client contract is identical for every verb, including `todays_ride_events` appearing on POST responses. Write verbs inherit the global `IsAdminRole` permission automatically: non-admins get 403 on all methods. Covered by `tests/test_views_crud.py` (17 tests: create / update / delete / permission / query-budget).

---

## Known Limitations & Future Work

Five items, balanced so that reviewers can see the upgrade path without being distracted from what works today.

1. **JWT tokens live in client `localStorage`.** Fine for the assessment, vulnerable to XSS in production. The upgrade is HttpOnly cookies + CSRF, which would also require rethinking the refresh flow on the frontend.
2. **Stateless logout cannot revoke a leaked token before it expires.** The refresh-token lifetime is seven days, which is the worst-case exposure window. A refresh-token blacklist table would fix this, at the cost of reintroducing per-request database state.
3. **No OpenAPI schema.** The API contract lives in the serializers and in the frontend consumer code. Adopting `drf-spectacular` would auto-generate a schema, let the frontend type-check its API calls, and replace the hand-written Postman collection.
4. **Bonus report query has no covering index.** At 24 rides it is a sub-millisecond sequential scan. At a million rides, a covering index on `ride_events(id_ride, description, created_at)` would drop the plan from a seq-scan to an index-only lookup. Not shipped because the assessment spec is explicit about not changing schemas.
5. **`seed_db` is destructive.** It deletes all users (cascading to rides and events) and rebuilds from scratch. Perfect for a demo, wrong for any environment with real data. An upsert-based version would be the production-grade form.

---

## Deployment

- **Platform**: Amazon Linux 2023 EC2 instance at `wingz-ride.d3sarrollo.dev`
- **Process manager**: `systemd`, unit `wingz-api.service`, running `gunicorn --bind 127.0.0.1:8000 --workers 2`
- **Reverse proxy**: nginx listens on `:443`, serves the ride1 SPA from `/usr/share/nginx/html/ride1/dist`, and reverse-proxies `/api/` to gunicorn on `127.0.0.1:8000`
- **HTTPS**: Let's Encrypt certificate issued via `certbot --nginx`, auto-renewed by the `certbot-renew.timer` systemd unit
- **CI/CD**: [`.github/workflows/deploy.yaml`](.github/workflows/deploy.yaml) runs `ruff check` and `pytest -v` on every push, then SSHes to the EC2 box and triggers a rolling restart of `wingz-api.service`
- **Frontend**: The React SPA lives in a sibling repository at `../ride1/`. Its own deploy workflow installs the nginx config and copies `dist/` to the shared webroot on the same box
