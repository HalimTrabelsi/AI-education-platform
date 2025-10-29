from django.contrib.auth import BACKEND_SESSION_KEY


class ForceMongoBackendMiddleware:
    """Ensure sessions use the Mongo backend so AuthenticationMiddleware can load users."""

    def __init__(self, get_response):
        self.get_response = get_response

        self.backend_path = "accounts.backends.MongoUserBackend"
        self.django_backend = "django.contrib.auth.backends.ModelBackend"

    def __call__(self, request):
        if request.session.get(BACKEND_SESSION_KEY) == self.django_backend:
            request.session[BACKEND_SESSION_KEY] = self.backend_path
        return self.get_response(request)

