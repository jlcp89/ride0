# Project Context: Wingz Ride Management API

*Last updated: 2026-04-10 (session 7). Updated by `/wrap` when project-level context changes.*

## Mission

Create a RESTful API using Django REST Framework for managing ride information. This is a take-home assessment for the AI Solutions Engineer (Full Stack) role at Wingz.

## Stakeholders

- **Primary users**: Wingz admin users (role=admin) accessing ride data via API
- **Evaluators**: Wingz engineering team reviewing the assessment
- **Maintainers**: Juan Carrillo

## Architecture Decisions

### ADR-001: Custom User model (plain Model, not AbstractUser)
- **Status**: accepted
- **Context**: Spec defines a User table with specific fields (id_user, role, password) that don't align with Django's built-in auth User
- **Decision**: Use plain `models.Model` with custom `EmailBasicAuthentication` instead of Django's auth system
- **Consequences**: Cannot use Django admin auth, `authenticate()`, or contrib.auth mixins. Passwords managed manually with `make_password`/`check_password`.

### ADR-002: Haversine distance sorting via RawSQL
- **Status**: accepted
- **Context**: Distance sorting must work with pagination on a VERY LARGE ride table. Cannot load all rides into Python.
- **Decision**: Use `RawSQL` annotation with Haversine formula for DB-level distance calculation
- **Consequences**: DB-agnostic math functions needed. SQLite tests require custom function registration in conftest.py.

### ADR-003: Filtered Prefetch for RideEvents
- **Status**: accepted
- **Context**: RideEvent table assumed VERY LARGE. API must return only last-24h events.
- **Decision**: Use `Prefetch` with `queryset=RideEvent.objects.filter(created_at__gte=last_24h)` and `to_attr="todays_ride_events"`
- **Consequences**: Keeps query count at 2-3 total. Never loads full event history.

### ADR-004: Ride status semantic model (trip-phase mapping)
- **Status**: accepted (session 7)
- **Context**: `requirement.md:39` lists `'en-route', 'pickup', 'dropoff'` as example values with no defined semantics. Seed data and UI were treating them inconsistently — `pickup` had been interpreted as both "scheduled upcoming" and "pickup just happened". The ambiguity produced incoherent demo data (pickup rides with 2024 timestamps, 18 events on a single ride, no tie between status and event log).
- **Decision**: Define each status as a real trip phase. Rename `pickup` → `to-pickup` (hyphenated, to match `en-route` and avoid URL encoding). Every ride has a canonical 5-step event lifecycle (`Ride requested` → `Ride accepted by driver` → `Status changed to pickup` → `Status changed to dropoff` → `Ride rated by rider`), filtered by status:
  - `to-pickup` = ride booked, driver accepted, rider NOT in car. pickup_time in the future. 2 events (request + accept).
  - `en-route` = trip in progress, rider in the car. pickup_time in the recent past. 3 events (+ pickup).
  - `dropoff` = trip completed, rider dropped off. pickup_time past. 5 events (+ dropoff + rating).
- **Consequences**: `"Status changed to pickup"` / `"Status changed to dropoff"` event descriptions are kept as spec-fixed literals even though they're semantically stale under the new status name (the status doesn't change "to pickup" — it changes from `to-pickup` to `en-route` at the pickup moment). Bonus SQL continues to filter on the exact descriptions. The rename touches ~55 locations across backend, tests, regression, frontend, CSS tokens, and docs, but requires no migration (status field is a plain `CharField` with no `choices=`).

## Active Goals

- Complete and polished Django REST API demonstrating senior-level Python/Django skills
- Clean commit history showing TDD progression
- Performance-optimized queries proving understanding of large-table constraints

## Constraints & Non-Negotiables

- Cannot modify table structure (per spec)
- Custom primary keys: `id_user`, `id_ride`, `id_ride_event`
- Admin-only API access (role-based, not Django auth groups)
- Maximum 3 DB queries for ride list endpoint
