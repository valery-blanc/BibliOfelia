"""Middlewares applicatifs BibliOfelia.

`MethodNotAllowedPrettyMiddleware` (FEAT-043) : Django ne fournit pas de
`handler405` configurable — la réponse `HttpResponseNotAllowed` générée par
`require_POST` / `require_http_methods` est un body HTML minimaliste sans
chrome. Ce middleware substitue notre template `405.html` (logo + topbars
Ofelia + bouton retour) quand le statut final est 405.
"""
from __future__ import annotations

from django.http import HttpResponse
from django.template.loader import render_to_string


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
