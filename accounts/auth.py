from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    SESSION_KEY,
    load_backend,
    user_logged_in,
)
from django.contrib.auth.models import AnonymousUser
from django.dispatch import receiver


MONGO_BACKEND_PATH = "accounts.backends.MongoUserBackend"


def get_mongo_user(request):
    if hasattr(request, "_cached_user"):
        return request._cached_user

    user_id = request.session.get(SESSION_KEY)
    backend_path = request.session.get(BACKEND_SESSION_KEY, MONGO_BACKEND_PATH)

    if not user_id:
        user = AnonymousUser()
    else:
        try:
            backend = load_backend(backend_path)
        except Exception:
            backend = load_backend(MONGO_BACKEND_PATH)
        user = backend.get_user(user_id) or AnonymousUser()

    request._cached_user = user
    return user


# Monkeypatch Django's authentication middleware helper
import django.contrib.auth.middleware as auth_middleware

auth_middleware.get_user = get_mongo_user


@receiver(user_logged_in)
def ensure_mongo_backend(sender, user, request, **kwargs):
    request.session[BACKEND_SESSION_KEY] = MONGO_BACKEND_PATH
