"""Settings pour pytest — base SQLite en mémoire, pas de tâches async."""
from .base import *  # noqa: F401, F403

DEBUG = False
SECRET_KEY = "test-secret-key"
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {"init_command": "PRAGMA foreign_keys=ON;"},
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

Q_CLUSTER = {"name": "test", "sync": True, "orm": "default"}

AXES_ENABLED = False
AUDITLOG_INCLUDE_ALL_MODELS = False
