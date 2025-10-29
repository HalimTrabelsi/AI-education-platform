"""
URL configuration for web_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
"""

from django.contrib import admin
from django.urls import path, include
from web_project.views import SystemView

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),

    # Accounts
    path("accounts/", include("accounts.urls")),

    # Dashboard
    path("", include("apps.dashboards.urls")),

    # Layouts
    path("", include("apps.layouts.urls")),

    # Pages
    path("", include("apps.pages.urls")),

    # Authentication
    path("", include("apps.authentication.urls")),

    # Cards
    path("", include("apps.cards.urls")),

    # UI
    path("", include("apps.ui.urls")),

    # Extended UI
    path("", include("apps.extended_ui.urls")),

    # Icons
    path("", include("apps.icons.urls")),

    # Forms
    path("", include("apps.forms.urls")),

    # Form Layouts
    path("", include("apps.form_layouts.urls")),

    # Tables
    path("", include("apps.tables.urls")),

    # Moderation (Reports CRUD)
    path("moderation/", include("moderation.urls", namespace="moderation")),
]

# Custom error handlers
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
