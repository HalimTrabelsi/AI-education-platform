from pathlib import Path
from uuid import uuid4

from django import forms
from django.core.files.storage import default_storage

from .models import User


ROLE_CHOICES = [
    ("student", "Etudiant"),
    ("teacher", "Enseignant"),
    ("moderator", "Moderateur"),
]


class StyledFormMixin:
    """Inject Sneat friendly classes and placeholders on init."""

    widget_classes = {}

    def _apply_widget_attrs(self):
        for name, field in self.fields.items():
            attrs = {"class": "form-control"}
            if isinstance(field.widget, forms.Select):
                attrs["class"] = "form-select"
            if isinstance(field.widget, forms.FileInput):
                attrs.setdefault("accept", "image/*")
            attrs.update(self.widget_classes.get(name, {}))
            field.widget.attrs = {**attrs, **field.widget.attrs}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_widget_attrs()


class RegisterForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur",
        error_messages={"required": "Veuillez saisir un nom d'utilisateur."},
        widget=forms.TextInput(
            attrs={"placeholder": "jdupont", "autocomplete": "username"}
        ),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        error_messages={"required": "Veuillez saisir une adresse e-mail valide."},
        widget=forms.EmailInput(
            attrs={
                "placeholder": "jean.dupont@email.com",
                "autocomplete": "email",
            }
        ),
    )
    password1 = forms.CharField(
        label="Mot de passe",
        error_messages={"required": "Veuillez saisir un mot de passe."},
        widget=forms.PasswordInput(
            attrs={"placeholder": "********", "autocomplete": "new-password"}
        ),
    )
    password2 = forms.CharField(
        label="Confirmation du mot de passe",
        error_messages={"required": "Veuillez confirmer le mot de passe."},
        widget=forms.PasswordInput(
            attrs={"placeholder": "********", "autocomplete": "new-password"}
        ),
    )
    role = forms.ChoiceField(
        label="Role",
        error_messages={"required": "Veuillez choisir un role."},
        choices=ROLE_CHOICES,
        widget=forms.Select(),
    )
    profile_image = forms.ImageField(
        label="Photo de profil",
        required=False,
        error_messages={"invalid": "Veuillez choisir une image valide."},
    )

    widget_classes = {
        "password1": {"class": "form-control input-password-toggle"},
        "password2": {"class": "form-control input-password-toggle"},
        "profile_image": {"class": "form-control"},
    }

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects(username=username):
            raise forms.ValidationError("Nom d'utilisateur deja pris.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects(email=email):
            raise forms.ValidationError("Adresse e-mail deja utilisee.")
        return email

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") and cleaned.get("password2"):
            if cleaned["password1"] != cleaned["password2"]:
                self.add_error("password2", "Les mots de passe ne correspondent pas.")
        return cleaned

    def save(self):
        user = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            role=self.cleaned_data["role"],
        )
        user.set_password(self.cleaned_data["password1"])

        image = self.files.get("profile_image")
        if image:
            ext = Path(image.name).suffix or ".png"
            filename = f"profiles/{uuid4().hex}{ext}"
            stored_path = default_storage.save(filename, image)
            user.profile_image = stored_path.replace("\\", "/")

        user.save()
        return user


class LoginForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        error_messages={"required": "Veuillez saisir votre nom d'utilisateur."},
        widget=forms.TextInput(
            attrs={"placeholder": "jdupont", "autocomplete": "username"}
        ),
    )
    password = forms.CharField(
        label="Mot de passe",
        error_messages={"required": "Veuillez saisir votre mot de passe."},
        widget=forms.PasswordInput(
            attrs={"placeholder": "********", "autocomplete": "current-password"}
        ),
    )
