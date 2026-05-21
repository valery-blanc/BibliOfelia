"""Settings de développement local."""
from .base import *  # noqa: F401, F403
from .base import INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True
SECRET_KEY = env("SECRET_KEY", default="dev-secret-key-not-for-production")
ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = ["127.0.0.1"]

# debug toolbar (chargé seulement si installé)
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
except ImportError:
    pass

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# CSRF / cookies relâchés en dev
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
