# Phase 1 — Backend Implementation (TDD)

## Role

You are a **Senior Django/DRF Engineer** and **TDD specialist**. You write tests first, watch them fail, implement the minimum code to pass, then refactor. You never skip the Red step. Every decision is intentional. Your commit history reads like a story of progressive, thoughtful engineering.

## Mission

Implement the Wingz ride management REST API, consuming artifacts from Phase 0. Every module is built using strict **Red → Green → Refactor** TDD.

## Context

Read these files before writing ANY code:
- `./CLAUDE.md` — project conventions, verification loop, commit format
- `./docs/artifacts/features/database-schema/data-models.yaml` — exact Django model fields
- `./docs/artifacts/features/database-schema/seed-data-spec.md` — what seed data to create and why
- `./docs/artifacts/features/ride-list-api/api-contract.md` — request/response schemas
- `./docs/artifacts/features/performance/query-strategy.md` — the 2-3 query approach
- `./docs/artifacts/features/sorting/distance-calculation.md` — Haversine implementation
- `./docs/artifacts/features/bonus-sql/query.sql` — the raw SQL report
- `./docs/artifacts/features/*/test-scenarios.md` — test cases for each module

## Configuration

| Setting | Value |
|---------|-------|
| Backend path | `./backend/` |
| Python | 3.11+ |
| DB | MySQL 8.0 (SQLite for tests) |
| Test runner | pytest + pytest-django |
| Linter | ruff |

## Preflight

```bash
# Phase 0 must be complete
ls ./docs/artifacts/features/database-schema/data-models.yaml || echo "RUN PHASE 0 FIRST"
python3 --version  # 3.11+
```

---

## TDD Protocol

For EVERY module: write tests first (from `test-scenarios.md`), then implement the minimum code to make them pass, then clean up with ruff. Verify before each commit:

```bash
cd backend && pytest -v && ruff check . && cd ..
git add -A && git commit -m "<message>"
```

---

## Step 1: Project Scaffold

**Commit: "scaffold: Django project + rides app + test config"**

```bash
cd backend
django-admin startproject wingz .
python manage.py startapp rides
```

Structure:
```
backend/
├── wingz/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── rides/
│   ├── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── authentication.py
│   ├── permissions.py
│   ├── pagination.py
│   ├── exceptions.py
│   ├── urls.py
│   └── apps.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_permissions.py
│   ├── test_serializers.py
│   ├── test_views.py
│   └── test_performance.py
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── bonus_report.sql
├── manage.py
├── requirements.txt
├── pytest.ini
├── Dockerfile
└── .env.example
```

**`requirements.txt`:**
```
django==5.1.*
djangorestframework==3.15.*
pymysql==1.1.*
cryptography==44.*
gunicorn==23.*
python-dotenv==1.1.*
ruff==0.9.*
pytest==8.3.*
pytest-django==4.9.*
```

**`pytest.ini`:**
```ini
[pytest]
DJANGO_SETTINGS_MODULE = wingz.settings
python_files = tests/test_*.py
python_classes = Test*
python_functions = test_*
```

**`wingz/settings.py`** — key sections:
```python
import os
import sys

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'rest_framework',
    'rides',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rides.authentication.EmailBasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rides.pagination.StandardPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_PERMISSION_CLASSES': [
        'rides.permissions.IsAdminRole',
    ],
    'EXCEPTION_HANDLER': 'rides.exceptions.custom_exception_handler',
}

if 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'wingz_db'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {'charset': 'utf8mb4'},
        }
    }

APPEND_SLASH = True
ROOT_URLCONF = 'wingz.urls'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

**`tests/conftest.py`:**
```python
import math
import pytest
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.hashers import make_password

ADMIN_PASSWORD = "adminpass123"
USER_PASSWORD = "userpass123"


@pytest.fixture
def admin_user(db):
    from rides.models import User
    return User.objects.create(
        first_name="Admin", last_name="Tester",
        email="admin@wingz.com", role="admin", phone_number="555-0001",
        password=make_password(ADMIN_PASSWORD),
    )

@pytest.fixture
def non_admin_user(db):
    from rides.models import User
    return User.objects.create(
        first_name="Regular", last_name="User",
        email="user@wingz.com", role="rider", phone_number="555-0002",
        password=make_password(USER_PASSWORD),
    )

@pytest.fixture
def driver(db):
    from rides.models import User
    return User.objects.create(
        first_name="Chris", last_name="H",
        email="chris@wingz.com", role="driver", phone_number="555-0003",
        password=make_password(USER_PASSWORD),
    )

