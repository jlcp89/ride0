# Test Scenarios: Ride List API

## Happy Path
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-001 | Returns rides with nested objects | Authenticated admin → GET /api/rides/ (seeded data) | 200, results contain rides with nested id_rider, id_driver User objects and todays_ride_events array | P0 |
| T-002 | Empty list returns 200 | Authenticated admin → GET /api/rides/ (no rides in DB) | 200, `{"count": 0, "results": []}` | P0 |
| T-003 | Pagination limits results | GET /api/rides/?page_size=5 (20 rides seeded) | 200, results has 5 items, count=20, next is not null | P0 |
| T-004 | Page 2 returns remaining | GET /api/rides/?page=2&page_size=5 (20 rides) | 200, results has 5 items, previous is not null | P0 |
| T-005 | Filter by status | GET /api/rides/?status=to-pickup | 200, all returned rides have status="to-pickup" | P0 |
| T-006 | Filter by rider_email | GET /api/rides/?rider_email=alice@wingz.com | 200, all returned rides have id_rider.email="alice@wingz.com" | P0 |
| T-007 | Combined filters | GET /api/rides/?status=to-pickup&rider_email=alice@example.com | 200, all rides match both status AND rider email | P1 |
| T-008 | Sort by pickup_time | GET /api/rides/?sort_by=pickup_time | 200, rides ordered by pickup_time ascending | P0 |
| T-009 | Sort by distance nearest first | GET /api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131 | 200, Zone 10 rides (~0km) first, Zone 14 (~3.5km) mid, Antigua (~25km) last | P0 |
| T-011 | Distance sort + pagination | GET /api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131&page_size=3 | 200, first 3 nearest rides, count reflects total | P1 |
| T-012 | Filter + sort compose | GET /api/rides/?status=to-pickup&sort_by=pickup_time | 200, only to-pickup rides, ordered by pickup_time | P1 |

## Error Cases
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-010 | Distance sort without coords | GET /api/rides/?sort_by=distance | 400, `{"error": "latitude and longitude are required for distance sorting"}` | P0 |
