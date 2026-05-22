"""Agrégations pour le dashboard et les rapports. SPEC §6.6.

Toutes les fonctions retournent des structures Python simples (dict/list)
consommables aussi bien par les vues HTML que par l'export CSV / PDF.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.db.models import Count, Q
from django.utils.translation import gettext_lazy as _


@dataclass
class SystemStatus:
    version: str
    disk_free_gb: float | None
    disk_total_gb: float | None
    last_backup_at: datetime | None
    last_backup_age_hours: float | None
    last_backup_status: str
    backup_alert: bool = False
    online: bool | None = None
    zerotier_status: str = ""


def system_status() -> SystemStatus:
    """État système : version, disque, dernière sauvegarde (Task #14)."""
    from apps.core.models import Setting

    version = getattr(settings, "BIBLIOFELIA_VERSION", "?")
    disk_free_gb = None
    disk_total_gb = None
    try:
        path = Path(settings.DATABASE_PATH).parent
        usage = shutil.disk_usage(str(path))
        disk_free_gb = round(usage.free / (1024 ** 3), 2)
        disk_total_gb = round(usage.total / (1024 ** 3), 2)
    except Exception:
        pass

    last_backup_at = None
    last_backup_age_hours = None
    last_backup_status = "unknown"
    backup_alert = False
    last = Setting.get("last_backup", {}) or {}
    if isinstance(last, dict):
        iso = last.get("at")
        last_backup_status = last.get("status", "unknown")
        if iso:
            try:
                last_backup_at = datetime.fromisoformat(iso)
                delta = datetime.now(last_backup_at.tzinfo) - last_backup_at
                last_backup_age_hours = round(delta.total_seconds() / 3600, 1)
                if last_backup_age_hours > 24:
                    backup_alert = True
            except ValueError:
                pass
        else:
            backup_alert = True

    zerotier = Setting.get("zerotier", {}) or {}
    zerotier_status = zerotier.get("status", "") if isinstance(zerotier, dict) else ""

    return SystemStatus(
        version=version,
        disk_free_gb=disk_free_gb,
        disk_total_gb=disk_total_gb,
        last_backup_at=last_backup_at,
        last_backup_age_hours=last_backup_age_hours,
        last_backup_status=last_backup_status,
        backup_alert=backup_alert,
        zerotier_status=zerotier_status,
    )


def loans_trend(days: int = 30) -> list[dict]:
    """Liste `[{day, count}]` des prêts créés par jour sur les `days` derniers."""
    from apps.loans.models import Loan

    today = date.today()
    start = today - timedelta(days=days - 1)
    qs = (
        Loan.objects.filter(loan_date__date__gte=start)
        .extra(select={"day": "DATE(loan_date)"})
        .values("day")
        .annotate(count=Count("id"))
    )
    by_day = {row["day"]: row["count"] for row in qs}
    out = []
    for i in range(days):
        d = start + timedelta(days=i)
        key = d.isoformat()
        out.append({"day": d, "count": by_day.get(key, 0) or by_day.get(d, 0)})
    return out


def top_loaned_records(period_start: date, period_end: date, limit: int = 10) -> list[dict]:
    """Top notices prêtées sur la période. `[{record, title, count}]`."""
    from apps.catalog.models import BibliographicRecord
    from apps.loans.models import Loan

    qs = (
        Loan.objects.filter(loan_date__date__gte=period_start, loan_date__date__lte=period_end)
        .values("item__record_id", "item__record__title")
        .annotate(count=Count("id"))
        .order_by("-count")[:limit]
    )
    return [
        {
            "record_id": row["item__record_id"],
            "title": row["item__record__title"],
            "count": row["count"],
        }
        for row in qs
    ]


def active_members(period_start: date, period_end: date) -> int:
    from apps.loans.models import Loan

    return (
        Loan.objects.filter(
            loan_date__date__gte=period_start, loan_date__date__lte=period_end
        )
        .values("member_id")
        .distinct()
        .count()
    )


def collection_growth(period_start: date, period_end: date) -> dict:
    from apps.catalog.models import BibliographicRecord, Item

    return {
        "records_added": BibliographicRecord.objects.filter(
            created_at__date__gte=period_start, created_at__date__lte=period_end
        ).count(),
        "items_added": Item.objects.filter(
            created_at__date__gte=period_start, created_at__date__lte=period_end
        ).count(),
    }


def month_year_periods(today: date | None = None) -> dict:
    """Renvoie (debut_mois, debut_annee, fin) pour les rapports `mois`/`année`."""
    today = today or date.today()
    return {
        "today": today,
        "month_start": today.replace(day=1),
        "year_start": today.replace(month=1, day=1),
    }


# ----------------------------------------------------------------------
# Listes pour rapports
# ----------------------------------------------------------------------
def overdue_loans(threshold_days: int = 7):
    """Prêts en retard depuis plus de `threshold_days` jours."""
    from apps.loans.models import Loan, LoanStatus

    cutoff = date.today() - timedelta(days=threshold_days)
    return (
        Loan.objects.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE], due_date__lt=cutoff
        )
        .select_related("item__record", "member")
        .order_by("due_date")
    )


