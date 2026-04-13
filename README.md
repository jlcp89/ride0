# Wingz Ride Management API

Django REST API for the Wingz Python/Django Developer take-home. Admin-only endpoints for managing rides, drivers, riders, and ride events, with a paginated ride-list endpoint that supports filtering, sorting by pickup time, and sorting by distance from a GPS point.

## Quick start

The project runs on SQLite out of the box:

```bash
git clone <repo-url>
cd ride0/backend

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set once for the whole session — all manage.py commands will use SQLite
export USE_SQLITE=1

python manage.py migrate
python manage.py seed_db
python manage.py runserver
```

The server listens on `http://localhost:8000`. `seed_db` creates an admin user (`admin@wingz.com` / `adminpass123`), 3 riders, 3 drivers, 24 rides, and ~90 ride events.

> **MySQL option:** if you prefer MySQL, copy `backend/.env.example` to `backend/.env`, fill in the `DB_*` variables, and skip the `export USE_SQLITE=1` line. Everything else stays the same.

### Full stack (backend + frontend)

To run the complete system with the React admin UI:

```bash
# Terminal 1 — backend API (port 8000)
cd ride0/backend
export USE_SQLITE=1
python manage.py migrate
python manage.py seed_db
python manage.py runserver

# Terminal 2 — frontend dev server (port 5173)
cd ride1
npm install
npm run dev
```

Open `http://localhost:5173` in the browser and log in with `admin@wingz.com` / `adminpass123`. The Vite dev server proxies all `/api` requests to the backend on port 8000 automatically.

## Log in and call the API

```bash
# 1. Get a JWT access token
TOKEN=$(curl -sX POST http://localhost:8000/api/auth/login/ \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@wingz.com","password":"adminpass123"}' | jq -r .access_token)

# 2. Fetch the paginated ride list
curl -sH "Authorization: Bearer $TOKEN" \
  'http://localhost:8000/api/rides/?page_size=5' | jq
```

## API endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login/` | Exchange email + password for an access + refresh token |
| POST | `/api/auth/refresh/` | Refresh an access token |
| GET | `/api/auth/me/` | Return the authenticated user |
| POST | `/api/auth/logout/` | Stateless logout |
| GET | `/api/rides/` | Paginated ride list |
| POST | `/api/rides/` | Create a ride |
| GET / PUT / PATCH / DELETE | `/api/rides/{id}/` | Retrieve, update or delete a ride |
| GET | `/api/reports/trips-over-hour/` | Bonus SQL report as JSON |

All endpoints except `login` and `refresh` require `Authorization: Bearer <token>` and the `admin` role.

`GET /api/rides/` accepts these query parameters:

- `page`, `page_size` — pagination (default `page_size=10`, max `100`)
- `status` — filter by ride status (`en-route`, `pickup`, `dropoff`, …)
- `rider_email` — filter by the rider's email
- `sort_by=pickup_time` — sort ascending by pickup time
- `sort_by=distance&latitude=<float>&longitude=<float>` — sort ascending by great-circle distance from the given GPS point (400 if `latitude` or `longitude` is missing or invalid)

Every ride in the response includes the nested `id_rider`, `id_driver`, and a `todays_ride_events` array containing only ride events from the last 24 hours.

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Relevant variables:

| Variable | Purpose |
|---|---|
| `USE_SQLITE` | Set to `1` to force SQLite and ignore MySQL config |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | MySQL connection |
| `DJANGO_SECRET_KEY` | Django session signing key |
| `DJANGO_DEBUG` | Debug flag (`True` / `False`) |
| `JWT_SECRET_KEY` | JWT signing key (falls back to `DJANGO_SECRET_KEY` if unset) |

## Running the tests

```bash
cd backend
.venv/bin/ruff check .
.venv/bin/pytest -v
```

Expected: lint clean and 87 tests passing. Tests always run against in-memory SQLite and take under 15 seconds.

## Bonus SQL — trips longer than one hour, by month and driver

