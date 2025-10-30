from collections import Counter
from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from accounts.constants import ROLE_CHOICES, ROLE_LABELS, get_dashboard_route
from accounts.models import AdminAuditLog, User
from web_project import TemplateLayout

from resources.models import Resource
from quiz.models import Quiz, QuizAttempt

class DashboardRedirectView(LoginRequiredMixin, View):
    """Redirect authenticated users to the dashboard associated with their role."""

    def get(self, request, *args, **kwargs):
        return redirect(get_dashboard_route(getattr(request.user, "role", None)))


class RoleDashboardMixin(LoginRequiredMixin, TemplateView):

    allowed_roles: list[str] | None = None

    def dispatch(self, request, *args, **kwargs):
        role = getattr(request.user, "role", None)
        if self.allowed_roles and role not in self.allowed_roles:
            return redirect(get_dashboard_route(role))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return TemplateLayout.init(self, super().get_context_data(**kwargs))


class StudentDashboardView(RoleDashboardMixin):
    template_name = "dashboard_student.html"
    allowed_roles = ["student"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resources = list(Resource.objects.order_by("-uploaded_at"))
        quizzes = list(Quiz.objects.order_by("-created_at"))
        user_id = str(getattr(self.request.user, "pk", ""))
        attempts = list(QuizAttempt.objects(user_id=user_id))
        attempts_map = {attempt.quiz.id: attempt for attempt in attempts}

        context.update(
            {
                "resources": resources,
                "total_courses": len(resources),
                "completed_courses": len({a.quiz.id for a in attempts}),
                "bookmarked_courses": 0,
                "recent_courses": resources[:3],
                "available_quizzes": len(quizzes),
                "quiz_list": quizzes,
                "quiz_attempts": attempts_map,
            }
        )
        return context


class TeacherDashboardView(RoleDashboardMixin):
    template_name = "dashboard_teacher.html"
    allowed_roles = ["teacher"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        resources = list(Resource.objects.order_by("-uploaded_at"))
        resource_types = {
            getattr(res, "resource_type", "") or "Autre" for res in resources
        }
        context.update(
            {
                "resources": resources,
                "total_resources": len(resources),
                "resource_types_count": len(resource_types),
                "available_quizzes": Quiz.objects.count(),
            }
        )
        return context


class ModeratorDashboardView(RoleDashboardMixin):
    template_name = "dashboard_moderator.html"
    allowed_roles = ["moderator"]


class AdminDashboardView(RoleDashboardMixin):
    template_name = "dashboard_admin.html"
    allowed_roles = ["admin"]
    STATUS_OPTIONS = [
        ("", "Tous"),
        ("active", "Actifs"),
        ("blocked", "Bloques"),
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filters = self._build_filters()

        all_users = list(User.objects.order_by("-created_at"))
        filtered_users = self._apply_filters(all_users, filters)

        total_users = len(all_users)
        blocked_users = sum(1 for u in all_users if getattr(u, "is_blocked", False))
        role_counts = Counter(getattr(u, "role", "inconnu") for u in all_users)
        role_counts_prepared = [
            (ROLE_LABELS.get(role, role.title()), count)
            for role, count in sorted(role_counts.items(), key=lambda item: item[0])
        ]

        recent_logs = list(AdminAuditLog.objects.order_by("-created_at").limit(8))
        action_labels = {
            "create_user": "Création de compte",
            "block_user": "Blocage d'utilisateur",
            "unblock_user": "Déblocage d'utilisateur",
            "change_role": "Changement de rôle",
            "reset_password": "Réinitialisation de mot de passe",
            "send_onboarding": "Envoi d'onboarding",
            "impersonate_start": "Impersonation démarrée",
            "impersonate_stop": "Impersonation terminée",
        }
        for log in recent_logs:
            setattr(log, "display_action", action_labels.get(log.action, log.action))

        context.update(
            {
                "users": filtered_users,
                "total_users": total_users,
                "blocked_users": blocked_users,
                "active_users": total_users - blocked_users,
                "role_counts": role_counts_prepared,
                "role_options": ROLE_CHOICES,
                "status_options": self.STATUS_OPTIONS,
                "filters": filters,
                "filtered_count": len(filtered_users),
                "recent_logs": recent_logs,
                "has_active_filters": any(value for value in filters.values()),
            }
        )
        return context

    def _build_filters(self):
        request = self.request
        return {
            "role": request.GET.get("role", "").strip(),
            "status": request.GET.get("status", "").strip(),
            "created_start": request.GET.get("created_start", "").strip(),
            "created_end": request.GET.get("created_end", "").strip(),
            "last_login_start": request.GET.get("last_login_start", "").strip(),
            "last_login_end": request.GET.get("last_login_end", "").strip(),
            "search": request.GET.get("search", "").strip(),
        }

    def _apply_filters(self, users, filters):
        result = users

        role = filters.get("role")
        if role:
            result = [u for u in result if getattr(u, "role", None) == role]

        status = filters.get("status")
        if status == "active":
            result = [u for u in result if not getattr(u, "is_blocked", False)]
        elif status == "blocked":
            result = [u for u in result if getattr(u, "is_blocked", False)]

        created_start = self._parse_date(filters.get("created_start"))
        if created_start:
            result = [
                u
                for u in result
                if getattr(u, "created_at", None)
                and u.created_at >= created_start
            ]

        created_end = self._parse_date(filters.get("created_end"))
        if created_end:
            inclusive_end = created_end + timedelta(days=1)
            result = [
                u
                for u in result
                if getattr(u, "created_at", None)
                and u.created_at < inclusive_end
            ]

        login_start = self._parse_date(filters.get("last_login_start"))
        if login_start:
            result = [
                u
                for u in result
                if getattr(u, "last_login_at", None)
                and u.last_login_at >= login_start
            ]

        login_end = self._parse_date(filters.get("last_login_end"))
        if login_end:
            inclusive_login_end = login_end + timedelta(days=1)
            result = [
                u
                for u in result
                if getattr(u, "last_login_at", None)
                and u.last_login_at < inclusive_login_end
            ]

        search = filters.get("search", "").lower()
        if search:
            result = [
                u
                for u in result
                if search in getattr(u, "username", "").lower()
                or search in (getattr(u, "email", "") or "").lower()
            ]

        return result

    @staticmethod
    def _parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return None

