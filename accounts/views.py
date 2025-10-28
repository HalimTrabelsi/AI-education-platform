from django.contrib import messages
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    login as auth_login,
)
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse

from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from .adapters import DjangoUserAdapter
from .backends import MongoUserBackend
from .forms import LoginForm, RegisterForm


ROLE_ROUTE_MAP = {
    "teacher": "dashboard_teacher",
    "moderator": "dashboard_moderator",
    "student": "dashboard_student",
}


def _auth_context(initial_context=None):
    context = TemplateLayout().init(initial_context or {})
    context["menu_fixed"] = False
    context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)
    return context


def _redirect_for_role(user):
    target = ROLE_ROUTE_MAP.get(user.role)
    if target:
        try:
            reverse(target)
            return target
        except NoReverseMatch:
            pass
    return "index"


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = DjangoUserAdapter(form.save())
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
                # NE PAS utiliser auth_login() - gérer manuellement la session
                
                # Nettoyer la session existante
                request.session.flush()
                
                # Créer manuellement la session utilisateur
                request.session[SESSION_KEY] = str(user.pk)  # Stocker l'ID comme chaîne
                request.session[BACKEND_SESSION_KEY] = 'accounts.backends.MongoUserBackend'
                request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
                
                # Sauvegarder la session
                request.session.save()
                
                # Régénérer la clé de session pour sécurité
                request.session.cycle_key()
                
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