The spec asks for a raw SQL statement returning the count of trips that lasted more than one hour from pickup to dropoff, grouped by month and driver. The canonical query lives at [`backend/sql/bonus_report.sql`](backend/sql/bonus_report.sql) and is reproduced below.

A ride can legitimately have more than one `Status changed to pickup` event (the driver can toggle pickup off and back on), so the pickup subquery takes `MIN(created_at)` to pin the earliest pickup, and the dropoff subquery takes `MAX(created_at)` to pin the final dropoff. The `TIMESTAMPDIFF(MINUTE, ...) > 60` filter is strict, so a trip that lasts exactly 60 minutes is not counted.

```sql
SELECT
    DATE_FORMAT(pickup_ev.pickup_time, '%Y-%m')        AS `Month`,
    CONCAT(u.first_name, ' ', LEFT(u.last_name, 1))    AS `Driver`,
    COUNT(*)                                           AS `Count of Trips > 1 hr`
FROM rides r
INNER JOIN (
    SELECT id_ride, MIN(created_at) AS pickup_time
    FROM ride_events
    WHERE description = 'Status changed to pickup'
    GROUP BY id_ride
) pickup_ev ON pickup_ev.id_ride = r.id_ride
INNER JOIN (
    SELECT id_ride, MAX(created_at) AS dropoff_time
    FROM ride_events
    WHERE description = 'Status changed to dropoff'
    GROUP BY id_ride
) dropoff_ev ON dropoff_ev.id_ride = r.id_ride
INNER JOIN users u ON u.id_user = r.id_driver
WHERE TIMESTAMPDIFF(MINUTE, pickup_ev.pickup_time, dropoff_ev.dropoff_time) > 60
GROUP BY
    DATE_FORMAT(pickup_ev.pickup_time, '%Y-%m'),
    u.id_user, u.first_name, u.last_name
ORDER BY
    `Month` ASC,
    `Driver` ASC;
```

The same query is also exposed as `GET /api/reports/trips-over-hour/` for quick verification against the seed data.

## Design decisions

1. **Custom `User` model, not `AbstractUser`.** The spec defines `id_user` as the primary key and `role` as a VARCHAR, which neither `AbstractUser` nor `AbstractBaseUser` matches cleanly. Using a plain `models.Model` keeps the table identical to the spec. Trade-off: the project ships its own `JWTAuthentication`, `IsAdminRole` permission, and password hashing since Django's `contrib.auth` helpers don't apply.

2. **JWT Bearer authentication instead of HTTP Basic.** HTTP Basic would require the admin credentials to be embedded in any client that calls the API. A stateless JWT flow (`/api/auth/login/` returns `access` + `refresh`) keeps secrets out of the client at the cost of two extra endpoints and a small amount of refresh-on-401 logic.

3. **Haversine distance sort as a `RawSQL` annotation.** The spec forbids schema changes, so a materialized `distance` column is not an option, and a Python-side sort would require loading the entire ride table into memory and would break pagination. Annotating each row with `6371 * 2 * ASIN(SQRT(...))` at query time lets `ORDER BY distance LIMIT 10 OFFSET 20` run entirely in SQL. Math functions (`RADIANS`, `SIN`, `COS`, `ASIN`, `SQRT`, `POWER`) are native in MySQL; for SQLite tests, `conftest.py` registers them as Python UDFs via `connection.create_function`.

4. **Filtered `Prefetch(..., to_attr="todays_ride_events")` plus `select_related("id_rider", "id_driver")`.** Requirement 4 asks for a minimal SQL-query count on the ride-list endpoint. `select_related` joins both users into the main rides query, and the filtered `Prefetch` fetches only the last 24 hours of ride events in a single additional query. Together with the pagination `COUNT(*)`, the list endpoint takes exactly 3 queries regardless of page size. This contract is pinned in `tests/test_performance.py::TestQueryCount::test_max_3_queries` and a `test_no_n_plus_1` regression guard.