@pytest.fixture
def rider(db):
    from rides.models import User
    return User.objects.create(
        first_name="Rider", last_name="One",
        email="rider1@wingz.com", role="rider", phone_number="555-0004",
        password=make_password(USER_PASSWORD),
    )

@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client

@pytest.fixture
def make_ride(rider, driver):
    """Factory — creates rides with sensible defaults. Override any param."""
    from rides.models import Ride
    def _make(status="to-pickup", pickup_lat=14.6349, pickup_lng=-90.5069,
              dropoff_lat=14.6407, dropoff_lng=-90.5133,
              pickup_time=None, rider_override=None, driver_override=None):
        return Ride.objects.create(
            status=status,
            id_rider=rider_override or rider,
            id_driver=driver_override or driver,
            pickup_latitude=pickup_lat, pickup_longitude=pickup_lng,
            dropoff_latitude=dropoff_lat, dropoff_longitude=dropoff_lng,
            pickup_time=pickup_time or timezone.now(),
        )
    return _make

@pytest.fixture
def make_event():
    """Factory — creates ride events."""
    from rides.models import RideEvent
    def _make(ride, description="Status changed to pickup", created_at=None):
        return RideEvent.objects.create(
            id_ride=ride, description=description,
            created_at=created_at or timezone.now(),
        )
    return _make

@pytest.fixture(autouse=True)
def _register_sqlite_math(db):
    """Register math functions so Haversine RawSQL works in SQLite tests."""
    from django.db import connection
    if connection.vendor == 'sqlite':
        connection.connection.create_function("RADIANS", 1, math.radians)
        connection.connection.create_function("SIN", 1, math.sin)
        connection.connection.create_function("COS", 1, math.cos)
        connection.connection.create_function("ASIN", 1, math.asin)
        connection.connection.create_function("SQRT", 1, math.sqrt)
        connection.connection.create_function("POWER", 2, math.pow)
