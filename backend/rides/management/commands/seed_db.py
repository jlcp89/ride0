from datetime import timedelta

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from rides.models import User, Ride, RideEvent


class Command(BaseCommand):
    help = "Seed database with sample data. Skips if data already exists."

    def handle(self, *args, **options):
        if User.objects.exists():
            self.stdout.write("Database already seeded — skipping.")
            return

        now = timezone.now()
        pwd = make_password("adminpass123")
        driver_pwd = make_password("driverpass123")

        # Users
        User.objects.create(
            role="admin", first_name="Admin", last_name="User",
            email="admin@wingz.com", phone_number="555-0001", password=pwd,
        )
        chris = User.objects.create(
            role="driver", first_name="Chris", last_name="H",
            email="chris@wingz.com", phone_number="555-0002", password=driver_pwd,
        )
        howard = User.objects.create(
            role="driver", first_name="Howard", last_name="Y",
            email="howard@wingz.com", phone_number="555-0003", password=driver_pwd,
        )
        randy = User.objects.create(
            role="driver", first_name="Randy", last_name="W",
            email="randy@wingz.com", phone_number="555-0004", password=driver_pwd,
        )
        alice = User.objects.create(
            role="rider", first_name="Alice", last_name="Rider",
            email="alice@wingz.com", phone_number="555-0010", password=driver_pwd,
        )
        bob = User.objects.create(
            role="rider", first_name="Bob", last_name="Rider",
            email="bob@wingz.com", phone_number="555-0011", password=driver_pwd,
        )
        carol = User.objects.create(
            role="rider", first_name="Carol", last_name="Rider",
            email="carol@wingz.com", phone_number="555-0012", password=driver_pwd,
        )

        # GPS zones
        zone10 = (14.5995, -90.5131, 14.6200, -90.5300)
        zone14 = (14.5880, -90.4800, 14.6100, -90.5000)
        antigua = (14.5586, -90.7295, 14.5700, -90.7100)

        # Rides — 24 total, spread Jan-Apr 2024
        ride_data = [
            # Jan (6)
            ("pickup", alice, chris, zone10, "2024-01-05 08:00"),
            ("pickup", bob, howard, zone14, "2024-01-10 09:00"),
            ("dropoff", carol, randy, antigua, "2024-01-15 10:00"),
            ("dropoff", alice, chris, zone10, "2024-01-20 11:00"),
            ("en-route", bob, howard, zone14, "2024-01-25 12:00"),
            ("en-route", carol, randy, antigua, "2024-01-30 13:00"),
            # Feb (6)
            ("pickup", alice, howard, zone10, "2024-02-05 08:00"),
            ("pickup", bob, randy, zone14, "2024-02-10 09:00"),
            ("dropoff", carol, chris, antigua, "2024-02-15 10:00"),
            ("dropoff", alice, howard, zone10, "2024-02-20 11:00"),
            ("en-route", bob, randy, zone14, "2024-02-25 12:00"),
            ("en-route", carol, chris, antigua, "2024-02-28 13:00"),
            # Mar (6)
            ("pickup", alice, randy, zone10, "2024-03-05 08:00"),
            ("pickup", bob, chris, zone14, "2024-03-10 09:00"),
            ("dropoff", carol, howard, antigua, "2024-03-15 10:00"),
            ("dropoff", alice, randy, zone10, "2024-03-20 11:00"),
            ("en-route", bob, chris, zone14, "2024-03-25 12:00"),
            ("en-route", carol, howard, antigua, "2024-03-30 13:00"),
            # Apr (6) — last 3 use NOW() for recent events
            ("pickup", alice, chris, zone10, "2024-04-05 08:00"),
            ("pickup", bob, howard, zone14, "2024-04-10 09:00"),
            ("dropoff", carol, randy, antigua, "2024-04-15 10:00"),
        ]

        rides = []
        for status, rider, driver, gps, pickup in ride_data:
            r = Ride.objects.create(
                status=status, id_rider=rider, id_driver=driver,
                pickup_latitude=gps[0], pickup_longitude=gps[1],
                dropoff_latitude=gps[2], dropoff_longitude=gps[3],
                pickup_time=pickup,
            )
            rides.append(r)

        # Last 3 rides use current time
        for status, rider, driver, gps in [
            ("dropoff", alice, chris, zone10),
            ("en-route", bob, howard, zone14),
            ("en-route", carol, randy, antigua),
        ]:
            r = Ride.objects.create(
                status=status, id_rider=rider, id_driver=driver,
                pickup_latitude=gps[0], pickup_longitude=gps[1],
                dropoff_latitude=gps[2], dropoff_longitude=gps[3],
                pickup_time=now,
            )
            rides.append(r)

        # Ride Events
        # Ride 1: 20+ events (stress test for Prefetch filtering)
        r1 = rides[0]
        r1_events = [
            ("Status changed to pickup", "2024-01-05 08:00"),
            ("Status changed to dropoff", "2024-01-05 09:30"),
            ("Driver arrived at pickup", "2024-01-05 08:05"),
            ("Rider confirmed pickup", "2024-01-05 08:10"),
            ("En route to destination", "2024-01-05 08:15"),
            ("Midway checkpoint", "2024-01-05 08:30"),
            ("Traffic delay noted", "2024-01-05 08:35"),
            ("Approaching destination", "2024-01-05 08:50"),
            ("Arrived at destination", "2024-01-05 09:00"),
            ("Rider confirmed dropoff", "2024-01-05 09:05"),
            ("Payment processed", "2024-01-05 09:10"),
            ("Rating submitted", "2024-01-05 09:15"),
            ("Receipt sent", "2024-01-05 09:20"),
            ("Trip summary generated", "2024-01-05 09:22"),
            ("Driver feedback received", "2024-01-05 09:25"),
            ("Route logged", "2024-01-05 09:26"),
            ("Trip archived", "2024-01-05 09:27"),
            ("Analytics event sent", "2024-01-05 09:28"),
            ("Cleanup completed", "2024-01-05 09:29"),
            ("Final status update", "2024-01-05 09:30"),
            ("Post-trip notification", "2024-01-05 09:31"),
        ]
        for desc, ts in r1_events:
            RideEvent.objects.create(id_ride=r1, description=desc, created_at=ts)

        # Pickup/dropoff pairs for bonus SQL (trips > 1hr)
        event_pairs = [
            # (ride_index, pickup_time, dropoff_time)
            (1, "2024-01-10 09:00", "2024-01-10 10:15"),     # 75 min
            (2, "2024-01-15 10:00", "2024-01-15 11:30"),     # 90 min
            (3, "2024-01-20 11:00", "2024-01-20 12:20"),     # 80 min
            (4, "2024-01-25 12:00", "2024-01-25 12:59"),     # 59 min — excluded
            (5, "2024-01-30 13:00", "2024-01-30 14:01"),     # 61 min
            (6, "2024-02-05 08:00", "2024-02-05 09:10"),     # 70 min
            (7, "2024-02-10 09:00", "2024-02-10 10:25"),     # 85 min
            (8, "2024-02-15 10:00", "2024-02-15 11:35"),     # 95 min
            (9, "2024-02-20 11:00", "2024-02-20 11:45"),     # 45 min — excluded
            (10, "2024-02-25 12:00", "2024-02-25 12:30"),    # 30 min — excluded
            (11, "2024-02-28 13:00", "2024-02-28 14:40"),    # 100 min
            (12, "2024-03-05 08:00", "2024-03-05 09:05"),    # 65 min
            (13, "2024-03-10 09:00", "2024-03-10 09:50"),    # 50 min — excluded
            (14, "2024-03-15 10:00", "2024-03-15 11:15"),    # 75 min
            (15, "2024-03-20 11:00", "2024-03-20 12:30"),    # 90 min
            (16, "2024-03-25 12:00", "2024-03-25 12:40"),    # 40 min — excluded
            (17, "2024-03-30 13:00", "2024-03-30 14:20"),    # 80 min
            (18, "2024-04-05 08:00", "2024-04-05 09:10"),    # 70 min
            (19, "2024-04-10 09:00", "2024-04-10 09:55"),    # 55 min — excluded
            (20, "2024-04-15 10:00", "2024-04-15 12:00"),    # 120 min
        ]
        for idx, pickup_ts, dropoff_ts in event_pairs:
            RideEvent.objects.create(
                id_ride=rides[idx], description="Status changed to pickup",
                created_at=pickup_ts,
            )
            RideEvent.objects.create(
                id_ride=rides[idx], description="Status changed to dropoff",
                created_at=dropoff_ts,
            )

        # Ride 3: extra pickup/dropoff pair (tests MIN/MAX in bonus SQL)
        RideEvent.objects.create(
            id_ride=rides[2], description="Status changed to pickup",
            created_at="2024-01-15 09:50",
        )
        RideEvent.objects.create(
            id_ride=rides[2], description="Status changed to dropoff",
            created_at="2024-01-15 11:45",
        )

        # Rides 22-24: recent events (within last 24h)
        for i, ride in enumerate(rides[21:24]):
            hours_ago_pickup = (i + 2) * 1 + 1
            hours_ago_dropoff = [1, 0.5, 0.25][i]
            RideEvent.objects.create(
                id_ride=ride, description="Status changed to pickup",
                created_at=now - timedelta(hours=hours_ago_pickup),
            )
            RideEvent.objects.create(
                id_ride=ride, description="Status changed to dropoff",
                created_at=now - timedelta(hours=hours_ago_dropoff),
            )
            # Old events (48h ago) — must NOT appear in todays_ride_events
            RideEvent.objects.create(
                id_ride=ride, description="Old status update",
                created_at=now - timedelta(hours=48),
            )
            if i < 2:
                RideEvent.objects.create(
                    id_ride=ride, description="Old driver note",
                    created_at=now - timedelta(hours=48),
                )

        self.stdout.write(self.style.SUCCESS(
            f"Seeded: {User.objects.count()} users, "
            f"{Ride.objects.count()} rides, "
            f"{RideEvent.objects.count()} events."
        ))
