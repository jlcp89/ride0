# Project Context: Wingz Ride Management API

*Last updated: 2026-04-10. Updated by `/wrap` when project-level context changes.*

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

## Active Goals

- Complete and polished Django REST API demonstrating senior-level Python/Django skills
- Clean commit history showing TDD progression
- Performance-optimized queries proving understanding of large-table constraints

## Constraints & Non-Negotiables

- Cannot modify table structure (per spec)
- Custom primary keys: `id_user`, `id_ride`, `id_ride_event`
- Admin-only API access (role-based, not Django auth groups)
- Maximum 3 DB queries for ride list endpoint
