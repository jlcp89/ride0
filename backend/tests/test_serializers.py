import pytest
from django.utils import timezone


@pytest.mark.django_db
class TestSerializers:
    def test_rider_is_nested_object(self, rider, driver):
        from rides.models import Ride
        from rides.serializers import RideSerializer
        ride = Ride.objects.create(
            status="pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        ride.todays_ride_events = []
        data = RideSerializer(ride).data
        assert isinstance(data["id_rider"], dict)
        assert data["id_rider"]["first_name"] == "Rider"
        assert data["id_rider"]["email"] == "rider1@wingz.com"

    def test_driver_is_nested_object(self, rider, driver):
        from rides.models import Ride
        from rides.serializers import RideSerializer
        ride = Ride.objects.create(
            status="pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        ride.todays_ride_events = []
        data = RideSerializer(ride).data
        assert isinstance(data["id_driver"], dict)
        assert data["id_driver"]["first_name"] == "Chris"
        assert data["id_driver"]["email"] == "chris@wingz.com"

    def test_todays_ride_events_includes_events(self, rider, driver):
        from rides.models import Ride, RideEvent
        from rides.serializers import RideSerializer
        ride = Ride.objects.create(
            status="pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        event = RideEvent.objects.create(
            id_ride=ride, description="Status changed to pickup",
            created_at=timezone.now(),
        )
        ride.todays_ride_events = [event]
        data = RideSerializer(ride).data
        assert len(data["todays_ride_events"]) == 1
        assert data["todays_ride_events"][0]["description"] == "Status changed to pickup"

    def test_todays_ride_events_empty_when_no_events(self, rider, driver):
        from rides.models import Ride
        from rides.serializers import RideSerializer
        ride = Ride.objects.create(
            status="pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        ride.todays_ride_events = []
        data = RideSerializer(ride).data
        assert data["todays_ride_events"] == []

    def test_all_spec_fields_present_and_password_excluded(self, rider, driver):
        from rides.models import Ride
        from rides.serializers import RideSerializer
        ride = Ride.objects.create(
            status="pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        ride.todays_ride_events = []
        data = RideSerializer(ride).data
        expected_fields = {
            "id_ride", "status", "id_rider", "id_driver",
            "pickup_latitude", "pickup_longitude",
            "dropoff_latitude", "dropoff_longitude",
            "pickup_time", "todays_ride_events",
        }
        assert set(data.keys()) == expected_fields
        assert "password" not in data["id_rider"]
        assert "password" not in data["id_driver"]
