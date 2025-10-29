import os
import random
import string
from pathlib import Path
from mongoengine import connect
from dotenv import load_dotenv

from .template import THEME_LAYOUT_DIR, THEME_VARIABLES

# ------------------------------------------------------------------------------
# Load environment variables
# ------------------------------------------------------------------------------
load_dotenv()  # take environment variables from .env

# ------------------------------------------------------------------------------
# Base directory setup
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------------------------------------------------------
# Security & Debug Settings
# ------------------------------------------------------------------------------
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "".join(random.choice(string.ascii_lowercase) for i in range(32))

DEBUG = os.environ.get("DEBUG", "True").lower() in ["true", "yes", "1"]

ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]
ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", default="local")

# ------------------------------------------------------------------------------
# Applications
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "accounts",
    "resources",
    "feed",
    "quiz",
    "moderation",
    "searchx",
    "community",
    "widget_tweaks",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Custom apps
    "apps.dashboards",
    "apps.layouts",
    "apps.pages",
    "apps.authentication",
    "apps.cards",
    "apps.ui",
    "apps.extended_ui",
    "apps.icons",
    "apps.forms",
    "apps.form_layouts",
    "apps.tables",
    "rest_framework",
]

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "accounts.middleware.ForceMongoBackendMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ------------------------------------------------------------------------------
# URL / Template / WSGI Config
# ------------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "config.context_processors.my_setting",
                "config.context_processors.environment",
            ],
            "libraries": {
                "theme": "web_project.template_tags.theme",
            },
            "builtins": [
                "django.templatetags.static",
                "web_project.template_tags.theme",
            ],
        },
    },
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "index"
WSGI_APPLICATION = "config.wsgi.application"

# ------------------------------------------------------------------------------
# Database (SQLite + MongoDB connection)
# ------------------------------------------------------------------------------
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

connect(
    db=os.getenv("MONGO_DB", "edusocial"),
    host=os.getenv("MONGO_URI", "mongodb://localhost:27017/edusocial"),
    alias="default",
)

AUTHENTICATION_BACKENDS = ["accounts.backends.MongoUserBackend"]
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"  # avoid hitting SQL database

# ------------------------------------------------------------------------------
# Password Validation
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "en"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# Static & Media Files
# ------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [BASE_DIR / "src" / "assets"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------------------
# Base URL
# ------------------------------------------------------------------------------
BASE_URL = os.environ.get("BASE_URL", default="http://127.0.0.1:8000")

# ------------------------------------------------------------------------------
# Email Settings
# ------------------------------------------------------------------------------
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "True").lower() in {"true", "1", "yes"}
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", EMAIL_HOST_USER or "no-reply@example.com"
)
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "30"))

# ------------------------------------------------------------------------------
# Default Auto Field
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# Theme Settings
# ------------------------------------------------------------------------------
THEME_LAYOUT_DIR = THEME_LAYOUT_DIR
THEME_VARIABLES = THEME_VARIABLES

# ------------------------------------------------------------------------------
# Your Stuff
# ------------------------------------------------------------------------------
# Add any custom settings or constants here if needed
