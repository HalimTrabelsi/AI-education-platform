from mongoengine import Document, StringField, EmailField
from werkzeug.security import generate_password_hash, check_password_hash

class User(Document):
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password_hash = StringField(required=True)
    role = StringField(choices=["student", "teacher", "moderator"])

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
