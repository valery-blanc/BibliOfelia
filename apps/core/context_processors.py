"""Context processors disponibles dans tous les templates."""
from __future__ import annotations

from datetime import date

from django.conf import settings


def global_settings(request):
    return {
        "library_name": _safe_setting("library_name", "BibliOfelia"),
        "app_version": "0.1.0-dev",
        "enabled_languages": settings.LANGUAGES,
    }


def notifications(request):
    """Compteurs de la barre de nav : retards + réservations prêtes (SPEC §6.8)."""
    if not getattr(request.user, "is_authenticated", False):
        return {"nav_counts": {}}
    try:
        from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus

        overdue = Loan.objects.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
            due_date__lt=date.today(),
        ).count()
        ready = Reservation.objects.filter(
            status=ReservationStatus.READY_FOR_PICKUP
        ).count()
    except Exception:
        return {"nav_counts": {}}
    return {"nav_counts": {"overdue": overdue, "reservations_ready": ready}}


def _safe_setting(key: str, default):
    try:
        from apps.core.models import Setting

        return Setting.get(key, default)
    except Exception:
        return default
