"""Tests for the JWT auth flow — login, refresh, /me, logout + /rides/ Bearer-only protection."""
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from django.conf import settings
from django.contrib.auth.hashers import make_password

from rides.jwt_service import (
    ACCESS_TYPE,
    REFRESH_TYPE,
    encode_access_token,
    encode_refresh_token,
)
from tests.conftest import ADMIN_PASSWORD

LOGIN_URL = "/api/auth/login/"
REFRESH_URL = "/api/auth/refresh/"
ME_URL = "/api/auth/me/"
LOGOUT_URL = "/api/auth/logout/"
RIDES_URL = "/api/rides/"


def _bearer(token: str) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {token}"}


def _expired_token(user, token_type: str) -> str:
    """Mint a token whose exp is already in the past."""
    past = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    payload = {
        "user_id": user.id_user,
        "type": token_type,
        "iat": int(past.timestamp()) - 10,
        "exp": int(past.timestamp()),
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


@pytest.mark.django_db
class TestLogin:
    """POST /api/auth/login/ — AllowAny, authentication_classes=[]."""

    def test_valid_credentials_returns_tokens_and_user(self, api_client, admin_user):
        """L-001: Correct email+password → 200 with access, refresh, expires_in, user."""
        response = api_client.post(
            LOGIN_URL,
            {"email": admin_user.email, "password": ADMIN_PASSWORD},
            format="json",
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body and body["access_token"]
        assert "refresh_token" in body and body["refresh_token"]
        assert body["expires_in"] == settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES * 60
        assert body["user"] == {
            "id": admin_user.id_user,
            "email": admin_user.email,
            "role": "admin",
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
        }

    def test_wrong_password_returns_401(self, api_client, admin_user):
        """L-002: Wrong password → 401 with generic error."""
        response = api_client.post(
            LOGIN_URL,
            {"email": admin_user.email, "password": "wrongpass"},
            format="json",
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Invalid credentials."}

    def test_unknown_email_returns_401(self, api_client, db):
        """L-003: Unknown email → 401 (same generic error, no enumeration)."""
        response = api_client.post(
            LOGIN_URL,
            {"email": "ghost@wingz.com", "password": "whatever"},
            format="json",
        )
        assert response.status_code == 401
        assert response.json() == {"error": "Invalid credentials."}

    def test_missing_email_returns_400(self, api_client, db):
        """L-004: Missing email → 400."""
        response = api_client.post(
            LOGIN_URL, {"password": "whatever"}, format="json"
        )
        assert response.status_code == 400

    def test_missing_password_returns_400(self, api_client, db):
        """L-005: Missing password → 400."""
        response = api_client.post(
            LOGIN_URL, {"email": "a@b.com"}, format="json"
        )
        assert response.status_code == 400

    def test_duplicate_email_returns_400(self, api_client, db):
        """L-006: email field has no DB unique constraint — handle gracefully."""
        from rides.models import User
        User.objects.create(
            first_name="A", last_name="One", email="dup@wingz.com",
            role="admin", phone_number="555-1", password=make_password("p1"),
        )
        User.objects.create(
            first_name="B", last_name="Two", email="dup@wingz.com",
            role="admin", phone_number="555-2", password=make_password("p2"),
        )
        response = api_client.post(
            LOGIN_URL, {"email": "dup@wingz.com", "password": "p1"}, format="json"
        )
        assert response.status_code == 400
        assert "Multiple" in response.json()["error"]


@pytest.mark.django_db
class TestRefresh:
    """POST /api/auth/refresh/ — AllowAny, no rotation."""

    def test_valid_refresh_returns_new_access(self, api_client, admin_user):
        """R-001: Valid refresh token → 200 with new access token."""
        refresh = encode_refresh_token(admin_user)
        response = api_client.post(
            REFRESH_URL, {"refresh_token": refresh}, format="json"
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body and body["access_token"]
        assert body["expires_in"] == settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES * 60
        assert "refresh_token" not in body  # no rotation

    def test_access_token_rejected_as_refresh(self, api_client, admin_user):
        """R-002: Sending an access token to /refresh/ → 401 (type claim check)."""
        access = encode_access_token(admin_user)
        response = api_client.post(
            REFRESH_URL, {"refresh_token": access}, format="json"
        )
        assert response.status_code == 401

    def test_garbage_refresh_returns_401(self, api_client, db):
        """R-003: Malformed token → 401."""
        response = api_client.post(
            REFRESH_URL, {"refresh_token": "not-a-jwt"}, format="json"
        )
        assert response.status_code == 401

    def test_expired_refresh_returns_401(self, api_client, admin_user):
        """R-004: Expired refresh token → 401."""
        expired = _expired_token(admin_user, REFRESH_TYPE)
        response = api_client.post(
            REFRESH_URL, {"refresh_token": expired}, format="json"
        )
        assert response.status_code == 401

    def test_missing_refresh_returns_400(self, api_client, db):
        """R-005: No refresh_token in body → 400."""
        response = api_client.post(REFRESH_URL, {}, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestMe:
    """GET /api/auth/me/ — IsAuthenticated, any logged-in role (not just admin)."""

    def test_valid_access_returns_user(self, api_client, admin_user):
        """M-001: Valid access token → 200 with user payload."""
        token = encode_access_token(admin_user)
        response = api_client.get(ME_URL, **_bearer(token))
        assert response.status_code == 200
        assert response.json() == {
            "id": admin_user.id_user,
            "email": admin_user.email,
            "role": "admin",
            "first_name": admin_user.first_name,
            "last_name": admin_user.last_name,
        }

    def test_non_admin_can_see_their_own_profile(self, api_client, non_admin_user):
        """M-002: /me is available to non-admins (global IsAdminRole is overridden)."""
        token = encode_access_token(non_admin_user)
        response = api_client.get(ME_URL, **_bearer(token))
        assert response.status_code == 200
        assert response.json()["role"] == "rider"

    def test_no_credentials_returns_401(self, api_client, db):
        """M-003: No Authorization header → 401."""
        response = api_client.get(ME_URL)
        assert response.status_code == 401

    def test_refresh_token_rejected_as_access(self, api_client, admin_user):
        """M-004: Sending a refresh token as Bearer → 401 (type claim check)."""
        refresh = encode_refresh_token(admin_user)
        response = api_client.get(ME_URL, **_bearer(refresh))
        assert response.status_code == 401

    def test_expired_access_returns_401(self, api_client, admin_user):
        """M-005: Expired access token → 401."""
        expired = _expired_token(admin_user, ACCESS_TYPE)
        response = api_client.get(ME_URL, **_bearer(expired))
        assert response.status_code == 401

    def test_garbage_token_returns_401(self, api_client, db):
        """M-006: Malformed Bearer token → 401."""
        response = api_client.get(ME_URL, **_bearer("not-a-jwt"))
        assert response.status_code == 401


@pytest.mark.django_db
class TestLogout:
    """POST /api/auth/logout/ — IsAuthenticated, stateless 204."""

    def test_authenticated_logout_returns_204(self, api_client, admin_user):
        """O-001: Authenticated logout → 204 No Content."""
        token = encode_access_token(admin_user)
        response = api_client.post(LOGOUT_URL, **_bearer(token))
        assert response.status_code == 204

    def test_unauthenticated_logout_returns_401(self, api_client, db):
        """O-002: No token → 401."""
        response = api_client.post(LOGOUT_URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestRidesBearerProtection:
    """JWT is the only accepted credential on /api/rides/ — no Basic Auth fallback."""

    def test_jwt_access_token_on_rides(self, api_client, admin_user):
        """F-001: /api/rides/ accepts a JWT access token for an admin."""
        token = encode_access_token(admin_user)
        response = api_client.get(RIDES_URL, **_bearer(token))
        assert response.status_code == 200

    def test_basic_auth_is_rejected_on_rides(self, api_client, admin_user):
        """F-002: Sending HTTP Basic credentials returns 401 — Basic Auth is disabled."""
        import base64
        credentials = base64.b64encode(
            f"{admin_user.email}:{ADMIN_PASSWORD}".encode()
        ).decode()
        response = api_client.get(
            RIDES_URL, HTTP_AUTHORIZATION=f"Basic {credentials}"
        )
        assert response.status_code == 401

    def test_no_credentials_on_rides_returns_401(self, api_client, db):
        """F-003: No Authorization header → 401."""
        response = api_client.get(RIDES_URL)
        assert response.status_code == 401

    def test_non_admin_jwt_on_rides_returns_403(self, api_client, non_admin_user):
        """F-004: JWT auth resolves, but IsAdminRole rejects non-admins → 403."""
        token = encode_access_token(non_admin_user)
        response = api_client.get(RIDES_URL, **_bearer(token))
        assert response.status_code == 403
