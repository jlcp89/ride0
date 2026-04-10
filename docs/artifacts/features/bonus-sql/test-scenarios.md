# Test Scenarios: Bonus SQL

## Happy Path
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-001 | Query runs without errors | Execute query.sql against seeded database | No SQL errors, returns result rows | P0 |
| T-004 | Output format matches sample | Inspect column names and values | Columns: Month (YYYY-MM), Driver ("FirstName L"), Count (integer) | P0 |
| T-005 | Multiple months and drivers | Seed data spanning Jan-Apr 2024 with 3 drivers | Results contain rows for multiple months and multiple drivers | P1 |

## Boundary Cases
| ID | Scenario | Input | Expected | Priority |
|----|----------|-------|----------|----------|
| T-002 | 59-minute trip excluded | Seed ride with pickup-to-dropoff = 59 minutes | Ride does NOT appear in results | P0 |
| T-003 | 61-minute trip included | Seed ride with pickup-to-dropoff = 61 minutes | Ride IS counted in results | P0 |
