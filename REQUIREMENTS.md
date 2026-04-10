# Requirements

Work items decomposed using the 5-question framework. Use `/new-feature` to add items.

**Status values:** `not-started` | `in-progress` | `blocked` | `done`

---

## Ride List API

**Status:** done
**Created:** 2026-04-10
**Priority:** P0

### Problem
Need a paginated, filterable, sortable API for ride information with nested related objects.

### Acceptance Criteria
- [x] Returns rides with nested rider, driver, and todays_ride_events
- [x] Supports pagination (page, page_size)
- [x] Supports filtering by status and rider_email
- [x] Supports sorting by pickup_time and distance (Haversine)
- [x] Maximum 3 DB queries
- [x] Only returns RideEvents from last 24 hours

---

## Bonus SQL Report

**Status:** done
**Created:** 2026-04-10
**Priority:** P1

### Problem
Raw SQL for trips >1hr from pickup to dropoff, grouped by month and driver.

### Acceptance Criteria
- [x] Raw SQL in `backend/sql/bonus_report.sql`
- [x] Groups by month and driver
- [x] Calculates duration from pickup/dropoff RideEvents

---

## React Frontend (ride1)

**Status:** not-started
**Created:** 2026-04-10
**Priority:** P1
**Location:** `/home/jl2/work/wingz/ride1` (sibling to ride0, separate git repo)
**Implementation prompt:** `docs/prompts/PHASE_2_FRONTEND.md`

### Problem
Assessment benefits from a working frontend demo of the ride list API. Must deploy to the same EC2 instance currently running `wingz-api.service` without disrupting the backend.

### Acceptance Criteria
- [ ] Vite + React SPA scaffolded at `wingz/ride1/` as its own git repo
- [ ] `fetchRides()` service with HTTP Basic Auth via `VITE_*` env vars
- [ ] `RideTable` + `Pagination` + inline filter form in `App.jsx`
- [ ] Filter by status, filter by rider email, sort by pickup_time
- [ ] `npm run lint` and `npm run build` pass with zero warnings
- [ ] `deploy/nginx-wingz.conf` committed — serves static + proxies `/api/` to `:8000`
- [ ] `.github/workflows/deploy.yaml` builds on CI and ships `dist/` via SCP
- [ ] nginx installed on EC2, replacing the current port 80 → 8000 shortcut
- [ ] `wingz-api.service` systemd unit remains unchanged
- [ ] `ride0/tests/test_deployed_api.sh http://107.23.122.99` still passes post-cutover
- [ ] README with dev + production architecture diagrams, deployment section, and Basic Auth tradeoff callout

---

## Parking Lot

Future ideas and deferred items. Move to active requirements when ready.

- (empty)
