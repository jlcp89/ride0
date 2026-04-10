import jwt
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from rides.jwt_service import ACCESS_TYPE, decode_token
from rides.models import User


class JWTAuthentication(BaseAuthentication):
    """
    Stateless JWT auth. Reads `Authorization: Bearer <token>`, validates the
    signature + expiry + type claim, and loads the custom `rides.models.User`.
    Returns None on absent/non-Bearer headers so DRF treats the request as
    unauthenticated, and on user-not-found so stale tokens for deleted users
    fall through to the unauthenticated path cleanly.
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Bearer "):
            return None
        token = auth_header[7:].strip()
        if not token:
            return None
        try:
            payload = decode_token(token, expected_type=ACCESS_TYPE)
        except jwt.InvalidTokenError:
            raise AuthenticationFailed("Invalid or expired token.")
        try:
            user = User.objects.get(id_user=payload["user_id"])
        except User.DoesNotExist:
            return None
        return (user, None)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
