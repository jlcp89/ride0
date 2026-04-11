"""Reports endpoints.

Currently a single endpoint that exposes the bonus "trips > 1 hour" SQL
report (`sql/bonus_report.sql`) as JSON so the frontend can render it as a
table. The view runs a raw SQL query via `cursor.execute()` and returns the
rows grouped by month and driver.

The canonical `.sql` file stays the single source of truth for reviewers
running the report directly against MySQL. This module embeds the same
query as a module-level constant plus a SQLite-compatible variant so the
test suite (which always runs on in-memory SQLite) exercises the same
code path as production.
"""
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


# MySQL variant — mirrors sql/bonus_report.sql verbatim so reviewers can
# diff the two. Uses DATE_FORMAT / TIMESTAMPDIFF / LEFT / CONCAT.
_SQL_MYSQL = """
SELECT
    DATE_FORMAT(pickup_ev.pickup_time, '%%Y-%%m') AS month_label,
    CONCAT(u.first_name, ' ', LEFT(u.last_name, 1)) AS driver_name,
    COUNT(*) AS trips_count
FROM rides r
INNER JOIN (
    SELECT id_ride, MIN(created_at) AS pickup_time
    FROM ride_events
    WHERE description = 'Status changed to pickup'
    GROUP BY id_ride
) pickup_ev ON pickup_ev.id_ride = r.id_ride
INNER JOIN (
    SELECT id_ride, MAX(created_at) AS dropoff_time
    FROM ride_events
    WHERE description = 'Status changed to dropoff'
    GROUP BY id_ride
) dropoff_ev ON dropoff_ev.id_ride = r.id_ride
INNER JOIN users u ON u.id_user = r.id_driver
WHERE TIMESTAMPDIFF(MINUTE, pickup_ev.pickup_time, dropoff_ev.dropoff_time) > 60
GROUP BY
    DATE_FORMAT(pickup_ev.pickup_time, '%%Y-%%m'),
    u.id_user,
    u.first_name,
    u.last_name
ORDER BY
    month_label ASC,
    driver_name ASC
"""

# SQLite variant — same query shape with vendor-specific date and string
# functions. strftime replaces DATE_FORMAT, (julianday(b) - julianday(a))
# replaces TIMESTAMPDIFF(MINUTE, ...), substr replaces LEFT, and `||`
# replaces CONCAT.
_SQL_SQLITE = """
SELECT
    strftime('%Y-%m', pickup_ev.pickup_time) AS month_label,
    u.first_name || ' ' || substr(u.last_name, 1, 1) AS driver_name,
    COUNT(*) AS trips_count
FROM rides r
INNER JOIN (
    SELECT id_ride, MIN(created_at) AS pickup_time
    FROM ride_events
    WHERE description = 'Status changed to pickup'
    GROUP BY id_ride
) pickup_ev ON pickup_ev.id_ride = r.id_ride
INNER JOIN (
    SELECT id_ride, MAX(created_at) AS dropoff_time
    FROM ride_events
    WHERE description = 'Status changed to dropoff'
    GROUP BY id_ride
) dropoff_ev ON dropoff_ev.id_ride = r.id_ride
INNER JOIN users u ON u.id_user = r.id_driver
WHERE (julianday(dropoff_ev.dropoff_time) - julianday(pickup_ev.pickup_time)) * 24 * 60 > 60
GROUP BY
    strftime('%Y-%m', pickup_ev.pickup_time),
    u.id_user,
    u.first_name,
    u.last_name
ORDER BY
    month_label ASC,
    driver_name ASC
"""


class TripsOverHourReportView(APIView):
    """GET /api/reports/trips-over-hour/ — bonus report as JSON.

    Inherits JWT authentication and the `IsAdminRole` permission class
    from the `REST_FRAMEWORK` defaults in settings.py, so no explicit
    overrides are needed. Anonymous callers get 401, non-admin callers
    get 403.
    """

    def get(self, request):
        sql = _SQL_SQLITE if connection.vendor == "sqlite" else _SQL_MYSQL
        with connection.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
        results = [
            {"month": row[0], "driver": row[1], "count": row[2]}
            for row in rows
        ]
        return Response({"results": results}, status=status.HTTP_200_OK)
