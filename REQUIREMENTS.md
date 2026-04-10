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

## Parking Lot

Future ideas and deferred items. Move to active requirements when ready.

- Frontend React dashboard for ride visualization
