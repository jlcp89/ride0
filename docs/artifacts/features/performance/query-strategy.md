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
