import pytest
from datetime import timedelta
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.utils import timezone


@pytest.mark.django_db
class TestQueryCount:
    """
    Spec: 'Retrieving the ride list with the related driver, rider, and
    RideEvents can be achieved with 2 queries (3 if you include the query
    required to get the total count used in Pagination).'
    """

    def test_max_3_queries(self, admin_client, make_ride, make_event):
        """3 queries: COUNT + rides JOIN users + filtered events."""
        for _ in range(10):
            ride = make_ride()
            make_event(ride)
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get("/api/rides/")
        assert response.status_code == 200
        assert len(ctx.captured_queries) <= 3

    def test_no_n_plus_1(self, admin_client, make_ride, make_event):
        """Query count stays at 3 whether 5 or 25 rides."""
        for _ in range(5):
            ride = make_ride()
            make_event(ride)
        with CaptureQueriesContext(connection) as ctx:
            admin_client.get("/api/rides/?page_size=100")
        count_with_5 = len(ctx.captured_queries)

        for _ in range(20):
            ride = make_ride()
            make_event(ride)
        with CaptureQueriesContext(connection) as ctx:
            admin_client.get("/api/rides/?page_size=100")
        count_with_25 = len(ctx.captured_queries)

        assert count_with_5 == count_with_25

    def test_prefetch_filters_created_at(self, admin_client, make_ride, make_event):
        """The ride_events query MUST filter on created_at."""
        ride = make_ride()
        make_event(ride)
        with CaptureQueriesContext(connection) as ctx:
            admin_client.get("/api/rides/")
        event_sql = [
            q["sql"] for q in ctx.captured_queries if "ride_events" in q["sql"]
        ]
        assert len(event_sql) == 1
        assert "created_at" in event_sql[0]

    def test_todays_events_only_recent(self, admin_client, make_ride, make_event):
        """End-to-end: old events excluded from response."""
        ride = make_ride()
        make_event(ride, "Fresh", timezone.now())
        make_event(ride, "Stale", timezone.now() - timedelta(hours=48))
        response = admin_client.get("/api/rides/")
        events = response.data["results"][0]["todays_ride_events"]
        assert len(events) == 1
        assert events[0]["description"] == "Fresh"
