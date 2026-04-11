import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from rides.models import Ride, RideEvent


def _payload(rider, driver, **overrides):
    """Build a valid write payload with sensible defaults, overridable kwargs."""
    body = {
        "status": "to-pickup",
        "id_rider": rider.id_user,
        "id_driver": driver.id_user,
        "pickup_latitude": 14.6349,
        "pickup_longitude": -90.5069,
        "dropoff_latitude": 14.6407,
        "dropoff_longitude": -90.5133,
        "pickup_time": timezone.now().isoformat(),
    }
    body.update(overrides)
    return body


@pytest.mark.django_db
class TestRideCreate:
    def test_admin_creates_ride_201(self, admin_client, rider, driver):
        """T-101: Admin POSTs valid body → 201 with nested rider and empty events."""
        response = admin_client.post(
            "/api/rides/", _payload(rider, driver), format="json"
        )
        assert response.status_code == 201
        assert isinstance(response.data["id_rider"], dict)
        assert response.data["id_rider"]["email"] == rider.email
        assert isinstance(response.data["id_driver"], dict)
        assert response.data["todays_ride_events"] == []
        assert response.data["status"] == "to-pickup"

    def test_create_persists_to_db(self, admin_client, rider, driver):
        """T-102: POST creates a row reachable via ORM."""
        response = admin_client.post(
            "/api/rides/", _payload(rider, driver), format="json"
        )
        assert response.status_code == 201
        ride = Ride.objects.get(pk=response.data["id_ride"])
        assert ride.status == "to-pickup"
        assert ride.id_rider_id == rider.id_user
        assert ride.id_driver_id == driver.id_user

    def test_create_rejects_invalid_status_400(self, admin_client, rider, driver):
        """T-103: status not in whitelist → 400."""
        response = admin_client.post(
            "/api/rides/",
            _payload(rider, driver, status="in-progress"),
            format="json",
        )
        assert response.status_code == 400
        assert "status" in response.data["error"]

    def test_create_rejects_lat_out_of_range_400(self, admin_client, rider, driver):
        """T-104: pickup_latitude=91 → 400 (range -90..90)."""
        response = admin_client.post(
            "/api/rides/",
            _payload(rider, driver, pickup_latitude=91.0),
            format="json",
        )
        assert response.status_code == 400
        assert "pickup_latitude" in response.data["error"]

    def test_create_rejects_rider_equals_driver_400(self, admin_client, rider):
        """T-105: Same user as rider AND driver → 400."""
        response = admin_client.post(
            "/api/rides/",
            _payload(rider, rider),
            format="json",
        )
        assert response.status_code == 400
        assert "different" in response.data["error"].lower()


@pytest.mark.django_db
class TestRideUpdate:
    def test_put_full_update_200(self, admin_client, make_ride, rider, driver):
        """T-106: PUT with all fields updates the row."""
        ride = make_ride()
        body = _payload(rider, driver, status="en-route", pickup_latitude=14.7000)
        response = admin_client.put(
            f"/api/rides/{ride.id_ride}/", body, format="json"
        )
        assert response.status_code == 200
        ride.refresh_from_db()
        assert ride.status == "en-route"
        assert ride.pickup_latitude == 14.7000

    def test_patch_partial_update_200(self, admin_client, make_ride):
        """T-107: PATCH just status leaves other fields unchanged."""
        ride = make_ride(status="to-pickup", pickup_lat=14.6349)
        response = admin_client.patch(
            f"/api/rides/{ride.id_ride}/",
            {"status": "dropoff"},
            format="json",
        )
        assert response.status_code == 200
        ride.refresh_from_db()
        assert ride.status == "dropoff"
        assert ride.pickup_latitude == 14.6349

    def test_put_response_has_nested_rider(
        self, admin_client, make_ride, make_event, rider, driver
    ):
        """T-108: PUT response re-serializes via RideReadSerializer."""
        ride = make_ride()
        make_event(ride)
        body = _payload(rider, driver, status="dropoff")
        response = admin_client.put(
            f"/api/rides/{ride.id_ride}/", body, format="json"
        )
        assert response.status_code == 200
        assert isinstance(response.data["id_rider"], dict)
        assert isinstance(response.data["id_driver"], dict)
        assert "todays_ride_events" in response.data
        assert len(response.data["todays_ride_events"]) == 1

    def test_patch_invalid_coord_400(self, admin_client, make_ride):
        """T-109: PATCH pickup_longitude=200 → 400 (range -180..180)."""
        ride = make_ride()
        response = admin_client.patch(
            f"/api/rides/{ride.id_ride}/",
            {"pickup_longitude": 200.0},
            format="json",
        )
        assert response.status_code == 400
        assert "pickup_longitude" in response.data["error"]


