# Feature: Sorting

## Summary
Support sorting rides by `pickup_time` (DB ORDER BY) and by `distance` from a
given GPS coordinate (Haversine formula via RawSQL annotation). Both sort modes
must execute in the database — not Python — so pagination works correctly on
large tables.

## Requirements
- REQ-1: `sort_by=pickup_time` uses `queryset.order_by('pickup_time')` (ascending)
- REQ-2: `sort_by=distance` requires `latitude` and `longitude` query params
- REQ-3: Distance calculated via Haversine formula as a `RawSQL` annotation
  - Result in kilometers, annotated as `distance` field on queryset
  - `queryset.order_by('distance')` for nearest-first ordering
- REQ-4: Missing latitude/longitude when `sort_by=distance` returns 400
- REQ-5: Sorting composes with filtering (status, rider_email) and pagination
- REQ-6: SQLite compatibility for tests via registered math functions (RADIANS, SIN, COS, ASIN, SQRT, POWER)

## Dependencies
- Depends on: database-schema, ride-list-api
- Depended by: none

## Acceptance Criteria
- [ ] `sort_by=pickup_time` returns rides in chronological ascending order
- [ ] `sort_by=distance` with known coords returns rides nearest-first
  - Zone 10 (14.5995, -90.5131) ≈ 0 km — first
  - Zone 14 (14.5880, -90.4800) ≈ 3.5 km — middle
  - Antigua (14.5586, -90.7295) ≈ 25 km — last
- [ ] `sort_by=distance` without lat/lng returns 400 with descriptive error
- [ ] Distance sort + pagination returns correct page of nearest rides
- [ ] Filter + distance sort compose (e.g., only pickup rides sorted by distance)

## Technical Notes
- Haversine formula: `6371 * 2 * ASIN(SQRT(...))` — result in km
- `RawSQL` annotation avoids verbose Django Func expressions
- SQLite lacks RADIANS/SIN/COS — pytest autouse fixture registers them via `connection.connection.create_function()`
- See `distance-calculation.md` for formula details and SQLite fixture code
