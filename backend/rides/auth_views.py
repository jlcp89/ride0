"""Auth endpoints: login, refresh, me, logout.

All token work is delegated to `rides.jwt_service` so these views stay thin.
Login and refresh are open; me and logout require authentication with an
explicit `IsAuthenticated` override because the global default permission
class (`IsAdminRole`) does NOT inherit from `IsAuthenticated` and would
reject any non-admin (even the viewer of their own profile).
"""
import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rides.jwt_service import (
    REFRESH_TYPE,
    decode_token,
    encode_access_token,
    encode_refresh_token,
)
from rides.models import User


def _user_payload(user: User) -> dict:
    return {
        "id": user.id_user,
        "email": user.email,
        "role": user.role,
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


def _access_expires_in() -> int:
    return settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES * 60


class LoginView(APIView):
    """POST /api/auth/login/ — exchange email+password for a token pair."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except User.MultipleObjectsReturned:
            return Response(
                {"error": "Multiple accounts exist for this email."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not check_password(password, user.password):
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "access_token": encode_access_token(user),
                "refresh_token": encode_refresh_token(user),
                "expires_in": _access_expires_in(),
                "user": _user_payload(user),
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    """POST /api/auth/refresh/ — exchange a refresh token for a new access token.

    No refresh rotation: the refresh token remains valid until its original
    expiry. Rotation without a blacklist table would be security theater
    because old refresh tokens would still verify against the same secret.
    """

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "refresh_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            payload = decode_token(refresh_token, expected_type=REFRESH_TYPE)
        except jwt.InvalidTokenError:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            user = User.objects.get(id_user=payload["user_id"])
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return Response(
            {
                "access_token": encode_access_token(user),
                "expires_in": _access_expires_in(),
            },
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """GET /api/auth/me/ — return the current user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(_user_payload(request.user), status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/logout/ — stateless courtesy endpoint.

    The server does not track issued tokens, so real invalidation happens
    client-side (drop both tokens). The endpoint returns 204 so clients
    have a consistent "logged out" signal and so authorised callers can
    confirm they are still authenticated at logout time.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