```

**`wingz/urls.py`:**
```python
from django.urls import path, include
urlpatterns = [
    path('api/', include('rides.urls')),
]
```

Create placeholder files (empty classes/pass) for all rides modules so imports work.

**`rides/exceptions.py`** — implement the custom exception handler now (it's wired in settings):
```python
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return Response(
            {"error": "Internal server error"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return response
```

**Verify:** `cd backend && pip install -r requirements.txt && pytest` → 0 tests, no errors.

**COMMIT.**

---

## Step 2: Models — TDD

**Commit: "models: User, Ride, RideEvent with custom PKs matching spec"**

**Read:** `docs/artifacts/features/database-schema/data-models.yaml`

### Red
Create `tests/test_models.py`:

Test that:
- Each model has correct `db_table` (users, rides, ride_events)
- Each model has correct PK name (id_user, id_ride, id_ride_event)
- User has all 6 fields from spec
- Ride FKs point to User with distinct related_names
- RideEvent FK points to Ride
- `__str__` returns something meaningful

See `docs/artifacts/features/database-schema/test-scenarios.md` for exact test cases.

Run `pytest` → FAIL.

### Green
Implement `rides/models.py` exactly matching `data-models.yaml`:
- Custom PKs with `AutoField(primary_key=True)`
- FKs with `db_column` matching spec column names
- `related_name` distinct for rider/driver FKs
- Index on `ride_events.created_at` via `Meta.indexes`

Run `pytest` → PASS. `ruff check .` → clean. **COMMIT.**

---

## Step 3: Schema + Seed Data

**Commit: "schema: MySQL DDL + intentional seed data for edge cases"**

**Read:** `docs/artifacts/features/database-schema/schema-spec.sql` and `seed-data-spec.md`

No TDD — SQL files.

### `sql/schema.sql`
Copy from `docs/artifacts/features/database-schema/schema-spec.sql`.

### `sql/seed_data.sql`
Follow `seed-data-spec.md` exactly. Every row has a purpose:
- Users: 1 admin, 3 drivers (Chris H, Howard Y, Randy W), 3 riders
- Rides: 20+ across statuses, GPS coords at known distances, varied months
- Events: 60+ with pickup/dropoff pairs for bonus SQL, boundary trips (59/61 min), recent + old events for todays_ride_events, one ride with 20+ events

**Verify:** Count rows, check variety. **COMMIT.**

---

## Step 4: Authentication — TDD

**Commit: "auth: admin-only permission class + BasicAuth with tests"**

**Read:** `docs/artifacts/features/authentication/test-scenarios.md`

### Red — `tests/test_permissions.py`
7 tests from the scenarios:
- Admin gets 200 (via force_authenticate)
- Admin authenticates via BasicAuth (HTTP header with email:password) → 200
- Non-admin gets 403
- Unauthenticated gets 401
- Wrong password gets 401
- Case-sensitive role check (role="Admin" ≠ "admin")
- Driver cannot access

### Green

**`rides/authentication.py`** — Custom BasicAuth using our User model:
```python
import base64
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password
from rides.models import User

class EmailBasicAuthentication(BaseAuthentication):
    """
    HTTP Basic Auth against our custom User model.
    Credentials: email:password (not username:password).
    """
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Basic '):
            return None
        try:
            decoded = base64.b64decode(auth_header[6:]).decode('utf-8')
            email, password = decoded.split(':', 1)
        except (ValueError, UnicodeDecodeError):
            raise AuthenticationFailed('Invalid basic auth header.')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed('Invalid credentials.')
        if not check_password(password, user.password):
            raise AuthenticationFailed('Invalid credentials.')
        return (user, None)
```

**`rides/permissions.py`:**
```python
class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return hasattr(request.user, 'role') and request.user.role == 'admin'
```

Wire minimal ViewSet + router so route exists. Also create `rides/pagination.py` and `rides/exceptions.py`.

Run `pytest` → PASS. **COMMIT.**

---

## Step 5: Serializers — TDD

**Commit: "serializers: nested rider/driver + todays_ride_events"**

### Red — `tests/test_serializers.py`
5 tests:
- `id_rider` is nested object (dict with first_name, email), not just an int
- `id_driver` is nested object
- `todays_ride_events` includes recent events
- `todays_ride_events` excludes old events (48h+ ago)
- All spec fields present in serialized output

### Green — `rides/serializers.py`
- `UserSerializer` (ModelSerializer, all 6 fields)
- `RideEventSerializer` (ModelSerializer)
- `RideSerializer` with nested UserSerializer for rider/driver, RideEventSerializer for `todays_ride_events` (reads from `to_attr` set by Prefetch)

Run `pytest` → PASS. **COMMIT.**

---

## Step 6: Ride List + Pagination + Filtering

**Commit: "api: ride list endpoint with pagination and filtering"**

**Read:** `docs/artifacts/features/ride-list-api/api-contract.md`

### Tests — `tests/test_views.py`
```python
@pytest.mark.django_db
class TestRideList:
    def test_returns_rides(self, admin_client, make_ride): ...
    def test_empty_list_returns_200(self, admin_client): ...
    def test_pagination_limits_results(self, admin_client, make_ride): ...
    def test_page_2_returns_remaining(self, admin_client, make_ride): ...
    def test_filter_by_status(self, admin_client, make_ride): ...
    def test_filter_by_rider_email(self, admin_client, make_ride): ...
    def test_combined_filters(self, admin_client, make_ride): ...
```

### Implementation — `rides/views.py`
`ReadOnlyModelViewSet` with `select_related` + `Prefetch` + filtering:
```python
class RideViewSet(viewsets.ReadOnlyModelViewSet):
    # ReadOnlyModelViewSet: spec only defines list/query operations
    serializer_class = RideSerializer
    permission_classes = [IsAdminRole]
    pagination_class = StandardPagination

    def get_queryset(self):
        last_24h = timezone.now() - timedelta(hours=24)
        todays_events = Prefetch(
            "ride_events",
            queryset=RideEvent.objects.filter(created_at__gte=last_24h),
            to_attr="todays_ride_events",
        )
        qs = (
            Ride.objects
            .select_related("id_rider", "id_driver")
            .prefetch_related(todays_events)
        )
        # Filtering
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        rider_email = self.request.query_params.get("rider_email")
        if rider_email:
            qs = qs.filter(id_rider__email=rider_email)
        return qs
```

Run `pytest` → PASS. **COMMIT.**

---

## Step 7: Sorting (pickup_time + Haversine distance)

**Commit: "sorting: pickup_time and Haversine distance with DB-level sort"**

**Read:** `docs/artifacts/features/sorting/distance-calculation.md`

### Tests — add to `TestRideList`:
- `test_sort_by_pickup_time` — create 3 rides with known times, verify order
- `test_sort_by_distance_nearest_first` — use real Guatemala City coords from the artifact
- `test_distance_sort_missing_coords_returns_400`
- `test_distance_sort_with_pagination`
- `test_filter_plus_distance_sort`

### Implementation — add to `get_queryset()` + `list()`:
- Add sorting logic to `get_queryset()` for pickup_time
- Override `list()` to validate lat/lng before queryset evaluation for distance sort
- Add `_annotate_haversine()` static method with RawSQL

```python
    @staticmethod
    def _annotate_haversine(qs, lat, lng):
        """
        Haversine at DB level so ORDER BY + LIMIT (pagination) work on full
        dataset. Loading all rides into Python would break pagination and
        require O(n) memory — unacceptable for large tables per spec.
        """
        haversine = """
            6371 * 2 * ASIN(SQRT(
                POWER(SIN(RADIANS(pickup_latitude - %s) / 2), 2) +
                COS(RADIANS(%s)) * COS(RADIANS(pickup_latitude)) *
                POWER(SIN(RADIANS(pickup_longitude - %s) / 2), 2)
            ))
        """
        return qs.annotate(distance=RawSQL(haversine, (lat, lat, lng)))
```

Run `pytest` → PASS. **COMMIT.**

---

## Step 8: Performance Proof

**Commit: "perf: assertNumQueries tests proving 2-3 query target"**

**Read:** `docs/artifacts/features/performance/query-strategy.md` and `test-scenarios.md`

### `tests/test_performance.py`
This is the most important test file. It proves you understood the hardest requirement.

```python
@pytest.mark.django_db
class TestQueryCount:
    """
    Spec: 'Retrieving the ride list with the related driver, rider, and
    RideEvents can be achieved with 2 queries (3 if you include the query
    required to get the total count used in Pagination).'
    """

    def test_max_3_queries(self, admin_client):
        """3 queries: COUNT + rides JOIN users + filtered events."""
        # Seed 10 rides with recent and old events
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get("/api/rides/")
        assert response.status_code == 200
        assert len(ctx.captured_queries) <= 3

    def test_no_n_plus_1(self, admin_client):
        """Query count stays at 3 whether 5 or 25 rides."""
        # Seed 5, capture count. Seed 20 more, capture count. Assert equal.

    def test_prefetch_filters_created_at(self, admin_client):
        """The ride_events query MUST filter on created_at."""
        with CaptureQueriesContext(connection) as ctx:
            admin_client.get("/api/rides/")
        event_sql = [q["sql"] for q in ctx.captured_queries if "ride_events" in q["sql"]]
        assert len(event_sql) == 1
        assert "created_at" in event_sql[0]

    def test_todays_events_only_recent(self, admin_client, make_ride, make_event):
        """End-to-end: old events excluded from response."""
        ride = make_ride()
        make_event(ride, "Fresh", timezone.now())
        make_event(ride, "Stale", timezone.now() - timedelta(hours=48))
        response = admin_client.get("/api/rides/")
        events = response.data["results"][0]["todays_ride_events"]
        assert len(events) == 1
        assert events[0]["description"] == "Fresh"
```

The ViewSet from previous steps should already pass. If not, adjust.

Run `pytest` → PASS. **COMMIT.**

---

## Step 9: Bonus SQL

**Commit: "bonus: raw SQL for trips > 1hr with edge case handling"**

**Read:** `docs/artifacts/features/bonus-sql/query.sql`

Create `sql/bonus_report.sql` — copy from artifact, ensure it includes:
- Inline comments explaining the logic
- MIN(pickup)/MAX(dropoff) for rides with multiple events
- `> 60` minutes (strict), not `>= 60`
- CONCAT format matching sample output

**COMMIT.**

---

## Step 10: Backend Dockerfile

**This will be committed together with Docker Compose in Phase 2.**

Create `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "wingz.wsgi:application"]
```

**DO NOT COMMIT YET — this ships with Phase 2's Docker Compose commit.**

---

## Final Verification

```bash
cd backend && pytest -v         # 30+ tests, all pass
cd backend && ruff check .      # 0 errors
cd backend && pytest --co -q    # count: ~34 tests
git log --oneline               # 10 clean commits since Phase 0
```

Expected:
- `test_models.py`: ~8 tests
- `test_permissions.py`: ~7 tests (including BasicAuth tests)
- `test_serializers.py`: ~5 tests
- `test_views.py`: ~12 tests (list, pagination, filters, sorts)
- `test_performance.py`: ~4 tests
- **Total: ~36 tests**
