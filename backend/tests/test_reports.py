"""Tests for the bonus trips-over-hour report endpoint."""
from datetime import datetime, timedelta

import pytest
from django.utils import timezone

ENDPOINT = "/api/reports/trips-over-hour/"


def _make_trip(make_ride, make_event, *, duration_minutes, pickup_at, driver_override=None):
    """Helper — create a ride with paired pickup+dropoff events."""
    ride = make_ride(driver_override=driver_override)
    make_event(
        ride,
        description="Status changed to pickup",
        created_at=pickup_at,
    )
    make_event(
        ride,
        description="Status changed to dropoff",
        created_at=pickup_at + timedelta(minutes=duration_minutes),
    )
    return ride


@pytest.mark.django_db
class TestTripsOverHourReport:
    """Contract tests for GET /api/reports/trips-over-hour/."""

    def test_long_trips_appear_short_trips_excluded(
        self, admin_client, make_ride, make_event
    ):
        """R-001: Trips > 60 min are counted; trips <= 60 min are not."""
        jan_15 = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        _make_trip(make_ride, make_event, duration_minutes=90, pickup_at=jan_15)
        _make_trip(make_ride, make_event, duration_minutes=45, pickup_at=jan_15)

        response = admin_client.get(ENDPOINT)

        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["month"] == "2024-01"
        assert results[0]["driver"] == "Chris H"
        assert results[0]["count"] == 1

    def test_groups_by_month_and_driver(
        self, admin_client, make_ride, make_event
    ):
        """R-002: Two long trips by the same driver in the same month collapse to one row."""
        jan_15 = timezone.make_aware(datetime(2024, 1, 15, 10, 0))
        jan_20 = timezone.make_aware(datetime(2024, 1, 20, 10, 0))
        _make_trip(make_ride, make_event, duration_minutes=90, pickup_at=jan_15)
        _make_trip(make_ride, make_event, duration_minutes=120, pickup_at=jan_20)

        response = admin_client.get(ENDPOINT)

        assert response.status_code == 200
        results = response.data["results"]
        assert len(results) == 1
        assert results[0]["month"] == "2024-01"
        assert results[0]["count"] == 2

    def test_non_admin_gets_403(self, api_client, non_admin_user):
        """R-003: Authenticated non-admin → 403."""
        api_client.force_authenticate(user=non_admin_user)

        response = api_client.get(ENDPOINT)

        assert response.status_code == 403

    def test_unauthenticated_gets_401(self, api_client):
        """R-004: No Authorization header → 401."""
        response = api_client.get(ENDPOINT)

        assert response.status_code == 401
