"""Settings de production (Ofelia Box / keebee)."""
import os

from .base import *  # noqa: F401, F403
from .base import env

DEBUG = False

# SECRET_KEY obligatoire via env ou fichier secret monté
if "SECRET_KEY_FILE" in os.environ:
    with open(os.environ["SECRET_KEY_FILE"], encoding="utf-8") as fh:
        SECRET_KEY = fh.read().strip()
else:
    SECRET_KEY = env("SECRET_KEY")

ALLOWED_HOSTS = env("ALLOWED_HOSTS", default=["*"])
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS", default=[])

# Sécurité HTTPS (nginx termine TLS, on est derrière proxy)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# SECURE_COOKIES : cookies marqués Secure + HSTS. Vaut True par défaut, mais la
# Ofelia Box sert l'UI en HTTP sur son point d'accès WiFi (443 bloqué sur wlan0
# par keebee) ; le mettre à False y permet la connexion HTTP comme HTTPS
# (FEAT-020). Reste à True pour tout déploiement 100 % HTTPS.
SECURE_COOKIES = env("SECURE_COOKIES")
SESSION_COOKIE_SECURE = SECURE_COOKIES
CSRF_COOKIE_SECURE = SECURE_COOKIES
SECURE_HSTS_SECONDS = 31536000 if SECURE_COOKIES else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_COOKIES
SECURE_HSTS_PRELOAD = False  # cert auto-signé local, pas de preload
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"

# Static files servis par nginx → manifest pour cache-busting
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage",
    },
}
