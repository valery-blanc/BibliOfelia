"""Handler d'exceptions DRF — format normalisé `{error: {code, message, details}}`.

SPEC §6.10 (Codes d'erreur et résilience).
"""
from __future__ import annotations

from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return None

    code = getattr(exc, "default_code", "error")
    detail = response.data
    message = str(detail) if not isinstance(detail, dict) else detail.get("detail") or "Erreur"
    details = detail if isinstance(detail, (dict, list)) else None

    return Response(
        {"error": {"code": code, "message": message, "details": details}},
        status=response.status_code,
        headers={k: v for k, v in (response.headers or {}).items()},
    )
