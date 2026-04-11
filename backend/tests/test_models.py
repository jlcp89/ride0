import pytest
from django.contrib.auth.hashers import make_password


@pytest.mark.django_db
class TestUserModel:
    def test_db_table(self):
        from rides.models import User
        assert User._meta.db_table == "users"

    def test_pk_name(self):
        from rides.models import User
        assert User._meta.pk.name == "id_user"

    def test_has_all_spec_fields(self):
        from rides.models import User
        field_names = {f.name for f in User._meta.get_fields()}
        expected = {"id_user", "role", "first_name", "last_name",
                    "email", "phone_number", "password"}
        assert expected.issubset(field_names)

    def test_str(self):
        from rides.models import User
        user = User.objects.create(
            first_name="Test", last_name="User",
            email="test@wingz.com", role="rider",
            phone_number="555-0000", password=make_password("pass"),
        )
        assert "Test" in str(user)


@pytest.mark.django_db
class TestRideModel:
    def test_db_table(self):
        from rides.models import Ride
        assert Ride._meta.db_table == "rides"

    def test_pk_name(self):
        from rides.models import Ride
        assert Ride._meta.pk.name == "id_ride"

    def test_fk_rider_to_user(self, rider, driver):
        from rides.models import Ride
        from django.utils import timezone
        ride = Ride.objects.create(
            status="to-pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        assert ride.id_rider.email == "rider1@wingz.com"
        assert ride.id_driver.email == "chris@wingz.com"

    def test_str(self, rider, driver):
        from rides.models import Ride
        from django.utils import timezone
        ride = Ride.objects.create(
            status="to-pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        assert "to-pickup" in str(ride)


@pytest.mark.django_db
class TestRideEventModel:
    def test_db_table(self):
        from rides.models import RideEvent
        assert RideEvent._meta.db_table == "ride_events"

    def test_pk_name(self):
        from rides.models import RideEvent
        assert RideEvent._meta.pk.name == "id_ride_event"

    def test_fk_to_ride(self, rider, driver):
        from rides.models import Ride, RideEvent
        from django.utils import timezone
        ride = Ride.objects.create(
            status="to-pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        event = RideEvent.objects.create(
            id_ride=ride, description="Status changed to pickup",
            created_at=timezone.now(),
        )
        assert event.id_ride.id_ride == ride.id_ride

    def test_str(self, rider, driver):
        from rides.models import Ride, RideEvent
        from django.utils import timezone
        ride = Ride.objects.create(
            status="to-pickup", id_rider=rider, id_driver=driver,
            pickup_latitude=14.0, pickup_longitude=-90.0,
            dropoff_latitude=14.1, dropoff_longitude=-90.1,
            pickup_time=timezone.now(),
        )
        event = RideEvent.objects.create(
            id_ride=ride, description="Status changed to pickup",
            created_at=timezone.now(),
        )
        assert "pickup" in str(event).lower()
