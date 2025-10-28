from collections import Counter
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View
from django.views.generic import TemplateView

from accounts.constants import get_dashboard_route
from accounts.models import User
from web_project import TemplateLayout


class DashboardRedirectView(LoginRequiredMixin, View):
    """Redirect authenticated users to the dashboard associated with their role."""

    def get(self, request, *args, **kwargs):
        return redirect(get_dashboard_route(getattr(request.user, "role", None)))


class RoleDashboardMixin(LoginRequiredMixin, TemplateView):
    """Base class that protects a dashboard page by role and loads the Sneat layout."""

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


class TeacherDashboardView(RoleDashboardMixin):
    template_name = "dashboard_teacher.html"
    allowed_roles = ["teacher"]


class ModeratorDashboardView(RoleDashboardMixin):
    template_name = "dashboard_moderator.html"
    allowed_roles = ["moderator"]


class AdminDashboardView(RoleDashboardMixin):
    template_name = "dashboard_admin.html"
    allowed_roles = ["admin"]

    ROLE_LABELS = {
        "student": "Etudiant",
        "teacher": "Enseignant",
        "moderator": "Moderateur",
        "admin": "Administrateur",
    }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users = list(User.objects.order_by("username"))
        total_users = len(users)
        blocked_users = sum(1 for u in users if getattr(u, "is_blocked", False))
        role_counts = Counter(getattr(u, "role", "inconnu") for u in users)
        role_counts_prepared = [
            (self.ROLE_LABELS.get(role, role.title()), count)
            for role, count in sorted(role_counts.items(), key=lambda item: item[0])
        ]

        context.update({
            "users": users,
            "total_users": total_users,
            "blocked_users": blocked_users,
            "active_users": total_users - blocked_users,
            "role_counts": role_counts_prepared,
        })
        return context
