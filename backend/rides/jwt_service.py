"""JWT encode/decode helpers for the stateless auth flow.

Signed HS256 tokens with a `type` claim so access tokens cannot be used
where a refresh token is expected and vice versa. No state is kept on the
server — verification is a signature check + expiry check.
"""
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings

ACCESS_TYPE = "access"
REFRESH_TYPE = "refresh"


def _encode(user, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "user_id": user.id_user,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + lifetime).timestamp()),
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def encode_access_token(user) -> str:
    lifetime = timedelta(minutes=settings.JWT_ACCESS_TOKEN_LIFETIME_MINUTES)
    return _encode(user, ACCESS_TYPE, lifetime)


def encode_refresh_token(user) -> str:
    lifetime = timedelta(days=settings.JWT_REFRESH_TOKEN_LIFETIME_DAYS)
    return _encode(user, REFRESH_TYPE, lifetime)


def decode_token(token: str, expected_type: str) -> dict:
    """Decode and validate a token. Raises jwt.InvalidTokenError on any failure
    (bad signature, expired, wrong type, missing claims)."""
    payload = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(
            f"Expected token type '{expected_type}', got '{payload.get('type')}'."
        )
    if "user_id" not in payload:
        raise jwt.InvalidTokenError("Missing user_id claim.")
    return payload
