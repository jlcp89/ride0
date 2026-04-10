# Feature: Ride List API

## Summary
`GET /api/rides/` endpoint returning a paginated list of rides. Each ride includes
nested rider and driver User objects plus a `todays_ride_events` array (events from
the last 24 hours only). Supports filtering by ride status and rider email, and
sorting by pickup_time or distance from a given GPS coordinate.

## Requirements
- REQ-1: `GET /api/rides/` returns paginated ride list (DRF PageNumberPagination)
- REQ-2: Each ride includes nested `id_rider` and `id_driver` as full User objects
- REQ-3: Each ride includes `todays_ride_events` — RideEvents from last 24h only
  (satisfies §3 "related RideEvents" refined by §4 performance constraint; see ADR-8)
- REQ-4: Pagination with `page` and `page_size` query params (default 10, max 100)
- REQ-5: Filter by `status` query param (exact match: en-route, pickup, dropoff)
- REQ-6: Filter by `rider_email` query param (exact email match on rider)
- REQ-7: Sort by `pickup_time` via `sort_by=pickup_time` (DB ORDER BY, ascending)
- REQ-8: Sort by `distance` via `sort_by=distance&latitude=X&longitude=Y` (Haversine)
- REQ-9: `sort_by=distance` without latitude/longitude returns 400
- REQ-10: Filters and sorting compose together (e.g., status + distance sort)

## Dependencies
- Depends on: database-schema, authentication
- Depended by: performance (query optimization), sorting (distance calculation)

## Acceptance Criteria
- [ ] Authenticated admin gets 200 with paginated results
- [ ] Response includes `count`, `next`, `previous`, `results` keys
- [ ] Each ride in results has nested `id_rider` and `id_driver` objects
- [ ] Each ride has `todays_ride_events` array (may be empty)
- [ ] `?status=pickup` returns only rides with status "pickup"
- [ ] `?rider_email=alice@wingz.com` returns only rides where rider is Alice
- [ ] `?sort_by=pickup_time` returns rides ordered by pickup_time ASC
- [ ] `?sort_by=distance&latitude=X&longitude=Y` returns rides nearest-first
- [ ] `?sort_by=distance` without coords returns 400 with error message
- [ ] Filters + sort compose correctly
- [ ] Empty result set returns 200 with empty `results` array

## Technical Notes
- Use `ReadOnlyModelViewSet` with only `list` action
- Override `get_queryset()` for filtering and sorting logic
- Use `PageNumberPagination` subclass with `page_size_query_param = 'page_size'`
- Serializer uses nested `UserSerializer` for id_rider and id_driver
- `todays_ride_events` read from `to_attr` set by Prefetch in queryset
