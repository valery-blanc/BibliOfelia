"""Settings pour pytest — base SQLite en mémoire, pas de tâches async."""
from .base import *  # noqa: F401, F403
from .base import MIDDLEWARE as _BASE_MIDDLEWARE

DEBUG = False
SECRET_KEY = "test-secret-key"
ALLOWED_HOSTS = ["*"]

# Le wizard de premier démarrage (SetupRequiredMiddleware) redirige toute
# requête vers /setup/ tant que `setup_completed` est faux. Les tests unitaires
# de vues s'exécutent hors de ce parcours : on retire le middleware ici.
MIDDLEWARE = [m for m in _BASE_MIDDLEWARE if "SetupRequiredMiddleware" not in m]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "OPTIONS": {"init_command": "PRAGMA foreign_keys=ON;"},
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# sync=True : les tâches s'exécutent en synchrone. retry > timeout pour éviter
# le UserWarning de django-q au chargement (cf. BUG-001).
Q_CLUSTER = {"name": "test", "sync": True, "timeout": 30, "retry": 60, "orm": "default"}

AXES_ENABLED = False
AUDITLOG_INCLUDE_ALL_MODELS = False
