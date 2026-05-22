"""Notifications offline (§6.8) : alertes attachées à un usager.

Centralisé ici pour être réutilisable depuis le workflow de prêt, la fiche
membre, et les listes imprimables.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.utils.translation import gettext as _


@dataclass
class MemberAlert:
    level: str  # "info" | "warning" | "danger"
    message: str


def member_alerts(member) -> list[MemberAlert]:
    """Retourne les alertes pertinentes pour `member` (retards, réservations,
    expiration). Liste vide = RAS.
    """
    from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus
    from apps.members.services import days_until_expiration

    alerts: list[MemberAlert] = []
    today = date.today()
    overdue = (
        Loan.objects.filter(
            member=member,
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
            due_date__lt=today,
        ).count()
    )
    if overdue:
        alerts.append(MemberAlert(
            level="error",
            message=_("%(n)s prêt(s) en retard.") % {"n": overdue},
        ))
    ready = Reservation.objects.filter(
        member=member, status=ReservationStatus.READY_FOR_PICKUP
    ).count()
    if ready:
        alerts.append(MemberAlert(
            level="info",
            message=_("%(n)s réservation(s) à retirer.") % {"n": ready},
        ))
    days_left = days_until_expiration(member)
    if days_left is not None:
        if days_left < 0:
            alerts.append(MemberAlert(
                level="error",
                message=_("Carte expirée depuis %(n)s jours.") % {"n": -days_left},
            ))
        elif days_left <= 30:
            alerts.append(MemberAlert(
                level="warning",
                message=_("Carte expirante dans %(n)s jours.") % {"n": days_left},
            ))
    return alerts


def navbar_counts() -> dict:
    """Compteurs permanents affichés dans la barre de nav (§6.8)."""
    from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus

    today = date.today()
    return {
        "overdue": Loan.objects.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
            due_date__lt=today,
        ).count(),
        "reservations_ready": Reservation.objects.filter(
            status=ReservationStatus.READY_FOR_PICKUP
        ).count(),
    }
