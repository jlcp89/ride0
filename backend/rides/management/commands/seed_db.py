"""Seed the database with synthetic demo data.

This command WIPES the existing User table (cascading to Ride and RideEvent
via on_delete=CASCADE) and rebuilds the dataset on every invocation. The
deploy workflow runs it after every migration so the demo always shows
now-relative timestamps in the UI.

Status semantic model
---------------------
Every ride is in exactly one phase of a real trip lifecycle:

  to-pickup = Ride booked, driver accepted, driver heading to pickup.
              Rider is NOT yet in the car.
              pickup_time: future (the scheduled/expected pickup moment).
              Events: 2 (request + accept).

  en-route  = Trip in progress. Rider IS in the car. Driver is driving
              to the destination.
              pickup_time: recent past (minutes to ~90 min ago).
              Events: 3 (request + accept + pickup).

  dropoff   = Trip completed. Rider has been dropped off.
              pickup_time: past (fresh or historical).
              Events: 5 (request + accept + pickup + dropoff + rating).

Lifecycle: to-pickup -> en-route -> dropoff.

The event descriptions `"Status changed to pickup"` and `"Status changed
to dropoff"` are spec-fixed (see requirement.md line 104 and bonus SQL
filters in sql/bonus_report.sql) and must not be renamed even though the
status value is now `to-pickup` rather than `pickup`.

DO NOT run against a database that holds real user data. There is no real
user data in this project; if that ever changes, remove this command from
the deploy workflow first.
"""

from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone

from rides.models import Ride, RideEvent, User

# Canonical event descriptions. The first two are free-form; the next two
# are fixed by requirement.md line 104 and must match exactly (bonus SQL
# filters on these literals). The last is free-form.
EVENT_REQUESTED = "Ride requested"
EVENT_ACCEPTED = "Ride accepted by driver"
EVENT_PICKUP = "Status changed to pickup"   # spec-fixed
EVENT_DROPOFF = "Status changed to dropoff"  # spec-fixed
EVENT_RATED = "Ride rated by rider"


class Command(BaseCommand):
    help = "Wipe and re-seed the database with now-relative demo data."

    def handle(self, *args, **options):
        # Synthetic-only data — see module docstring.
        User.objects.all().delete()
        _reset_auto_increment()

        now = timezone.now()
        admin_pwd = make_password("adminpass123")
        user_pwd = make_password("driverpass123")

        # ---------- Users ----------
        User.objects.create(
            role="admin", first_name="Admin", last_name="User",
            email="admin@wingz.com", phone_number="555-0001", password=admin_pwd,
        )
        chris = User.objects.create(
            role="driver", first_name="Chris", last_name="H",
            email="chris@wingz.com", phone_number="555-0002", password=user_pwd,
        )
        howard = User.objects.create(
            role="driver", first_name="Howard", last_name="Y",
            email="howard@wingz.com", phone_number="555-0003", password=user_pwd,
        )
        randy = User.objects.create(
            role="driver", first_name="Randy", last_name="W",
            email="randy@wingz.com", phone_number="555-0004", password=user_pwd,
        )
        alice = User.objects.create(
            role="rider", first_name="Alice", last_name="Johnson",
            email="alice@example.com", phone_number="555-0010", password=user_pwd,
        )
        bob = User.objects.create(
            role="rider", first_name="Bob", last_name="Martin",
            email="bob@example.com", phone_number="555-0011", password=user_pwd,
        )
        carol = User.objects.create(
            role="rider", first_name="Carol", last_name="Davis",
            email="carol@example.com", phone_number="555-0012", password=user_pwd,
        )

        # ---------- GPS zones (Guatemala City + Antigua) ----------
        zone10 = (14.5995, -90.5131, 14.6200, -90.5300)
        zone14 = (14.5880, -90.4800, 14.6100, -90.5000)
        antigua = (14.5586, -90.7295, 14.5700, -90.7100)
        zones = [zone10, zone14, antigua]
        riders = [alice, bob, carol]
        drivers = [chris, howard, randy]

        # ---------- Rides ----------
        # 24 rides ordered so page 1 shows a mix of statuses and event
        # counts: fresh dropoffs (5 events) + en-route (3 events) +
        # to-pickup (2 events).
        #
        # Rider distribution is constrained by the deployed regression
        # (test_deployed_api.sh):
        #   - Alice: 8 rides total, of which 4 are to-pickup (FILT-04a/05)
        #   - Bob:   8 rides total
        #   - Carol: 8 rides total
        # Status distribution: 8 to-pickup, 8 en-route, 8 dropoff.
        #
        # Tuple: (status, pickup_offset, rider_idx, driver_idx, zone_idx,
        #         trip_duration_min)
        # trip_duration_min is only meaningful for dropoff rides; others
        # pass 0.
        ride_specs = [
            # Rides 1-3: fresh dropoffs (all 5 events visible in EVENTS 24H)
            ("dropoff",  -timedelta(minutes=90), 0, 0, 0, 25),  # alice, chris, zone10
            ("dropoff",  -timedelta(hours=2),    1, 1, 1, 28),  # bob, howard, zone14
            ("dropoff",  -timedelta(hours=4),    2, 2, 2, 32),  # carol, randy, antigua
            # Rides 4-6: en-route, very recent
            ("en-route", -timedelta(minutes=8),  0, 1, 0, 0),   # alice, howard, zone10
            ("en-route", -timedelta(minutes=15), 1, 2, 1, 0),   # bob, randy, zone14
            ("en-route", -timedelta(minutes=25), 2, 0, 2, 0),   # carol, chris, antigua
            # Rides 7-9: to-pickup, near future
            ("to-pickup", timedelta(minutes=30), 0, 0, 0, 0),   # alice to-pickup #1
            ("to-pickup", timedelta(hours=1),    1, 1, 1, 0),   # bob to-pickup
            ("to-pickup", timedelta(hours=2),    2, 2, 2, 0),   # carol to-pickup
            # Ride 10: en-route
            ("en-route", -timedelta(minutes=35), 0, 2, 1, 0),   # alice en-route #2
            # Rides 11-14: more en-route
            ("en-route", -timedelta(minutes=45), 1, 0, 2, 0),   # bob
            ("en-route", -timedelta(minutes=55), 2, 1, 0, 0),   # carol
            ("en-route", -timedelta(minutes=70), 1, 2, 2, 0),   # bob
            ("en-route", -timedelta(minutes=85), 2, 0, 1, 0),   # carol
            # Rides 15-19: more to-pickup, further out
            ("to-pickup", timedelta(hours=4),            0, 1, 0, 0),  # alice #2
            ("to-pickup", timedelta(hours=8),            1, 2, 1, 0),  # bob
            ("to-pickup", timedelta(days=1),             0, 0, 2, 0),  # alice #3
            ("to-pickup", timedelta(days=1, hours=12),   2, 1, 0, 0),  # carol
            ("to-pickup", timedelta(days=2),             0, 2, 1, 0),  # alice #4
            # Rides 20-21: dropoffs ~2 weeks ago — boundary tests
            ("dropoff",  -timedelta(days=14),    1, 0, 0, 61),  # bob, chris — 61 min included
            ("dropoff",  -timedelta(days=15),    1, 1, 1, 59),  # bob, howard — 59 min excluded
            # Rides 22-24: historical dropoffs across months
            ("dropoff",  -timedelta(days=32),    2, 1, 2, 75),  # carol, howard — 75 min
            ("dropoff",  -timedelta(days=62),    0, 2, 1, 90),  # alice, randy — 90 min
            ("dropoff",  -timedelta(days=95),    2, 0, 0, 120),  # carol, chris — 120 min
        ]

        rides = []
        ride_durations = []
        for status, offset, rider_idx, driver_idx, zone_idx, duration in ride_specs:
            zone = zones[zone_idx]
            r = Ride.objects.create(
                status=status,
                id_rider=riders[rider_idx],
                id_driver=drivers[driver_idx],
                pickup_latitude=zone[0],
                pickup_longitude=zone[1],
                dropoff_latitude=zone[2],
                dropoff_longitude=zone[3],
                pickup_time=now + offset,
            )
            rides.append(r)
            ride_durations.append(duration)

        # ---------- Events ----------
        # Every ride has a canonical 5-step lifecycle; only the events that
        # have already happened by `now` are created. The current status
        # tells us how far along the ride is.
        for r, duration in zip(rides, ride_durations):
            _create_events_for_ride(r, duration, now)

        # MIN/MAX bonus-SQL edge case: ride 22 (idx 21) — carol's ~1-month-old
        # dropoff — gets an EXTRA "Status changed to pickup" event 2 minutes
        # before the normal one. This exercises MIN(created_at) in
        # bonus_report.sql which handles rides with multiple pickup events.
        r22 = rides[21]
        RideEvent.objects.create(
            id_ride=r22,
            description=EVENT_PICKUP,
            created_at=r22.pickup_time - timedelta(minutes=2),
        )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {User.objects.count()} users, "
            f"{Ride.objects.count()} rides, "
            f"{RideEvent.objects.count()} events."
        ))


