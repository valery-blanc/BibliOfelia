"""Statistiques d'activité et pilotage du bouclement. FEAT-085 / FEAT-086."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone

from .models import (
    ActivityEntry,
    AnimationAttendance,
    AnimationSession,
    DayClosing,
)

logger = logging.getLogger(__name__)


@dataclass
class AnimationStats:
    """La phrase que Val veut pouvoir écrire en fin d'année."""

    sessions: int = 0
    member_attendance: int = 0
    non_member_adults: int = 0
    non_member_children: int = 0
    minutes: int = 0

    @property
    def non_members(self) -> int:
        return self.non_member_adults + self.non_member_children

    @property
    def total_attendance(self) -> int:
        return self.member_attendance + self.non_members

    @property
    def hours(self) -> float:
        return round(self.minutes / 60, 1)


def animation_stats(start: date, end: date) -> AnimationStats:
    qs = AnimationSession.objects.filter(occurred_on__gte=start, occurred_on__lte=end)
    totals = qs.aggregate(
        sessions=Count("id"),
        minutes=Sum("minutes"),
        adults=Sum("non_member_adults"),
        children=Sum("non_member_children"),
    )
    # Compté sur la table des présences, jamais dans le même `aggregate` que
    # les sommes ci-dessus : la jointure dupliquerait chaque session autant de
    # fois qu'elle a de présents, et `Sum("non_member_adults")` serait multiplié
    # d'autant.
    members = AnimationAttendance.objects.filter(
        session__occurred_on__gte=start, session__occurred_on__lte=end
    ).count()
    return AnimationStats(
        sessions=totals["sessions"] or 0,
        member_attendance=members,
        non_member_adults=totals["adults"] or 0,
        non_member_children=totals["children"] or 0,
        minutes=totals["minutes"] or 0,
    )


def activity_stats(start: date, end: date) -> list[dict]:
    """Temps passé par nature d'activité, la plus lourde d'abord."""
    rows = (
        ActivityEntry.objects.filter(occurred_on__gte=start, occurred_on__lte=end)
        .values("activity_type__label")
        .annotate(minutes=Sum("minutes"), entries=Count("id"))
        .order_by("-minutes")
    )
    return [
        {
            "label": row["activity_type__label"],
            "minutes": row["minutes"] or 0,
            "hours": round((row["minutes"] or 0) / 60, 1),
            "entries": row["entries"],
        }
        for row in rows
    ]


@dataclass
class MonthRow:
    month: int
    sessions: int = 0
    member_attendance: int = 0
    non_members: int = 0
    activity_minutes: int = 0


def monthly_rows(year: int) -> list[MonthRow]:
    rows = {m: MonthRow(month=m) for m in range(1, 13)}
    sessions = (
        AnimationSession.objects.filter(occurred_on__year=year)
        .values("occurred_on__month")
        .annotate(
            n=Count("id"),
            adults=Sum("non_member_adults"),
            children=Sum("non_member_children"),
        )
    )
    for row in sessions:
        target = rows[row["occurred_on__month"]]
        target.sessions = row["n"]
        target.non_members = (row["adults"] or 0) + (row["children"] or 0)
    # Requête séparée : agréger les présences avec les sommes ci-dessus
    # multiplierait `non_member_adults` par le nombre de présents.
    attendances = (
        AnimationAttendance.objects.filter(session__occurred_on__year=year)
        .values("session__occurred_on__month")
        .annotate(n=Count("id"))
    )
    for row in attendances:
        rows[row["session__occurred_on__month"]].member_attendance = row["n"]
    activities = (
        ActivityEntry.objects.filter(occurred_on__year=year)
        .values("occurred_on__month")
        .annotate(minutes=Sum("minutes"))
    )
    for row in activities:
        rows[row["occurred_on__month"]].activity_minutes = row["minutes"] or 0
    return list(rows.values())


# ----------------------------------------------------------------------
# Bouclement
# ----------------------------------------------------------------------
def get_or_create_closing(user, day: date | None = None) -> DayClosing:
    day = day or date.today()
    closing, _created = DayClosing.objects.get_or_create(closing_date=day, user=user)
    return closing


def is_box() -> bool:
    """L'instance tourne-t-elle sur la Ofelia Box ?

    Sur `sanjuan` ou `grand-saconnex`, éteindre le serveur n'a aucun sens :
    l'étape disparaît (arbitrage Val, 2026-08-31).
    """
    from apps.core.models import Setting

    return bool(Setting.get("is_box", False))


@dataclass
class ShutdownResult:
    requested: bool = False
    flag_path: str = ""
    error: str = ""
    details: list = field(default_factory=list)


def request_shutdown() -> ShutdownResult:
    """Écrit le fichier-drapeau surveillé par l'unité systemd de la Box.

    Un conteneur ne peut pas éteindre son hôte : la moitié système de ce
    mécanisme (`ofelia-shutdown.path`) vit dans le dépôt keebee/ofeliabox. Tant
    qu'elle n'est pas déployée, le fichier est écrit et rien ne se passe — c'est
    ce que dit l'écran, plutôt que d'annoncer un arrêt qui n'arrivera pas.
    """
    from pathlib import Path

    path = Path(getattr(settings, "BOX_SHUTDOWN_FLAG", "/data/shutdown.request"))
    result = ShutdownResult(flag_path=str(path))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Écriture en binaire après encodage : `open(..., "w")` tronque le
        # fichier AVANT d'encoder, et un échec d'encodage laisserait un drapeau
        # vide que l'hôte pourrait quand même interpréter.
        payload = timezone.now().isoformat().encode("utf-8")
        with open(path, "wb") as handle:
            handle.write(payload)
        result.requested = True
    except OSError as exc:
        result.error = str(exc)
        logger.warning("Demande d'extinction impossible : %s", exc)
    return result
