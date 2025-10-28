from django.urls import path

from .views import (
    AdminDashboardView,
    DashboardRedirectView,
    ModeratorDashboardView,
    StudentDashboardView,
    TeacherDashboardView,
)

app_name = "dashboards"

urlpatterns = [
    path("", DashboardRedirectView.as_view(), name="home"),
    path("student/", StudentDashboardView.as_view(), name="student"),
    path("teacher/", TeacherDashboardView.as_view(), name="teacher"),
    path("moderator/", ModeratorDashboardView.as_view(), name="moderator"),
    path("admin/", AdminDashboardView.as_view(), name="admin"),
]
