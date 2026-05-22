"""Middleware qui redirige vers /setup/ tant que le wizard n'est pas terminé.

Activé via `apps.setup.middleware.SetupRequiredMiddleware` dans MIDDLEWARE.
Idempotent : si Setting.get('setup_completed') == True, ne fait rien.
"""
from __future__ import annotations

from django.http import HttpResponseRedirect
from django.urls import resolve, reverse

ALLOWED_NAMESPACES = {"setup", "admin", "accounts"}
ALLOWED_PATHS = {"/static/", "/media/"}


class SetupRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._needs_setup(request):
            return HttpResponseRedirect(reverse("setup:wizard"))
        return self.get_response(request)

    def _needs_setup(self, request) -> bool:
        # On évite l'import au top-level pour ne pas casser les migrations
        try:
            from apps.core.models import Setting
        except Exception:
            return False

        path = request.path_info
        if any(path.startswith(p) for p in ALLOWED_PATHS):
            return False
        try:
            match = resolve(path)
            if match.namespace in ALLOWED_NAMESPACES or match.app_name in ALLOWED_NAMESPACES:
                return False
        except Exception:
            return False

        try:
            return not Setting.get("setup_completed", False)
        except Exception:
            # BD pas encore migrée
            return False
