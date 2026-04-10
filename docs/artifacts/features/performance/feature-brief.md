# Feature: Performance Optimization

## Summary
Optimize the Ride List API to use at most 3 SQL queries regardless of result count.
Use `select_related` for rider/driver JOINs and `Prefetch` with a filtered queryset
for `todays_ride_events` (last 24 hours only). The RideEvent table is assumed very
large — we must never retrieve the full list of events. `todays_ride_events` serves
as the ride's RideEvents field (§3), constrained to last 24h per §4. See ADR-8.

## Requirements
- REQ-1: Maximum 3 DB queries for the full ride list response
  - Query 1: COUNT for pagination
  - Query 2: Rides + Users via select_related (SQL JOIN)
  - Query 3: Filtered RideEvents via Prefetch (last 24h only)
- REQ-2: `select_related('id_rider', 'id_driver')` to avoid N+1 on User lookups
- REQ-3: `Prefetch('ride_events', queryset=..., to_attr='todays_ride_events')` with
  `created_at__gte=now - 24h` filter to avoid loading full event history
- REQ-4: `to_attr='todays_ride_events'` stores prefetched results directly on model instance
- REQ-5: Never use `ride.ride_events.all()` in serializer — that triggers per-ride queries

## Dependencies
- Depends on: database-schema, ride-list-api
- Depended by: none (this is a cross-cutting optimization)

## Acceptance Criteria
- [ ] `assertNumQueries(3)` passes for ride list with riders, drivers, and events
- [ ] Query count is stable regardless of ride count (no N+1)
- [ ] Captured Prefetch SQL contains `created_at >=` filter
- [ ] `todays_ride_events` only includes events from the last 24 hours
- [ ] Events older than 24h are excluded even if they belong to a returned ride

## Technical Notes
- Use `CaptureQueriesContext` or `assertNumQueries` in tests
- Inspect captured SQL to verify Prefetch includes the `created_at` filter
- Serializer reads `todays_ride_events` from `to_attr`, not via a method field
- See `query-strategy.md` for exact SQL examples
