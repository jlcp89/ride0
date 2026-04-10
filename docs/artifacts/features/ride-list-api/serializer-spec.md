# Serializer Specification

Serializers for JSON serialization/deserialization per §1.
Three serializers: `UserSerializer`, `RideEventSerializer`, `RideSerializer`.

## UserSerializer

Read-only nested serializer for rider/driver objects.

| Field | Source | Type | Notes |
|-------|--------|------|-------|
| id_user | model PK | int | |
| role | model field | string | |
| first_name | model field | string | |
| last_name | model field | string | |
| email | model field | string | |
| phone_number | model field | string | |

**Excluded:** `password` — never exposed in API responses.

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id_user', 'role', 'first_name', 'last_name', 'email', 'phone_number']
```

## RideEventSerializer

Read-only nested serializer for todays_ride_events.

| Field | Source | Type | Notes |
|-------|--------|------|-------|
| id_ride_event | model PK | int | |
| description | model field | string | |
| created_at | model field | datetime | ISO 8601 format |

**Excluded:** `id_ride` — redundant when nested under the parent Ride.

```python
class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ['id_ride_event', 'description', 'created_at']
```

## RideSerializer

Main serializer for the Ride List API response.

| Field | Source | Type | Notes |
|-------|--------|------|-------|
| id_ride | model PK | int | |
| status | model field | string | 'en-route', 'pickup', 'dropoff' |
| id_rider | FK → User | nested UserSerializer | Full User object, not integer ID |
| id_driver | FK → User | nested UserSerializer | Full User object, not integer ID |
| pickup_latitude | model field | float | |
| pickup_longitude | model field | float | |
| dropoff_latitude | model field | float | |
| dropoff_longitude | model field | float | |
| pickup_time | model field | datetime | ISO 8601 format |
| todays_ride_events | Prefetch to_attr | list[RideEventSerializer] | Last 24h only; see ADR-8, performance/query-strategy.md |

**Key implementation detail:** `todays_ride_events` reads directly from the `to_attr`
set by the Prefetch in the viewset's `get_queryset()`. It must NOT trigger a new
query — use `serializers.SerializerMethodField` or `ListSerializer` reading from the
prefetched attribute, never `obj.ride_events.filter(...)`.

```python
class RideSerializer(serializers.ModelSerializer):
    id_rider = UserSerializer(read_only=True)
    id_driver = UserSerializer(read_only=True)
    todays_ride_events = RideEventSerializer(many=True, read_only=True)

    class Meta:
        model = Ride
        fields = [
            'id_ride', 'status',
            'id_rider', 'id_driver',
            'pickup_latitude', 'pickup_longitude',
            'dropoff_latitude', 'dropoff_longitude',
            'pickup_time', 'todays_ride_events',
        ]
```
