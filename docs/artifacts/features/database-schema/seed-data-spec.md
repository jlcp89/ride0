# Seed Data Specification

## Design Principle
Every row exists to test something specific. This is NOT random data.

## Users (7 total)

All users seeded with password hashed via Django's `make_password('adminpass123')` for the admin, and `make_password('userpass123')` for others.

| id | first_name | last_name | email | role | Purpose |
|----|-----------|-----------|-------|------|---------|
| 1 | Admin | User | admin@wingz.com | admin | Auth test — can access API (password: adminpass123) |
| 2 | Chris | H | chris@wingz.com | driver | Bonus SQL sample driver |
| 3 | Howard | Y | howard@wingz.com | driver | Bonus SQL sample driver |
| 4 | Randy | W | randy@wingz.com | driver | Bonus SQL sample driver |
| 5 | Alice | Rider | alice@wingz.com | rider | Filtering by rider email |
| 6 | Bob | Rider | bob@wingz.com | rider | Second rider for filter tests |
| 7 | Carol | Rider | carol@wingz.com | rider | Third rider |

**Note:** Driver names match the bonus SQL sample output (Chris H, Howard Y, Randy W).

## Rides (20+ total)

Design requirements:
- At least 5 per status (en-route, pickup, dropoff) — tests status filtering
- Multiple drivers and riders — tests email filtering
- GPS coords at KNOWN distances from reference point (14.5995, -90.5131 = Zone 10, Guatemala City):
  - 2-3 rides AT reference point (~0 km) — distance sort first position
  - 2-3 rides at Zone 14 (14.5880, -90.4800 ≈ 3.5 km) — middle
  - 2-3 rides at Antigua (14.5586, -90.7295 ≈ 25 km) — distance sort last position
- pickup_time spread across Jan-Apr 2024 — tests time sorting
- 2-3 rides with pickup_time = NOW() — tests todays_ride_events

## RideEvents (60+ total)

Design requirements:
- Every ride with status 'pickup' or 'dropoff' must have matching events
- Pickup/dropoff EVENT PAIRS for bonus SQL:
  - 10+ pairs where duration > 60 minutes (counted in bonus)
  - 5+ pairs where duration < 60 minutes (excluded from bonus)
  - 2 pairs at EXACTLY 59 and 61 minutes (boundary test)
- For todays_ride_events testing:
  - 5+ events with created_at = NOW() - 1 hour (should appear)
  - 5+ events with created_at = NOW() - 48 hours (must NOT appear)
- 1 ride with 20+ events (mix of recent and old) — proves Prefetch filtering matters
- Distribute events so bonus SQL produces results for multiple months and drivers

## Bonus SQL Expected Output

The seed data must produce a report matching this pattern:
| Month | Driver | Count |
|-------|--------|-------|
| 2024-01 | Chris H | ≥2 |
| 2024-01 | Howard Y | ≥1 |
| 2024-02 | ... | ... |
| 2024-03 | ... | ... |

Verify by running: `make bonus-sql` after Docker is up.
