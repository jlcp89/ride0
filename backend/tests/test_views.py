import pytest
from datetime import timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestRideList:
    def test_returns_rides_with_nested_objects(self, admin_client, make_ride, make_event):
        """T-001: Rides include nested rider, driver, and todays_ride_events."""
        ride = make_ride()
        make_event(ride)
        response = admin_client.get("/api/rides/")
        assert response.status_code == 200
        result = response.data["results"][0]
        assert isinstance(result["id_rider"], dict)
        assert isinstance(result["id_driver"], dict)
        assert isinstance(result["todays_ride_events"], list)
        assert len(result["todays_ride_events"]) == 1

    def test_empty_list_returns_200(self, admin_client):
        """T-002: No rides → 200 with count=0."""
        response = admin_client.get("/api/rides/")
        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []

    def test_pagination_limits_results(self, admin_client, make_ride):
        """T-003: page_size=5 with 12 rides → 5 results, count=12."""
        for _ in range(12):
            make_ride()
        response = admin_client.get("/api/rides/?page_size=5")
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
        assert response.data["count"] == 12
        assert response.data["next"] is not None

    def test_page_2_returns_remaining(self, admin_client, make_ride):
        """T-004: Page 2 with page_size=5 and 12 rides."""
        for _ in range(12):
            make_ride()
        response = admin_client.get("/api/rides/?page=2&page_size=5")
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
        assert response.data["previous"] is not None

    def test_filter_by_status(self, admin_client, make_ride):
        """T-005: Filter by status returns only matching rides."""
        make_ride(status="to-pickup")
        make_ride(status="to-pickup")
        make_ride(status="dropoff")
        response = admin_client.get("/api/rides/?status=to-pickup")
        assert response.status_code == 200
        assert response.data["count"] == 2
        for ride in response.data["results"]:
            assert ride["status"] == "to-pickup"

    def test_filter_by_rider_email(self, admin_client, make_ride, rider):
        """T-006: Filter by rider_email returns only matching rides."""
        from rides.models import User
        from django.contrib.auth.hashers import make_password
        other_rider = User.objects.create(
            first_name="Other", last_name="Rider",
            email="other@wingz.com", role="rider",
            phone_number="555-9999", password=make_password("pass"),
        )
        make_ride()  # default rider (rider1@wingz.com)
        make_ride()  # default rider
        make_ride(rider_override=other_rider)
        response = admin_client.get("/api/rides/?rider_email=rider1@wingz.com")
        assert response.status_code == 200
        assert response.data["count"] == 2
        for ride in response.data["results"]:
            assert ride["id_rider"]["email"] == "rider1@wingz.com"

    def test_combined_filters(self, admin_client, make_ride):
        """T-007: status + rider_email both applied."""
        make_ride(status="to-pickup")
        make_ride(status="dropoff")
        response = admin_client.get(
            "/api/rides/?status=to-pickup&rider_email=rider1@wingz.com"
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "to-pickup"

    def test_sort_by_pickup_time(self, admin_client, make_ride):
        """T-008: Rides ordered by pickup_time ascending."""
        now = timezone.now()
        make_ride(pickup_time=now + timedelta(hours=3))
        make_ride(pickup_time=now + timedelta(hours=1))
        make_ride(pickup_time=now + timedelta(hours=2))
        response = admin_client.get("/api/rides/?sort_by=pickup_time")
        assert response.status_code == 200
        times = [r["pickup_time"] for r in response.data["results"]]
        assert times == sorted(times)

    def test_sort_by_distance_nearest_first(self, admin_client, make_ride):
        """T-009: Zone 10 (~0km) first, Zone 14 (~3.5km) mid, Antigua (~25km) last."""
        make_ride(pickup_lat=14.5586, pickup_lng=-90.7295)  # Antigua ~25km
        make_ride(pickup_lat=14.5880, pickup_lng=-90.4800)  # Zone 14 ~3.5km
        make_ride(pickup_lat=14.5995, pickup_lng=-90.5131)  # Zone 10 ~0km
        response = admin_client.get(
            "/api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131"
        )
        assert response.status_code == 200
        lats = [r["pickup_latitude"] for r in response.data["results"]]
        assert abs(lats[0] - 14.5995) < 0.01  # Zone 10 first
        assert abs(lats[1] - 14.5880) < 0.01  # Zone 14 second
        assert abs(lats[2] - 14.5586) < 0.01  # Antigua last

    def test_distance_sort_missing_coords_returns_400(self, admin_client):
        """T-010: sort_by=distance without lat/lng → 400."""
        response = admin_client.get("/api/rides/?sort_by=distance")
        assert response.status_code == 400
        assert "latitude" in response.data["error"]

    def test_distance_sort_with_pagination(self, admin_client, make_ride):
        """T-011: Distance sort + pagination returns correct page."""
        for i in range(5):
            make_ride(pickup_lat=14.5995 + i * 0.01, pickup_lng=-90.5131)
        response = admin_client.get(
            "/api/rides/?sort_by=distance&latitude=14.5995&longitude=-90.5131&page_size=3"
        )
        assert response.status_code == 200
        assert len(response.data["results"]) == 3
        assert response.data["count"] == 5

    def test_filter_plus_distance_sort(self, admin_client, make_ride):
        """T-012: Filter + sort compose correctly."""
        make_ride(status="to-pickup", pickup_lat=14.5586, pickup_lng=-90.7295)
        make_ride(status="to-pickup", pickup_lat=14.5995, pickup_lng=-90.5131)
        make_ride(status="dropoff", pickup_lat=14.5880, pickup_lng=-90.4800)
        response = admin_client.get(
            "/api/rides/?status=to-pickup&sort_by=distance"
            "&latitude=14.5995&longitude=-90.5131"
        )
        assert response.status_code == 200
        assert response.data["count"] == 2
        for r in response.data["results"]:
            assert r["status"] == "to-pickup"
