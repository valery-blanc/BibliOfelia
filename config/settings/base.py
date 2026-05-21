"""Settings communs à tous les environnements.

Lit la conf via django-environ. Les valeurs spécifiques (DEBUG, hosts, base)
sont surchargées dans dev.py / prod.py / test.py.
"""
from __future__ import annotations

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SESSION_COOKIE_AGE=(int, 8 * 60 * 60),
    ENABLED_LANGUAGES=(list, ["fr", "en", "es", "mg"]),
    DEFAULT_LANGUAGE=(str, "fr"),
    DATABASE_PATH=(str, str(BASE_DIR / "data" / "bibliofelia.sqlite3")),
    FORCE_SCRIPT_NAME=(str, ""),
    STATIC_URL=(str, "/static/"),
    MEDIA_URL=(str, "/media/"),
    OPENLIBRARY_BASE_URL=(str, "https://openlibrary.org"),
    OPENLIBRARY_TIMEOUT=(int, 5),
    BACKUP_USB_PATH=(str, "/backup"),
    CUPS_HOST=(str, ""),
    CUPS_PORT=(int, 631),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "modeltranslation",  # doit précéder admin
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # tiers
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_q",
    "axes",
    "auditlog",
    "django_htmx",
    "widget_tweaks",
    # apps maison
    "apps.core",
    "apps.accounts",
    "apps.catalog",
    "apps.members",
    "apps.loans",
    "apps.inventory",
    "apps.printing",
    "apps.reports",
    "apps.setup",
    "apps.api",
    "apps.tasks",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "auditlog.middleware.AuditlogMiddleware",
    "axes.middleware.AxesMiddleware",
    "apps.setup.middleware.SetupRequiredMiddleware",
]

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
                "django.template.context_processors.i18n",
                "apps.core.context_processors.global_settings",
                "apps.core.context_processors.notifications",
            ],
            "builtins": [
                "django.templatetags.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASE_PATH = env("DATABASE_PATH")
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATABASE_PATH,
        "OPTIONS": {
            "init_command": (
                "PRAGMA journal_mode=WAL;"
                "PRAGMA synchronous=NORMAL;"
                "PRAGMA temp_store=MEMORY;"
                "PRAGMA mmap_size=134217728;"  # 128 MiB
                "PRAGMA foreign_keys=ON;"
                "PRAGMA busy_timeout=5000;"
            ),
            "transaction_mode": "IMMEDIATE",
        },
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Auth
AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = [
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
     "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
]

# Sessions et cookies
SESSION_COOKIE_AGE = env("SESSION_COOKIE_AGE")
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"

# Internationalisation
LANGUAGE_CODE = env("DEFAULT_LANGUAGE")
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

_ENABLED = env("ENABLED_LANGUAGES")
LANGUAGES = [
    (code, name)
    for code, name in [
        ("fr", "Français"),
        ("en", "English"),
        ("es", "Español"),
        ("mg", "Malagasy"),
    ]
    if code in _ENABLED
]
LOCALE_PATHS = [BASE_DIR / "locale"]

MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE
MODELTRANSLATION_LANGUAGES = tuple(code for code, _ in LANGUAGES)
MODELTRANSLATION_FALLBACK_LANGUAGES = (LANGUAGE_CODE,)

# Fichiers statiques et média
FORCE_SCRIPT_NAME = env("FORCE_SCRIPT_NAME") or None
STATIC_URL = env("STATIC_URL")
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = env("MEDIA_URL")
MEDIA_ROOT = BASE_DIR / "media"

# REST framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "scan": "60/min",
        "isbn": "30/min",
        "default": "60/min",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.CursorPagination",
    "PAGE_SIZE": 50,
    "EXCEPTION_HANDLER": "apps.api.exceptions.api_exception_handler",
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=4),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=90),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
}

# django-q2
Q_CLUSTER = {
    "name": "bibliofelia",
    "workers": 2,
    "recycle": 500,
    "timeout": 90,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 500,
    "cpu_affinity": 1,
    "label": "Django Q",
    "orm": "default",
    "scheduler": True,
    "catch_up": False,
}

# django-axes
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1  # heure
AXES_LOCKOUT_PARAMETERS = [["username", "ip_address"]]
AXES_RESET_ON_SUCCESS = True

# django-auditlog
AUDITLOG_INCLUDE_ALL_MODELS = False
AUDITLOG_EXCLUDE_TRACKING_MODELS = (
    "sessions.session",
    "admin.logentry",
    "auditlog.logentry",
    "axes.accessattempt",
    "axes.accesslog",
    "axes.accessfailurelog",
    "django_q.schedule",
    "django_q.task",
    "django_q.success",
    "django_q.failure",
    "django_q.ormq",
)

# OpenLibrary
OPENLIBRARY_BASE_URL = env("OPENLIBRARY_BASE_URL")
OPENLIBRARY_TIMEOUT = env("OPENLIBRARY_TIMEOUT")

# Sauvegardes
BACKUP_USB_PATH = env("BACKUP_USB_PATH")

# Impression
CUPS_HOST = env("CUPS_HOST")
CUPS_PORT = env("CUPS_PORT")

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{asctime} {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.security.csrf": {"level": "WARNING"},
        "axes": {"level": "WARNING"},
    },
}
