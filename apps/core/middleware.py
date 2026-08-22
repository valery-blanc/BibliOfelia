"""Middlewares applicatifs BibliOfelia.

`MethodNotAllowedPrettyMiddleware` (FEAT-043) : Django ne fournit pas de
`handler405` configurable — la réponse `HttpResponseNotAllowed` générée par
`require_POST` / `require_http_methods` est un body HTML minimaliste sans
chrome. Ce middleware substitue notre template `405.html` (logo + topbars
Ofelia + bouton retour) quand le statut final est 405.
"""
from __future__ import annotations

import logging
import zoneinfo

from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class MethodNotAllowedPrettyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request) -> HttpResponse:
        response = self.get_response(request)
        if response.status_code != 405:
            return response
        # Garder les en-têtes (Allow notamment) sur la nouvelle réponse.
        allow = response.get("Allow", "")
        referer = request.META.get("HTTP_REFERER", "")
        # Filet : ne pas renvoyer vers la même URL POST-only.
        if referer and referer.endswith(request.get_full_path()):
            referer = ""
        html = render_to_string(
            "405.html",
            {
                "method": request.method,
                "allow": allow,
                "back_url": referer,
            },
            request=request,
        )
        new_response = HttpResponse(html, status=405)
        if allow:
            new_response["Allow"] = allow
        return new_response


class TimezoneMiddleware:
    """FEAT-077 — active le fuseau horaire réglé dans les Paramètres.

    Sans ça, tout l'applicatif vit dans `settings.TIME_ZONE` (`TZ` de la
    machine, UTC par défaut) : une bibliothèque hors UTC verrait sur l'accueil
    une heure décalée en permanence et croirait sa Box déréglée, alors que
    l'affichage de l'heure sert précisément à repérer une Box réellement
    déréglée.

    Réglage vide = on garde le fuseau du système, ce qui est le cas de la Box
    (elle prend celui du Raspberry Pi). Un fuseau invalide est ignoré plutôt
    que fatal : mieux vaut une heure en UTC qu'une application qui ne répond
    plus.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from django.utils import timezone

        name = self._configured()
        if name:
            try:
                timezone.activate(zoneinfo.ZoneInfo(name))
            except Exception:
                logger.warning("Fuseau horaire inconnu dans les Paramètres : %s", name)
                timezone.deactivate()
        else:
            timezone.deactivate()
        return self.get_response(request)

    @staticmethod
    def _configured() -> str:
        """Nom IANA réglé, ou "" (table absente avant la 1re migration)."""
        from apps.core.models import Setting

        try:
            return (Setting.get("timezone", "") or "").strip()
        except Exception:
            return ""
