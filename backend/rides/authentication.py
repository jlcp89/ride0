from rest_framework.authentication import BaseAuthentication


class EmailBasicAuthentication(BaseAuthentication):
    def authenticate(self, request):
        return None
