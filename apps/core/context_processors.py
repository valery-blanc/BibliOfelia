"""Context processors disponibles dans tous les templates."""
from __future__ import annotations

from datetime import date

from django.conf import settings


def global_settings(request):
    script_name = settings.FORCE_SCRIPT_NAME or ""
    return {
        "library_name": _safe_setting("library_name", "BibliOfelia"),
        # Une seule source de vérité pour la version : le pied de page la codait
        # en dur, l'API et /pairing/info lisaient le réglage. Les deux pouvaient
        # donc annoncer des versions différentes du même logiciel.
        "app_version": settings.BIBLIOFELIA_VERSION,
        "enabled_languages": settings.LANGUAGES,
        # Guide utilisateur statique (Sprint 15) servi par nginx à `<SCRIPT_NAME>/docs/`.
        # En dev (FORCE_SCRIPT_NAME=""), lancer `mkdocs serve` séparément.
        "docs_url": script_name.rstrip("/") + "/docs/",
    }


def notifications(request):
    """Compteurs de la barre de nav (§6.8)."""
    if not getattr(request.user, "is_authenticated", False):
        return {"nav_counts": {}}
    try:
        from apps.members.notifications import navbar_counts

        return {"nav_counts": navbar_counts()}
    except Exception:
        return {"nav_counts": {}}


def _safe_setting(key: str, default):
    try:
        from apps.core.models import Setting

        return Setting.get(key, default)
    except Exception:
        return default
