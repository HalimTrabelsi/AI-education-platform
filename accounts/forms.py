from pathlib import Path
from uuid import uuid4

from django import forms
from django.core.files.storage import default_storage

from .models import User


ROLE_CHOICES = [
    ("student", "Etudiant"),
    ("teacher", "Enseignant"),
    ("moderator", "Moderateur"),
    ("admin", "Administrateur"),
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


class EditProfileForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        max_length=150,
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={"autocomplete": "username"}),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )
    role = forms.ChoiceField(
        label="Role",
        choices=ROLE_CHOICES,
        widget=forms.Select(),
    )
    profile_image = forms.ImageField(
        label="Photo de profil",
        required=False,
    )
    delete_image = forms.BooleanField(
        label="Supprimer la photo actuelle",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    widget_classes = {
        "profile_image": {"class": "form-control"},
    }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        initial = kwargs.setdefault("initial", {})
        if self.user:
            initial.setdefault("username", self.user.username)
            initial.setdefault("email", self.user.email)
            initial.setdefault("role", self.user.role)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data["username"]
        qs = User.objects(username=username)
        if self.user:
            qs = qs.filter(id__ne=self.user.id)
        if qs.first():
            raise forms.ValidationError("Nom d'utilisateur deja pris.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        qs = User.objects(email=email)
        if self.user:
            qs = qs.filter(id__ne=self.user.id)
        if qs.first():
            raise forms.ValidationError("Adresse e-mail deja utilisee.")
        return email

    def save(self):
        if not self.user:
            raise ValueError("User instance is required to save the profile.")

        self.user.username = self.cleaned_data["username"]
        self.user.email = self.cleaned_data["email"]
        self.user.role = self.cleaned_data["role"]

        image = self.files.get("profile_image")
        if image:
            ext = Path(image.name).suffix or ".png"
            filename = f"profiles/{uuid4().hex}{ext}"
            stored_path = default_storage.save(filename, image)
            self.user.profile_image = stored_path.replace("\\", "/")
        elif self.cleaned_data.get("delete_image"):
            self.user.profile_image = None

        self.user.save()
        return self.user


class ForgotPasswordForm(StyledFormMixin, forms.Form):
    username = forms.CharField(
        label="Nom d'utilisateur",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "jdupont"}),
    )
    email = forms.EmailField(
        label="Adresse e-mail",
        required=False,
        widget=forms.EmailInput(attrs={"placeholder": "jean.dupont@email.com"}),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "********"}),
    )
    new_password2 = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"placeholder": "********"}),
    )

    widget_classes = {
        "new_password1": {"class": "form-control input-password-toggle"},
        "new_password2": {"class": "form-control input-password-toggle"},
    }

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get("username")
        email = cleaned.get("email")
        if not username and not email:
            raise forms.ValidationError(
                "Veuillez renseigner votre nom d'utilisateur ou votre adresse e-mail."
            )

        qs = User.objects
        if username:
            qs = qs.filter(username=username)
        if email:
            qs = qs.filter(email=email)

        user = qs.first()
        if not user:
            raise forms.ValidationError("Aucun compte ne correspond aux informations fournies.")

        if cleaned.get("new_password1") != cleaned.get("new_password2"):
            self.add_error("new_password2", "Les mots de passe ne correspondent pas.")

        self.user = user
        return cleaned

    def save(self):
        self.user.set_password(self.cleaned_data["new_password1"])
        self.user.save()
        return self.user