def _reset_auto_increment():
    """Reset the AUTO_INCREMENT counter on users, rides, ride_events so that
    a freshly-seeded DB always starts IDs at 1. Without this, every re-seed
    accumulates ever-higher IDs (SQLite doesn't reset on DELETE, and MySQL
    doesn't reset on TRUNCATE CASCADE either).
    """
    with connection.cursor() as cursor:
        if connection.vendor == "sqlite":
            cursor.execute(
                "DELETE FROM sqlite_sequence "
                "WHERE name IN ('users', 'rides', 'ride_events')"
            )
        elif connection.vendor == "mysql":
            for table in ("users", "rides", "ride_events"):
                cursor.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")


def _create_events_for_ride(ride, trip_duration_min, now):
    """Create the canonical event log for a ride based on its current status.

    Every ride's full lifecycle is 5 events (request, accept, pickup,
    dropoff, rated). We only create the events that have happened by `now`:
      to-pickup -> 2 events (request, accept)
      en-route  -> 3 events (request, accept, pickup)
      dropoff   -> 5 events (request, accept, pickup, dropoff, rated)

    For to-pickup rides pickup_time is in the future, so request/accept
    anchor to `now` (they already happened). For en-route and dropoff
    rides, request/accept anchor to pickup_time - offsets.
    """
    pt = ride.pickup_time

    if ride.status == "to-pickup":
        req_at = now - timedelta(minutes=10)
        acc_at = now - timedelta(minutes=5)
    else:
        req_at = pt - timedelta(minutes=10)
        acc_at = pt - timedelta(minutes=5)

    RideEvent.objects.create(id_ride=ride, description=EVENT_REQUESTED, created_at=req_at)
    RideEvent.objects.create(id_ride=ride, description=EVENT_ACCEPTED, created_at=acc_at)

    if ride.status in ("en-route", "dropoff"):
        RideEvent.objects.create(id_ride=ride, description=EVENT_PICKUP, created_at=pt)

    if ride.status == "dropoff":
        drop_at = pt + timedelta(minutes=trip_duration_min)
        rate_at = drop_at + timedelta(minutes=3)
        RideEvent.objects.create(id_ride=ride, description=EVENT_DROPOFF, created_at=drop_at)
        RideEvent.objects.create(id_ride=ride, description=EVENT_RATED, created_at=rate_at)
