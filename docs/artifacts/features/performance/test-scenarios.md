# Test Scenarios: Performance

## Happy Path
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-001 | Query count within target | Authenticated admin → GET /api/rides/ with 10 seeded rides (each with rider, driver, events) | assertNumQueries ≤ 3 | P0 |
| T-002 | No N+1 — query count stable | GET /api/rides/ with 1 ride, then with 20 rides | Same query count for both (≤ 3) | P0 |
| T-003 | Prefetch SQL includes time filter | Capture SQL queries during GET /api/rides/ | Third query (Prefetch) contains `created_at >=` clause | P1 |
| T-004 | todays_ride_events filters correctly | Seed ride with events at now-1h and now-48h → GET /api/rides/ | todays_ride_events contains only the now-1h event, not the now-48h event | P0 |
