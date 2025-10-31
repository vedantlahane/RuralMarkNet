"""Django settings for the RuralMarkNet project."""
from __future__ import annotations

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def getenv(name: str, default: str | None = None) -> str:
    """Fetch an environment variable or raise if missing."""
    if default is not None:
        return os.getenv(name, default)
    value = os.getenv(name)
    if value is None:
        raise ImproperlyConfigured(f"Environment variable {name!r} is required.")
    return value


SECRET_KEY = getenv("DJANGO_SECRET_KEY", "django-insecure-change-me")
DEBUG = getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS: list[str] = getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django_tailwind",
    "theme",
    "accounts",
    "products",
    "orders",
    "deliveries",
    "payments",
]

SITE_ID = 1

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ruralmarknet.urls"

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
                "products.context_processors.product_filters",
            ]
        },
    }
]

WSGI_APPLICATION = "ruralmarknet.wsgi.application"
ASGI_APPLICATION = "ruralmarknet.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": getenv("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": getenv("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": getenv("DJANGO_DB_USER", ""),
        "PASSWORD": getenv("DJANGO_DB_PASSWORD", ""),
        "HOST": getenv("DJANGO_DB_HOST", ""),
        "PORT": getenv("DJANGO_DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 9},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("hi", "Hindi"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

TAILWIND_APP_NAME = "theme"
INTERNAL_IPS = ["127.0.0.1"]

LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"
LOGIN_URL = "login"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {
    "default": {
        "BACKEND": getenv(
            "DJANGO_CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"
        ),
        "LOCATION": getenv("DJANGO_CACHE_LOCATION", "ruralmarknet-cache"),
    }
}

SESSION_ENGINE = getenv(
    "DJANGO_SESSION_ENGINE", "django.contrib.sessions.backends.cached_db"
)

CSRF_TRUSTED_ORIGINS = getenv(
    "DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost,http://127.0.0.1"
).split(",")

STRIPE_API_KEY = getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = getenv("STRIPE_WEBHOOK_SECRET", "")
PAYPAL_CLIENT_ID = getenv("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = getenv("PAYPAL_CLIENT_SECRET", "")

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
