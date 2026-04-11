"""Seed the database with synthetic demo data.

This command WIPES the existing User table (cascading to Ride and RideEvent
via on_delete=CASCADE) and rebuilds the dataset on every invocation. The
deploy workflow runs it after every migration so the demo always shows
now-relative timestamps in the UI.

Status semantics:
  pickup   = upcoming ride (pickup_time is in the future)
  en-route = trip in progress (pickup just happened, minutes ago)
  dropoff  = trip concluded (pickup_time in the past — fresh or historical)

DO NOT run against a database that holds real user data. There is no real
user data in this project; if that ever changes, remove this command from
the deploy workflow first.
"""

from datetime import timedelta

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand
from django.utils import timezone

from rides.models import Ride, RideEvent, User


class Command(BaseCommand):
    help = "Wipe and re-seed the database with now-relative demo data."

    def handle(self, *args, **options):
        # Synthetic-only data — see module docstring.
        User.objects.all().delete()

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
        # 24 rides ordered so page 1 shows a mix of statuses and event counts:
        # stress test + fresh dropoffs + en-route rides + some pickup rides.
        #
        # Rider distribution is constrained by the deployed regression script
        # (test_deployed_api.sh):
        #   - Alice: 8 rides total, of which 4 are `pickup` (FILT-04a, FILT-05)
        #   - Bob:   8 rides total
        #   - Carol: 8 rides total
        # Status distribution: 8 pickup, 8 en-route, 8 dropoff.
        #
        # Tuple format:
        # (status, pickup_time_offset_from_now, rider_idx, driver_idx, zone_idx)
        ride_specs = [
            # Ride 1 (idx 0): stress test, dropoff finished 90 min ago
            ("dropoff",  -timedelta(minutes=90), 0, 0, 0),  # alice, chris, zone10
            # Rides 2, 3 (idx 1, 2): fresh dropoffs (recent past)
            ("dropoff",  -timedelta(hours=2),    1, 1, 1),  # bob, howard, zone14
            ("dropoff",  -timedelta(hours=4),    2, 2, 2),  # carol, randy, antigua
            # Rides 4, 5, 6 (idx 3, 4, 5): en-route, very recent
            ("en-route", -timedelta(minutes=5),  0, 1, 0),  # alice, howard, zone10
            ("en-route", -timedelta(minutes=12), 1, 2, 1),  # bob, randy, zone14
            ("en-route", -timedelta(minutes=18), 2, 0, 2),  # carol, chris, antigua
            # Rides 7, 8, 9 (idx 6, 7, 8): pickup, near future
            ("pickup",   timedelta(hours=1),     0, 0, 0),  # alice pickup #1
            ("pickup",   timedelta(hours=4),     1, 1, 1),  # bob pickup
            ("pickup",   timedelta(hours=8),     2, 2, 2),  # carol pickup
            # Ride 10 (idx 9): en-route
            ("en-route", -timedelta(minutes=25), 0, 2, 1),  # alice en-route #2
            # Rides 11-14 (idx 10-13): more en-route
            ("en-route", -timedelta(minutes=33), 1, 0, 2),  # bob
            ("en-route", -timedelta(minutes=42), 2, 1, 0),  # carol
            ("en-route", -timedelta(minutes=51), 1, 2, 2),  # bob
            ("en-route", -timedelta(minutes=58), 2, 0, 1),  # carol
            # Rides 15-19 (idx 14-18): more pickup, further out
            ("pickup",   timedelta(hours=18),            0, 1, 0),  # alice pickup #2
            ("pickup",   timedelta(days=1),              1, 2, 1),  # bob pickup
            ("pickup",   timedelta(days=1, hours=12),    0, 0, 2),  # alice pickup #3
            ("pickup",   timedelta(days=2),              2, 1, 0),  # carol pickup
            ("pickup",   timedelta(days=3),              0, 2, 1),  # alice pickup #4
            # Rides 20, 21 (idx 19, 20): dropoffs ~2 weeks ago — boundary tests
            ("dropoff",  -timedelta(days=14),    1, 0, 0),  # bob, chris — 61 min
            ("dropoff",  -timedelta(days=15),    1, 1, 1),  # bob, howard — 59 min (excluded)
            # Rides 22-24 (idx 21-23): historical dropoffs across months
            ("dropoff",  -timedelta(days=32),    2, 1, 2),  # carol, howard — 75 min
            ("dropoff",  -timedelta(days=62),    0, 2, 1),  # alice, randy — 90 min
            ("dropoff",  -timedelta(days=95),    2, 0, 0),  # carol, chris — 120 min
        ]

        rides = []
        for status, offset, rider_idx, driver_idx, zone_idx in ride_specs:
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

        # ---------- Events ----------

        # Ride 1 (idx 0): realistic full trip lifecycle.
        # 6 fresh events (all within 24h) walking through the normal ride
        # flow, plus 1 event 48h ago to demonstrate the 24h Prefetch filter
        # excluding old events. EVENTS 24H column shows 6.
        #
        # Note: we intentionally do NOT stress-test the Prefetch filter with
        # many events here — `tests/test_performance.py` already covers the
        # query count + filter correctness at the code level with its own
        # fixtures, and a realistic event count reads better in the UI demo.
        ride1 = rides[0]
        ride1_pickup = ride1.pickup_time  # now - 90 min
        ride1_events = [
            ("Ride requested",              ride1_pickup - timedelta(minutes=10)),
            ("Driver assigned",             ride1_pickup - timedelta(minutes=5)),
            ("Status changed to pickup",    ride1_pickup),
            ("Status changed to dropoff",   ride1_pickup + timedelta(minutes=25)),
            ("Payment processed",           ride1_pickup + timedelta(minutes=27)),
            ("Rating submitted",            ride1_pickup + timedelta(minutes=35)),
        ]
        for desc, ts in ride1_events:
            RideEvent.objects.create(
                id_ride=ride1, description=desc, created_at=ts,
            )
        # 1 old event (48h ago) — excluded by the 24h Prefetch filter.
        RideEvent.objects.create(
            id_ride=ride1, description="Old analytics event",
            created_at=now - timedelta(hours=48),
        )

        # Rides 2, 3 (idx 1, 2): fresh dropoff pairs — 2 events each
        for idx in (1, 2):
            r = rides[idx]
            RideEvent.objects.create(
                id_ride=r, description="Status changed to pickup",
                created_at=r.pickup_time,
            )
            RideEvent.objects.create(
                id_ride=r, description="Status changed to dropoff",
                created_at=r.pickup_time + timedelta(minutes=30),
            )

        # Ride 2 (idx 1) gets one extra event from 48h ago — independent
        # 24h-filter exclusion test. EVENTS 24H column on ride 2 still shows 2.
        RideEvent.objects.create(
            id_ride=rides[1], description="Old status update",
            created_at=now - timedelta(hours=48),
        )

        # En-route rides — 1 pickup event each, at the ride's pickup_time
        en_route_indices = (3, 4, 5, 9, 10, 11, 12, 13)
        for idx in en_route_indices:
            r = rides[idx]
            RideEvent.objects.create(
                id_ride=r, description="Status changed to pickup",
                created_at=r.pickup_time,
            )

        # Historical dropoff rides 20-24 (idx 19-23): pickup/dropoff event
        # pairs sized for the bonus SQL "trips > 1 hour" report.
        # (ride_idx, duration_minutes)
        historical_pairs = [
            (19, 61),   # ~2 weeks ago — boundary INCLUDED
            (20, 59),   # ~2 weeks ago — boundary EXCLUDED
            (21, 75),   # ~1 month ago
            (22, 90),   # ~2 months ago
            (23, 120),  # ~3 months ago
        ]
        for idx, duration_min in historical_pairs:
            r = rides[idx]
            RideEvent.objects.create(
                id_ride=r, description="Status changed to pickup",
                created_at=r.pickup_time,
            )
            RideEvent.objects.create(
                id_ride=r, description="Status changed to dropoff",
                created_at=r.pickup_time + timedelta(minutes=duration_min),
            )

        # MIN/MAX bonus SQL edge: ride 22 (idx 21) gets a second
        # "Status changed to pickup" event 10 min earlier than the first.
        # The bonus report uses MIN(created_at) to capture the first pickup.
        RideEvent.objects.create(
            id_ride=rides[21],
            description="Status changed to pickup",
            created_at=rides[21].pickup_time - timedelta(minutes=10),
        )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {User.objects.count()} users, "
            f"{Ride.objects.count()} rides, "
            f"{RideEvent.objects.count()} events."
        ))
