from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework import serializers

from rides.models import Ride, RideEvent, User

# Canonical ride status values — mirrors the lifecycle documented in
# rides/management/commands/seed_db.py. Kept at the serializer layer because
# the spec forbids model/table changes.
RIDE_STATUS_CHOICES = [
    ("to-pickup", "To Pickup"),
    ("en-route", "En Route"),
    ("dropoff", "Dropoff"),
]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id_user", "role", "first_name", "last_name", "email", "phone_number"]


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ["id_ride_event", "description", "created_at"]


class RideReadSerializer(serializers.ModelSerializer):
    id_rider = UserSerializer(read_only=True)
    id_driver = UserSerializer(read_only=True)
    todays_ride_events = RideEventSerializer(many=True, read_only=True)

    class Meta:
        model = Ride
        fields = [
            "id_ride", "status",
            "id_rider", "id_driver",
            "pickup_latitude", "pickup_longitude",
            "dropoff_latitude", "dropoff_longitude",
            "pickup_time", "todays_ride_events",
        ]


class RideWriteSerializer(serializers.ModelSerializer):
    status = serializers.ChoiceField(choices=RIDE_STATUS_CHOICES)
    id_rider = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    id_driver = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    pickup_latitude = serializers.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    pickup_longitude = serializers.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )
    dropoff_latitude = serializers.FloatField(
        validators=[MinValueValidator(-90), MaxValueValidator(90)]
    )
    dropoff_longitude = serializers.FloatField(
        validators=[MinValueValidator(-180), MaxValueValidator(180)]
    )

    class Meta:
        model = Ride
        fields = [
            "id_ride", "status",
            "id_rider", "id_driver",
            "pickup_latitude", "pickup_longitude",
            "dropoff_latitude", "dropoff_longitude",
            "pickup_time",
        ]
        read_only_fields = ["id_ride"]

    def validate(self, attrs):
        rider = attrs.get("id_rider")
        driver = attrs.get("id_driver")
        if rider is not None and driver is not None and rider == driver:
            raise serializers.ValidationError(
                {"id_driver": "Rider and driver must be different users"}
            )
        return attrs


# Backwards-compatible alias. Existing imports (e.g. tests/test_serializers.py)
# keep working without a rename.
RideSerializer = RideReadSerializer
