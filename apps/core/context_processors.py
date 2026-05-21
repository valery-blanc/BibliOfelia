"""Context processors disponibles dans tous les templates."""
from __future__ import annotations

from django.conf import settings


def global_settings(request):
    return {
        "library_name": _safe_setting("library_name", "BibliOfelia"),
        "app_version": "0.1.0-dev",
        "enabled_languages": settings.LANGUAGES,
    }


def notifications(request):
    """Compteurs pour la barre de nav (retards, réservations prêtes). À étoffer."""
    if not request.user.is_authenticated:
        return {"nav_counts": {}}
    return {"nav_counts": {"overdue": 0, "reservations_ready": 0}}


def _safe_setting(key: str, default):
    try:
        from apps.core.models import Setting

        return Setting.get(key, default)
    except Exception:
        return default
