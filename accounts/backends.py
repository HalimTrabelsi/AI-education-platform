from bson import ObjectId
from django.contrib.auth.backends import BaseBackend

from .adapters import DjangoUserAdapter
from .models import User


class MongoUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        login_value = username or kwargs.get("email")
        if not login_value:
            return None

        user = User.objects(username=login_value).first()
        if not user:
            user = User.objects(email=login_value).first()

        if user and user.check_password(password):
            return DjangoUserAdapter(user)
        return None

    def get_user(self, user_id):
        try:
            user = User.objects(id=ObjectId(user_id)).first()
        except Exception:
            user = None

        return DjangoUserAdapter(user) if user else None

    def user_can_authenticate(self, user):
        return getattr(user, "is_active", False)
