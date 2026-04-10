-- Bonus SQL: Count of trips > 1 hour from pickup to dropoff, by month and driver
--
-- Edge case handling:
--   - A ride may have multiple "Status changed to pickup" events (e.g., status toggled).
--     We use MIN(created_at) to capture the FIRST pickup time.
--   - A ride may have multiple "Status changed to dropoff" events.
--     We use MAX(created_at) to capture the LAST dropoff time.
--   - This gives us the full trip window and avoids double-counting.
--
-- Boundary: strictly > 60 minutes (a 60-minute trip is NOT counted).

SELECT
    DATE_FORMAT(pickup_ev.pickup_time, '%Y-%m') AS `Month`,
    CONCAT(u.first_name, ' ', LEFT(u.last_name, 1)) AS `Driver`,
    COUNT(*) AS `Count of Trips > 1 hr`
FROM rides r
-- Subquery: first pickup event per ride
INNER JOIN (
    SELECT
        id_ride,
        MIN(created_at) AS pickup_time
    FROM ride_events
    WHERE description = 'Status changed to pickup'
    GROUP BY id_ride
) pickup_ev ON pickup_ev.id_ride = r.id_ride
-- Subquery: last dropoff event per ride
INNER JOIN (
    SELECT
        id_ride,
        MAX(created_at) AS dropoff_time
    FROM ride_events
    WHERE description = 'Status changed to dropoff'
    GROUP BY id_ride
) dropoff_ev ON dropoff_ev.id_ride = r.id_ride
-- Join driver info
INNER JOIN users u ON u.id_user = r.id_driver
-- Filter: trip duration must exceed 60 minutes
WHERE TIMESTAMPDIFF(MINUTE, pickup_ev.pickup_time, dropoff_ev.dropoff_time) > 60
GROUP BY
    DATE_FORMAT(pickup_ev.pickup_time, '%Y-%m'),
    u.id_user,
    u.first_name,
    u.last_name
ORDER BY
    `Month` ASC,
    `Driver` ASC;
