# Feature: Database Schema & Models

## Summary
Define the MySQL schema and Django ORM models for the three tables specified
in the assessment: User, Ride, and RideEvent. All primary keys, foreign keys,
field types, and table names must match the spec exactly.

## Requirements
- REQ-1: User table with id_user PK, role, first_name, last_name, email, phone_number (per spec §5)
  - Note: `password` field added beyond spec to support authentication (§2). The spec's
    User table defines 6 columns; password is a 7th column required so BasicAuth can
    verify credentials. See ADR-2.
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
