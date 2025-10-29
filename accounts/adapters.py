from types import SimpleNamespace


class DjangoUserAdapter:
    """Wrap a MongoEngine user to satisfy Django auth expectations."""

    class _PK:
        def __init__(self, adapter):
            self.adapter = adapter
            self.attname = "id"

        def value_to_string(self, obj):
            return str(self.adapter.pk)

        def to_python(self, value):
            return str(value)

    def __init__(self, user):
        object.__setattr__(self, "_user", user)
        object.__setattr__(self, "_meta", SimpleNamespace(pk=self._PK(self)))

    def __getattr__(self, item):
        return getattr(self._user, item)

    def __setattr__(self, key, value):
        if key in {"_user", "_meta"}:
            object.__setattr__(self, key, value)
        else:
            setattr(self._user, key, value)

    def __delattr__(self, item):
        if item in {"_user", "_meta"}:
            raise AttributeError(f"Cannot delete attribute {item}")
        delattr(self._user, item)

    def __str__(self):
        return str(self._user)

    @property
    def pk(self):
        return str(self._user.pk)

    @property
    def id(self):
        return self.pk

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return getattr(self._user, "is_active", True)

    @property
    def is_anonymous(self):
        return False

    def get_session_auth_hash(self):
        return getattr(self._user, "password_hash", "")

    def get_document(self):
        return self._user
