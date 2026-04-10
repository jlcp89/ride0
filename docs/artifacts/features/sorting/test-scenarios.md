# Test Scenarios: Sorting

## Happy Path
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-001 | Sort by pickup_time ASC | GET /api/rides/?sort_by=pickup_time (rides seeded with varied pickup_times) | 200, rides ordered chronologically ascending | P0 |
| T-002 | Sort by distance nearest first | GET /api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131 (rides at Zone 10, Zone 14, Antigua) | 200, Zone 10 (~0km) first, Zone 14 (~3.5km) mid, Antigua (~25km) last | P0 |
| T-004 | Distance sort + pagination | GET /api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131&page_size=3 | 200, first 3 nearest rides returned, count reflects total rides | P1 |
| T-005 | Filter + distance sort compose | GET /api/rides/?status=pickup&sort_by=distance&latitude=14.5995&longitude=-90.5131 | 200, only pickup rides returned, sorted by distance nearest first | P1 |

## Error Cases
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-003 | Distance sort without coords | GET /api/rides/?sort_by=distance (no latitude/longitude params) | 400, `{"error": "latitude and longitude are required for distance sorting"}` | P0 |
