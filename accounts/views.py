from datetime import datetime
from secrets import token_urlsafe

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import (
    BACKEND_SESSION_KEY,
    HASH_SESSION_KEY,
    SESSION_KEY,
    login as auth_login,
)
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMultiAlternatives
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.template.loader import render_to_string

from web_project import TemplateLayout
from web_project.template_helpers.theme import TemplateHelper

from .adapters import DjangoUserAdapter
from .backends import MongoUserBackend
from .constants import ROLE_CHOICES, get_dashboard_route
from .forms import (
    ChangePasswordForm,
    EditProfileForm,
    ForgotPasswordForm,
    LoginForm,
    RegisterForm,
)
from .models import AdminAuditLog, User


def _auth_context(initial_context=None):
    context = TemplateLayout().init(initial_context or {})
    context["menu_fixed"] = False
    context["layout_path"] = TemplateHelper.set_layout("layout_blank.html", context)
    return context


def _redirect_for_role(user):
    target = get_dashboard_route(getattr(user, "role", None))
    try:
        reverse(target)
        return target
    except NoReverseMatch:
        return target



def _log_admin_action(admin_user, target_ids, action, metadata=None):
    admin_pk = str(getattr(admin_user, 'pk', ''))
    if not admin_pk:
        return
    AdminAuditLog(
        admin_id=admin_pk,
        target_user_id=','.join(target_ids) if target_ids else None,
        action=action,
        metadata=metadata or {},
    ).save()


def _send_onboarding_email(user):
    email_address = getattr(user, "email", None)
    if not email_address:
        return False, "Aucune adresse e-mail"

    theme_vars = getattr(settings, "THEME_VARIABLES", {}) or {}
    site_name = (
        getattr(settings, "SITE_NAME", None)
        or theme_vars.get("template_name")
        or "EduSocial"
    )
    try:
        login_path = reverse("accounts:login")
    except NoReverseMatch:
        login_path = "/accounts/login/"
    base_url = getattr(settings, "BASE_URL", "http://127.0.0.1:8000").rstrip("/")

    context = {
        "user_name": getattr(user, "username", "") or email_address,
        "username": getattr(user, "username", "") or email_address,
        "site_name": site_name,
        "login_url": f"{base_url}{login_path}",
    }

    subject = f"Bienvenue sur {site_name}"
    text_body = render_to_string("accounts/emails/onboarding_email.txt", context)
    html_body = render_to_string("accounts/emails/onboarding_email.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[email_address],
    )
    message.attach_alternative(html_body, "text/html")

    try:
        message.send()
    except Exception as exc:  # pragma: no cover - depends on SMTP availability
        return False, str(exc)

    return True, None

@login_required
def register_view(request):
    if request.user.role != 'admin':
        messages.error(request, "Acces reserve a l'administrateur.")
        return redirect(_redirect_for_role(request.user))

    if request.method == "POST":
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            created_user = form.save()
            _log_admin_action(request.user, [str(created_user.id)], "create_user", {"role": created_user.role})
            messages.success(request, "Compte cree avec succes.")
            return redirect('dashboards:admin')
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
                try:
                    user_doc = user.get_document()
                except AttributeError:
                    user_doc = None
                if user_doc:
                    user_doc.last_login_at = datetime.utcnow()
                    user_doc.save()
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

    request.session.pop('_impersonator_id', None)
    request.session.flush()
    messages.info(request, "Vous etes maintenant deconnecte.")
    return redirect("accounts:login")


@login_required
def profile_edit_view(request):
    user_doc = request.user.get_document() if hasattr(request.user, "get_document") else request.user

    if request.method == "POST" and "profile_submit" in request.POST:
        profile_form = EditProfileForm(request.POST, request.FILES, user=user_doc)
        password_form = ChangePasswordForm(user=user_doc)
        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profil mis a jour avec succes.")
            return redirect("pages-account-settings-account")
        messages.error(request, "Veuillez corriger les erreurs du formulaire de profil.")
    elif request.method == "POST" and "password_submit" in request.POST:
        profile_form = EditProfileForm(user=user_doc)
        password_form = ChangePasswordForm(request.POST, user=user_doc)
        if password_form.is_valid():
            password_form.save()
            messages.success(request, "Mot de passe mis a jour avec succes.")
            return redirect("pages-account-settings-account")
        messages.error(request, "Veuillez corriger les erreurs du formulaire de mot de passe.")
    else:
        profile_form = EditProfileForm(user=user_doc)
        password_form = ChangePasswordForm(user=user_doc)

    context = TemplateLayout().init({"profile_form": profile_form, "password_form": password_form})
    context["page_title"] = "Parametres du profil"
    return render(request, "pages_account_settings_account.html", context)


