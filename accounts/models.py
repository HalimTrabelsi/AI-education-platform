from mongoengine import Document, StringField, EmailField
from werkzeug.security import generate_password_hash, check_password_hash


class User(Document):
    meta = {"collection": "users"}

    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = StringField(
        choices=["student", "teacher", "moderator"],
        default="student",
    )

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
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    @property
    def is_staff(self) -> bool:
        return self.role == "moderator"

    @property
    def is_superuser(self) -> bool:
        return self.role == "moderator"

    @property
    def pk(self) -> str:
        return str(self.id)

    def get_full_name(self) -> str:
        return self.username

    def get_short_name(self) -> str:
        return self.username

    def get_session_auth_hash(self) -> str:
        return self.password_hash
