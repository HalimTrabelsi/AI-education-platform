from datetime import datetime

from mongoengine import (
    BooleanField,
    DateTimeField,
    DictField,
    Document,
    EmailField,
    StringField,
)
from werkzeug.security import generate_password_hash, check_password_hash


class User(Document):
    meta = {"collection": "users"}

    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = StringField(
        choices=["student", "teacher", "moderator", "admin"],
        default="student",
    )
    profile_image = StringField()
    is_blocked = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    last_login_at = DateTimeField()
    last_password_change_at = DateTimeField()

    def __str__(self) -> str:
        return f"{self.username} ({self.role})"

    # Password helpers -------------------------------------------------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    # Django auth compatibility ----------------------------------------
    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_active(self) -> bool:
        return not self.is_blocked

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_staff(self) -> bool:
        return self.role in {"moderator", "admin"}

    @property
    def is_superuser(self) -> bool:
        return self.role == "admin"

    @property
    def pk(self) -> str:
        return str(self.id)

    def get_full_name(self) -> str:
        return self.username

    def get_short_name(self) -> str:
        return self.username

    def get_session_auth_hash(self) -> str:
        return self.password_hash


class AdminAuditLog(Document):
    meta = {"collection": "admin_audit_log"}

    admin_id = StringField(required=True)
    target_user_id = StringField()
    action = StringField(required=True)
    metadata = DictField()
    created_at = DateTimeField(default=datetime.utcnow)