@pytest.mark.django_db
class TestRideDelete:
    def test_admin_deletes_ride_204(self, admin_client, make_ride):
        """T-110: DELETE → 204 and row removed."""
        ride = make_ride()
        response = admin_client.delete(f"/api/rides/{ride.id_ride}/")
        assert response.status_code == 204
        assert not Ride.objects.filter(pk=ride.id_ride).exists()

    def test_delete_cascades_ride_events(self, admin_client, make_ride, make_event):
        """T-111: Deleting a ride cascades to its RideEvent rows."""
        ride = make_ride()
        make_event(ride)
        make_event(ride, description="Status changed to dropoff")
        assert RideEvent.objects.filter(id_ride=ride).count() == 2
        response = admin_client.delete(f"/api/rides/{ride.id_ride}/")
        assert response.status_code == 204
        assert RideEvent.objects.filter(id_ride=ride).count() == 0

    def test_delete_nonexistent_404(self, admin_client):
        """T-112: DELETE /api/rides/99999/ → 404."""
        response = admin_client.delete("/api/rides/99999/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestRideWritePermissions:
    def test_non_admin_post_403(self, api_client, non_admin_user, rider, driver):
        """T-113: Non-admin POST → 403."""
        api_client.force_authenticate(user=non_admin_user)
        response = api_client.post(
            "/api/rides/", _payload(rider, driver), format="json"
        )
        assert response.status_code == 403

    def test_unauthenticated_post_401(self, api_client, rider, driver):
        """T-114: Unauthenticated POST → 401."""
        response = api_client.post(
            "/api/rides/", _payload(rider, driver), format="json"
        )
        assert response.status_code == 401

    def test_non_admin_delete_403(self, api_client, non_admin_user, make_ride):
        """T-115: Non-admin DELETE → 403 and ride still exists."""
        ride = make_ride()
        api_client.force_authenticate(user=non_admin_user)
        response = api_client.delete(f"/api/rides/{ride.id_ride}/")
        assert response.status_code == 403
        assert Ride.objects.filter(pk=ride.id_ride).exists()


@pytest.mark.django_db
class TestRideWriteQueryBudget:
    def test_create_query_budget(self, admin_client, rider, driver):
        """T-116: POST path query count stays bounded (no N+1 on write)."""
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.post(
                "/api/rides/", _payload(rider, driver), format="json"
            )
        assert response.status_code == 201
        # Expected: rider FK existence check, driver FK existence check,
        # INSERT rides, re-fetch SELECT (joins rider+driver), events prefetch.
        # Bound at 8 to absorb savepoint overhead; catches regressions if the
        # re-fetch accidentally N+1s.
        assert len(ctx.captured_queries) <= 8, (
            f"POST used {len(ctx.captured_queries)} queries: "
            f"{[q['sql'] for q in ctx.captured_queries]}"
        )

    def test_list_query_budget_unchanged(self, admin_client, make_ride, make_event):
        """T-117: Regression — GET list still ≤3 queries after ModelViewSet promotion."""
        for _ in range(10):
            ride = make_ride()
            make_event(ride)
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get("/api/rides/")
        assert response.status_code == 200
        assert len(ctx.captured_queries) <= 3
