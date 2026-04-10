import base64

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.hashers import check_password

from rides.models import User


class EmailBasicAuthentication(BaseAuthentication):
    """
    HTTP Basic Auth against our custom User model.
    Credentials: email:password (not username:password).
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        if not auth_header.startswith("Basic "):
            return None
        try:
            decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
            email, password = decoded.split(":", 1)
        except (ValueError, UnicodeDecodeError):
            raise AuthenticationFailed("Invalid basic auth header.")
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid credentials.")
        if not check_password(password, user.password):
            raise AuthenticationFailed("Invalid credentials.")
        return (user, None)

    def authenticate_header(self, request):
        return 'Basic realm="api"'
