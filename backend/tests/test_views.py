import pytest


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
        make_ride(status="pickup")
        make_ride(status="pickup")
        make_ride(status="dropoff")
        response = admin_client.get("/api/rides/?status=pickup")
        assert response.status_code == 200
        assert response.data["count"] == 2
        for ride in response.data["results"]:
            assert ride["status"] == "pickup"

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
        make_ride(status="pickup")
        make_ride(status="dropoff")
        response = admin_client.get(
            "/api/rides/?status=pickup&rider_email=rider1@wingz.com"
        )
        assert response.status_code == 200
        assert response.data["count"] == 1
        assert response.data["results"][0]["status"] == "pickup"
