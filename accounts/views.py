from django.contrib import messages
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    login as auth_login,
)
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse

from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from .adapters import DjangoUserAdapter
from .backends import MongoUserBackend
from .forms import EditProfileForm, ForgotPasswordForm, LoginForm, RegisterForm


DEFAULT_DASHBOARD_ROUTE = "dashboards:home"
ROLE_ROUTE_MAP = {
    "teacher": DEFAULT_DASHBOARD_ROUTE,
    "moderator": DEFAULT_DASHBOARD_ROUTE,
    "student": DEFAULT_DASHBOARD_ROUTE,
}


def _auth_context(initial_context=None):
    context = TemplateLayout().init(initial_context or {})
    context["menu_fixed"] = False
    context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)
    return context


def _redirect_for_role(user):
    target = ROLE_ROUTE_MAP.get(user.role, DEFAULT_DASHBOARD_ROUTE)
    try:
        reverse(target)
        return target
    except NoReverseMatch:
        return DEFAULT_DASHBOARD_ROUTE


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Compte cree avec succes ! Veuillez vous connecter.")
            return redirect("accounts:login")
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = RegisterForm()

    context = _auth_context({"form": form})
    return render(request, "accounts/register.html", context)


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            backend = MongoUserBackend()
            user = backend.authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                request.session.pop(SESSION_KEY, None)
                auth_login(request, user, backend="accounts.backends.MongoUserBackend")
                messages.success(request, "Connexion reussie.")
                return redirect(_redirect_for_role(user))
            messages.error(request, "Identifiants invalides.")
    else:
        form = LoginForm()

    context = _auth_context({"form": form})
    return render(request, "accounts/login.html", context)


def logout_view(request):
    for key in (SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY):
        request.session.pop(key, None)

    request.session.flush()
    messages.info(request, "Vous etes maintenant deconnecte.")
    return redirect("accounts:login")


@login_required
def profile_edit_view(request):
    user_doc = request.user.get_document() if hasattr(request.user, "get_document") else request.user

    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, user=user_doc)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil mis à jour avec succès.")
            return redirect("pages-account-settings-account")
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = EditProfileForm(user=user_doc)

    context = TemplateLayout().init({"form": form})
    context["page_title"] = "Paramètres du profil"
    return render(request, "pages_account_settings_account.html", context)


def forgot_password_view(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe réinitialisé. Vous pouvez vous connecter.")
            return redirect("accounts:login")
        messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    else:
        form = ForgotPasswordForm()

    context = _auth_context({"form": form})
    return render(request, "auth_forgot_password_basic.html", context)


def home_redirect_view(request):
    if request.user.is_authenticated:
        return redirect(_redirect_for_role(request.user))
    return redirect("accounts:login")