def reservations_ready_for_pickup():
    """Réservations satisfaites en attente de retrait (§6.8)."""
    from apps.loans.models import Reservation, ReservationStatus

    return (
        Reservation.objects.filter(status=ReservationStatus.READY_FOR_PICKUP)
        .select_related("record", "member", "fulfilled_by_item")
        .order_by("ready_since")
    )


def inactive_members(days: int = 365):
    """Usagers sans prêt depuis `days` jours."""
    from apps.members.models import Member

    cutoff = date.today() - timedelta(days=days)
    return (
        Member.objects.annotate(
            recent=Count(
                "loans",
                filter=Q(loans__loan_date__date__gte=cutoff),
            )
        )
        .filter(recent=0)
        .order_by("last_name", "first_name")
    )


def inactive_items(days: int = 365):
    """Exemplaires sans prêt depuis `days` jours."""
    from apps.catalog.models import Item

    cutoff = date.today() - timedelta(days=days)
    return (
        Item.objects.annotate(
            recent=Count(
                "loans",
                filter=Q(loans__loan_date__date__gte=cutoff),
            )
        )
        .filter(recent=0)
        .select_related("record")
        .order_by("internal_id")
    )


def loans_period(period_start: date, period_end: date):
    """Prêts créés sur la période — utilisé pour l'export CSV."""
    from apps.loans.models import Loan

    return (
        Loan.objects.filter(
            loan_date__date__gte=period_start, loan_date__date__lte=period_end
        )
        .select_related("item__record", "member")
        .order_by("loan_date")
    )


@dataclass
class AnnualReport:
    year: int
    period_start: date
    period_end: date
    loans_total: int = 0
    loans_returned: int = 0
    loans_overdue: int = 0
    loans_lost: int = 0
    members_active: int = 0
    members_total: int = 0
    records_added: int = 0
    items_added: int = 0
    top: list = field(default_factory=list)


def annual_report(year: int) -> AnnualReport:
    from apps.loans.models import Loan, LoanStatus
    from apps.members.models import Member

    period_start = date(year, 1, 1)
    period_end = date(year, 12, 31)
    base = Loan.objects.filter(
        loan_date__date__gte=period_start, loan_date__date__lte=period_end
    )
    growth = collection_growth(period_start, period_end)
    return AnnualReport(
        year=year,
        period_start=period_start,
        period_end=period_end,
        loans_total=base.count(),
        loans_returned=base.filter(status=LoanStatus.RETURNED).count(),
        loans_overdue=base.filter(status=LoanStatus.OVERDUE).count(),
        loans_lost=base.filter(status=LoanStatus.LOST).count(),
        members_active=active_members(period_start, period_end),
        members_total=Member.objects.count(),
        records_added=growth["records_added"],
        items_added=growth["items_added"],
        top=top_loaned_records(period_start, period_end, limit=10),
    )
