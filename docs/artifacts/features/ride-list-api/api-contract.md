# API Contract: Ride List

## Endpoint
`GET /api/rides/`

## Authentication
Required. HTTP Basic Authentication with email and password.
Only users with `role='admin'` can access.

```bash
curl -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/
```

## Query Parameters
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| status | string | No | — | Filter: en-route, pickup, dropoff |
| rider_email | string | No | — | Filter: exact email match |
| sort_by | string | No | — | pickup_time or distance |
| latitude | float | Conditional | — | Required when sort_by=distance |
| longitude | float | Conditional | — | Required when sort_by=distance |
| page | int | No | 1 | Page number |
| page_size | int | No | 10 | Results per page (max 100) |

## Response: 200 Success
```json
{
  "count": 20,
  "next": "http://host/api/rides/?page=2",
  "previous": null,
  "results": [
    {
      "id_ride": 1,
      "status": "pickup",
      "id_rider": {
        "id_user": 5,
        "role": "rider",
        "first_name": "Alice",
        "last_name": "Rider",
        "email": "alice@wingz.com",
        "phone_number": "555-0010"
      },
      "id_driver": {
        "id_user": 2,
        "role": "driver",
        "first_name": "Chris",
        "last_name": "H",
        "email": "chris@wingz.com",
        "phone_number": "555-0001"
      },
      "pickup_latitude": 14.5995,
      "pickup_longitude": -90.5131,
      "dropoff_latitude": 14.6200,
      "dropoff_longitude": -90.5300,
      "pickup_time": "2024-01-15T08:00:00Z",
      "todays_ride_events": [
        {
          "id_ride_event": 42,
          "description": "Status changed to pickup",
          "created_at": "2024-01-15T08:00:00Z"
        }
      ]
    }
  ]
}
```

## Response: 400 Bad Request
```json
{"error": "latitude and longitude are required for distance sorting"}
```

## Response: 403 Forbidden
```json
{"detail": "You do not have permission to perform this action."}
```

## Examples
```bash
# Basic list (auth required)
curl -u admin@wingz.com:adminpass123 http://localhost:8000/api/rides/

# Filter + sort
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?status=pickup&sort_by=pickup_time"

# Distance sort
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131"

# Pagination
curl -u admin@wingz.com:adminpass123 "http://localhost:8000/api/rides/?page=2&page_size=5"
```
