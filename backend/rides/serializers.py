from rest_framework import serializers

from rides.models import User, Ride, RideEvent


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id_user", "role", "first_name", "last_name", "email", "phone_number"]


class RideEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = RideEvent
        fields = ["id_ride_event", "description", "created_at"]


class RideSerializer(serializers.ModelSerializer):
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
