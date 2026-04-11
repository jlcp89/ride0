import math
import pytest
from django.utils import timezone
from django.contrib.auth.hashers import make_password

ADMIN_PASSWORD = "adminpass123"
USER_PASSWORD = "userpass123"


@pytest.fixture
def admin_user(db):
    from rides.models import User
    return User.objects.create(
        first_name="Admin", last_name="Tester",
        email="admin@wingz.com", role="admin", phone_number="555-0001",
        password=make_password(ADMIN_PASSWORD),
    )


@pytest.fixture
def non_admin_user(db):
    from rides.models import User
    return User.objects.create(
        first_name="Regular", last_name="User",
        email="user@wingz.com", role="rider", phone_number="555-0002",
        password=make_password(USER_PASSWORD),
    )


@pytest.fixture
def driver(db):
    from rides.models import User
    return User.objects.create(
        first_name="Chris", last_name="H",
        email="chris@wingz.com", role="driver", phone_number="555-0003",
        password=make_password(USER_PASSWORD),
    )


@pytest.fixture
def rider(db):
    from rides.models import User
    return User.objects.create(
        first_name="Rider", last_name="One",
        email="rider1@wingz.com", role="rider", phone_number="555-0004",
        password=make_password(USER_PASSWORD),
    )


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def make_ride(rider, driver):
    """Factory — creates rides with sensible defaults. Override any param."""
    from rides.models import Ride
    def _make(status="to-pickup", pickup_lat=14.6349, pickup_lng=-90.5069,
              dropoff_lat=14.6407, dropoff_lng=-90.5133,
              pickup_time=None, rider_override=None, driver_override=None):
        return Ride.objects.create(
            status=status,
            id_rider=rider_override or rider,
            id_driver=driver_override or driver,
            pickup_latitude=pickup_lat, pickup_longitude=pickup_lng,
            dropoff_latitude=dropoff_lat, dropoff_longitude=dropoff_lng,
            pickup_time=pickup_time or timezone.now(),
        )
    return _make


@pytest.fixture
def make_event():
    """Factory — creates ride events."""
    from rides.models import RideEvent
    def _make(ride, description="Status changed to pickup", created_at=None):
        return RideEvent.objects.create(
            id_ride=ride, description=description,
            created_at=created_at or timezone.now(),
        )
    return _make


@pytest.fixture(autouse=True)
def _register_sqlite_math(db):
    """Register math functions so Haversine RawSQL works in SQLite tests."""
    from django.db import connection
    if connection.vendor == 'sqlite':
        connection.ensure_connection()
        connection.connection.create_function("RADIANS", 1, math.radians)
        connection.connection.create_function("SIN", 1, math.sin)
        connection.connection.create_function("COS", 1, math.cos)
        connection.connection.create_function("ASIN", 1, math.asin)
        connection.connection.create_function("SQRT", 1, math.sqrt)
        connection.connection.create_function("POWER", 2, math.pow)
