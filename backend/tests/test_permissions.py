import pytest
from django.contrib.auth.hashers import make_password


@pytest.mark.django_db
class TestAuthentication:
    """Permission tests from docs/artifacts/features/authentication/test-scenarios.md.

    Wrong-password and raw-Basic-header cases previously covered by T-002/T-005
    now live in tests/test_auth.py against the /api/auth/login/ endpoint, which
    is the only way to obtain credentials after the switch to Bearer-only auth.
    """

    def test_admin_force_auth_gets_200(self, admin_client):
        """T-001: Admin via force_authenticate → 200."""
        response = admin_client.get("/api/rides/")
        assert response.status_code == 200

    def test_non_admin_gets_403(self, api_client, non_admin_user):
        """T-003: Non-admin role → 403."""
        api_client.force_authenticate(user=non_admin_user)
        response = api_client.get("/api/rides/")
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self, api_client):
        """T-004: No credentials → 401."""
        response = api_client.get("/api/rides/")
        assert response.status_code == 401

    def test_case_sensitive_role_check(self, api_client, db):
        """T-006: role='Admin' (capital A) ≠ 'admin' → 403."""
        from rides.models import User
        user = User.objects.create(
            first_name="Fake", last_name="Admin",
            email="fakeadmin@wingz.com", role="Admin",
            phone_number="555-9999", password=make_password("pass"),
        )
        api_client.force_authenticate(user=user)
        response = api_client.get("/api/rides/")
        assert response.status_code == 403

    def test_driver_cannot_access(self, api_client, driver):
        """T-007: Driver role → 403."""
        api_client.force_authenticate(user=driver)
        response = api_client.get("/api/rides/")
        assert response.status_code == 403
