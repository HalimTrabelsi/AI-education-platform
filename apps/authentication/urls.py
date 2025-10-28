from django.urls import path

from accounts.views import forgot_password_view
from .views import AuthView


urlpatterns = [
    path(
        "auth/login/",
        AuthView.as_view(template_name="auth_login_basic.html"),
        name="auth-login-basic",
    ),
    path(
        "auth/register/",
        AuthView.as_view(template_name="auth_register_basic.html"),
        name="auth-register-basic",
    ),
    path(
        "auth/forgot_password/",
        forgot_password_view,
        name="auth-forgot-password-basic",
    ),
]
