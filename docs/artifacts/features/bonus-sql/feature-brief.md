# Feature: Bonus SQL Report

## Summary
Raw SQL query that returns the count of trips taking more than 1 hour from pickup
to dropoff, grouped by month and driver. Trip duration is calculated from the time
difference between "Status changed to pickup" and "Status changed to dropoff"
RideEvent records for each ride.

## Requirements
- REQ-1: Raw SQL statement (not Django ORM)
- REQ-2: Count trips where duration > 60 minutes (strictly greater, not >=)
- REQ-3: Group by month (YYYY-MM format) and driver
- REQ-4: Driver name format: `"FirstName LastInitial"` (e.g., "Chris H")
- REQ-5: Handle edge case of multiple pickup/dropoff events per ride
  - Use MIN(created_at) for pickup events (first pickup)
  - Use MAX(created_at) for dropoff events (last dropoff)
- REQ-6: Output columns: Month, Driver, Count of Trips > 1 hr
- REQ-7: Order by month ASC, then driver name ASC

## Dependencies
- Depends on: database-schema (rides, ride_events, users tables)
- Depended by: none

## Acceptance Criteria
- [ ] Query executes without SQL errors on seeded database
- [ ] Trip of 59 minutes is NOT counted
- [ ] Trip of 61 minutes IS counted
- [ ] Output has three columns: Month, Driver, Count
- [ ] Month is formatted as YYYY-MM
- [ ] Driver name matches "FirstName L" format (first name + space + last initial)
- [ ] Results span multiple months and multiple drivers with seed data

## Technical Notes
- Use subqueries with MIN/MAX to handle multiple events per ride (ADR-6)
- `TIMESTAMPDIFF(MINUTE, pickup_time, dropoff_time) > 60` for MySQL
- Pickup event: `description = 'Status changed to pickup'`
- Dropoff event: `description = 'Status changed to dropoff'`
- See `query.sql` for the complete implementation
