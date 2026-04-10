from django.db import models


class User(models.Model):
    id_user = models.AutoField(primary_key=True)
    role = models.CharField(max_length=50)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50)
    password = models.CharField(max_length=128)

    class Meta:
        db_table = "users"

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.role})"


class Ride(models.Model):
    id_ride = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50)
    id_rider = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="rides_as_rider", db_column="id_rider",
    )
    id_driver = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="rides_as_driver", db_column="id_driver",
    )
    pickup_latitude = models.FloatField()
    pickup_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_longitude = models.FloatField()
    pickup_time = models.DateTimeField()

    class Meta:
        db_table = "rides"

    def __str__(self):
        return f"Ride {self.id_ride} ({self.status})"


class RideEvent(models.Model):
    id_ride_event = models.AutoField(primary_key=True)
    id_ride = models.ForeignKey(
        Ride, on_delete=models.CASCADE,
        related_name="ride_events", db_column="id_ride",
    )
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField()

    class Meta:
        db_table = "ride_events"
        indexes = [
            models.Index(fields=["created_at"], name="idx_rideevent_created"),
        ]

    def __str__(self):
        return f"Event {self.id_ride_event}: {self.description}"