def forgot_password_view(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe reinitialise. Vous pouvez vous connecter.")
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


@login_required
def toggle_user_block(request, user_id):
    if getattr(request.user, "role", None) != "admin":
        messages.error(request, "Acces reserve a l'administrateur.")
        return redirect(_redirect_for_role(request.user))

    if request.method != "POST":
        return redirect('dashboards:admin')

    target = User.objects(id=user_id).first()
    if not target:
        messages.error(request, "Utilisateur introuvable.")
        return redirect("dashboards:admin")

    if target.role == "admin":
        messages.error(request, "Impossible de modifier le statut d'un administrateur.")
        return redirect("dashboards:admin")

    current_user_id = str(getattr(request.user, "pk", ""))
    if str(target.id) == current_user_id:
        messages.error(request, "Vous ne pouvez pas bloquer votre propre compte.")
        return redirect("dashboards:admin")

    target.is_blocked = not target.is_blocked
    target.save()

    action = "block_user" if target.is_blocked else "unblock_user"
    _log_admin_action(request.user, [str(target.id)], action)

    if target.is_blocked:
        messages.success(request, f"Le compte {target.username} est maintenant bloque.")
    else:
        messages.success(request, f"Le compte {target.username} est de nouveau actif.")

    return redirect("dashboards:admin")


@login_required
def admin_bulk_user_action(request):
    if getattr(request.user, "role", None) != "admin":
        messages.error(request, "Acces reserve a l'administrateur.")
        return redirect(_redirect_for_role(request.user))

    if request.method != "POST":
        return redirect("dashboards:admin")

    user_ids = request.POST.getlist("user_ids")
    action = request.POST.get("bulk_action")
    if not user_ids or not action:
        messages.error(request, "Veuillez selectionner au moins un utilisateur et une action.")
        return redirect("dashboards:admin")

    users = list(User.objects(id__in=user_ids))
    if not users:
        messages.error(request, "Aucun utilisateur valide trouve.")
        return redirect("dashboards:admin")

    processed = []
    skipped = []

    if action == "block":
        for user in users:
            if user.role == "admin":
                skipped.append(user.username)
                continue
            if not user.is_blocked:
                user.is_blocked = True
                user.save()
                processed.append(user)
        if processed:
            _log_admin_action(
                request.user, [str(u.id) for u in processed], "block_user", {"count": len(processed)}
            )
            messages.success(request, f"{len(processed)} compte(s) bloques.")
        if skipped:
            messages.warning(request, f"Impossible de bloquer: {', '.join(skipped)}.")

    elif action == "unblock":
        for user in users:
            if user.is_blocked:
                user.is_blocked = False
                user.save()
                processed.append(user)
        if processed:
            _log_admin_action(
                request.user, [str(u.id) for u in processed], "unblock_user", {"count": len(processed)}
            )
            messages.success(request, f"{len(processed)} compte(s) reactives.")

    elif action == "change_role":
        new_role = request.POST.get("new_role")
        valid_roles = {value for value, _ in ROLE_CHOICES}
        if new_role not in valid_roles:
            messages.error(request, "Role cible invalide.")
            return redirect("dashboards:admin")
        for user in users:
            if str(user.id) == str(getattr(request.user, "pk", "")):
                skipped.append(user.username)
                continue
            user.role = new_role
            user.save()
            processed.append(user)
        if processed:
            _log_admin_action(
                request.user,
                [str(u.id) for u in processed],
                "change_role",
                {"new_role": new_role, "count": len(processed)},
            )
            messages.success(request, f"Role mis a jour pour {len(processed)} utilisateur(s).")
        if skipped:
            messages.warning(request, f"Role non modifie pour: {', '.join(skipped)}.")

    elif action == "reset_password":
        reset_info = []
        for user in users:
            temp_password = token_urlsafe(8)[:12]
            user.set_password(temp_password)
            user.last_password_change_at = datetime.utcnow()
            user.save()
            reset_info.append((user.username, temp_password))
        if reset_info:
            _log_admin_action(
                request.user,
                [str(u.id) for u in users],
                "reset_password",
                {"count": len(reset_info)},
            )
            details = ", ".join([f"{username}: {pwd}" for username, pwd in reset_info])
            messages.success(
                request,
                f"Mot de passe reinitialise pour {len(reset_info)} utilisateur(s). {details}",
            )

    elif action == "send_onboarding":
        sent = 0
        failures = []
        successful_ids = []
        for user in users:
            success, error = _send_onboarding_email(user)
            if success:
                sent += 1
                successful_ids.append(str(user.id))
            else:
                identifier = getattr(user, "username", None) or getattr(user, "email", None) or str(user.id)
                failures.append(f"{identifier}: {error}")

        if sent:
            _log_admin_action(
                request.user,
                successful_ids,
                "send_onboarding",
                {"count": sent},
            )
            messages.success(
                request,
                f"Message d'onboarding envoyé pour {sent} utilisateur(s).",
            )
        if failures:
            messages.warning(
                request,
                "Impossible d'envoyer pour : " + "; ".join(failures),
            )
        if not sent and not failures:
            messages.info(
                request,
                "Aucun e-mail d'onboarding n'a été envoyé.",
            )

    else:
        messages.error(request, "Action inconnue.")

    return redirect("dashboards:admin")


@login_required
def admin_impersonate_user(request, user_id):
    if getattr(request.user, "role", None) != "admin":
        messages.error(request, "Acces reserve a l'administrateur.")
        return redirect(_redirect_for_role(request.user))

    if request.method != "POST":
        return redirect("dashboards:admin")

    if request.session.get("_impersonator_id"):
        messages.error(request, "Une session d'impersonation est deja active.")
        return redirect("dashboards:admin")

    target = User.objects(id=user_id).first()
    if not target:
        messages.error(request, "Utilisateur introuvable.")
        return redirect("dashboards:admin")

    if target.role == "admin":
        messages.error(request, "Impossible d'impersoner un autre administrateur.")
        return redirect("dashboards:admin")

    admin_pk = str(getattr(request.user, "pk", ""))
    admin_user = request.user

    adapter = DjangoUserAdapter(target)
    _log_admin_action(admin_user, [str(target.id)], "impersonate_start")

    for key in (SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY):
        request.session.pop(key, None)

    auth_login(request, adapter, backend="accounts.backends.MongoUserBackend")
    request.session["_impersonator_id"] = admin_pk
    request.session[BACKEND_SESSION_KEY] = "accounts.backends.MongoUserBackend"
    messages.info(request, f"Impersonation active sur {target.username}.")
    return redirect(_redirect_for_role(adapter))


@login_required
def admin_stop_impersonation(request):
    if request.method != "POST":
        return redirect(_redirect_for_role(request.user))

    impersonator_id = request.session.get("_impersonator_id")
    if not impersonator_id:
        messages.error(request, "Aucune session d'impersonation en cours.")
        return redirect(_redirect_for_role(request.user))

    admin_user = User.objects(id=impersonator_id).first()
    if not admin_user:
        request.session.pop("_impersonator_id", None)
        messages.error(
            request, "Administrateur d'origine introuvable. Veuillez vous reconnecter."
        )
        return redirect("accounts:login")

    adapter = DjangoUserAdapter(admin_user)

    for key in (SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY):
        request.session.pop(key, None)

    auth_login(request, adapter, backend="accounts.backends.MongoUserBackend")
    request.session[BACKEND_SESSION_KEY] = "accounts.backends.MongoUserBackend"
    request.session.pop("_impersonator_id", None)
    _log_admin_action(admin_user, [], "impersonate_stop")
    messages.info(request, "Impersonation terminee.")
    return redirect("dashboards:admin")

