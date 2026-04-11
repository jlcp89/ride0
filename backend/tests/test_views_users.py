import pytest
from django.contrib.auth.hashers import make_password
from django.db import connection
from django.test.utils import CaptureQueriesContext

from rides.models import User


def _extra_users(n, *, role="rider"):
    """Create N additional users with distinct emails."""
    return [
        User.objects.create(
            first_name=f"User{i}", last_name="Extra",
            email=f"extra{i}@example.com", role=role,
            phone_number=f"555-10{i:02d}",
            password=make_password("pw"),
        )
        for i in range(n)
    ]


@pytest.mark.django_db
class TestUserList:
    def test_admin_lists_all_users_200(self, admin_client, rider, driver):
        """T-201: Admin GET /api/users/ → 200 with all seeded users."""
        response = admin_client.get("/api/users/")
        assert response.status_code == 200
        emails = {u["email"] for u in response.data["results"]}
        assert "admin@wingz.com" in emails
        assert "rider1@wingz.com" in emails
        assert "chris@wingz.com" in emails
        # Response has the 6 expected fields, including role, and no password.
        first = response.data["results"][0]
        assert set(first.keys()) == {
            "id_user", "role", "first_name", "last_name", "email", "phone_number",
        }
        assert "password" not in first

    def test_non_admin_list_403(self, api_client, non_admin_user):
        """T-202: Non-admin GET /api/users/ → 403 (IsAdminRole)."""
        api_client.force_authenticate(user=non_admin_user)
        response = api_client.get("/api/users/")
        assert response.status_code == 403

    def test_unauthenticated_list_401(self, api_client):
        """T-203: Anonymous GET /api/users/ → 401."""
        response = api_client.get("/api/users/")
        assert response.status_code == 401

    def test_pagination_respects_page_size(self, admin_client, rider, driver):
        """T-204: page_size=2 returns exactly 2 results with a next cursor."""
        _extra_users(5)
        response = admin_client.get("/api/users/?page_size=2")
        assert response.status_code == 200
        assert len(response.data["results"]) == 2
        assert response.data["next"] is not None
        assert response.data["count"] >= 7  # admin + rider + driver + 5 extras

    def test_query_budget(self, admin_client, rider, driver):
        """T-205: GET /api/users/ stays bounded (COUNT + SELECT + session)."""
        _extra_users(10)
        with CaptureQueriesContext(connection) as ctx:
            response = admin_client.get("/api/users/?page_size=100")
        assert response.status_code == 200
        assert len(ctx.captured_queries) <= 3, (
            f"GET /api/users/ used {len(ctx.captured_queries)} queries: "
            f"{[q['sql'] for q in ctx.captured_queries]}"
        )
