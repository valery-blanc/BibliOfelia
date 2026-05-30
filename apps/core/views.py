"""Vues transverses : dashboard, recherche globale, aide, préférences UI."""
from __future__ import annotations

from datetime import date, timedelta
from urllib.parse import urlencode

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.catalog.models import BibliographicRecord, Item
from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus
from apps.members.models import Member

from .search import classify_query


@login_required
def dashboard(request):
    """SPEC §6.6 : KPI principaux + tendance 30j + top 10 + état système."""
    from apps.reports import services as reports

    today = date.today()
    periods = reports.month_year_periods(today)
    active_loans = Loan.objects.filter(
        status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE]
    ).count()
    overdue = Loan.objects.filter(
        status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE], due_date__lt=today
    ).count()
    reservations_ready = Reservation.objects.filter(
        status=ReservationStatus.READY_FOR_PICKUP
    ).count()

    trend = reports.loans_trend(days=30)
    trend_max = max((row["count"] for row in trend), default=0)

    top_month = reports.top_loaned_records(periods["month_start"], today, limit=10)
    top_year = reports.top_loaned_records(periods["year_start"], today, limit=10)
    members_month = reports.active_members(periods["month_start"], today)
    members_year = reports.active_members(periods["year_start"], today)
    growth_month = reports.collection_growth(periods["month_start"], today)
    growth_year = reports.collection_growth(periods["year_start"], today)

    reminders = list(
        Loan.objects.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE],
            due_date__lt=today,
        )
        .select_related("item__record", "member")
        .order_by("due_date")[:10]
    )
    for loan in reminders:
        loan.days_overdue_count = (today - loan.due_date).days
    overdue_total = overdue

    # FEAT-036 : réservations prêtes pour lesquelles le membre n'a pas encore
    # été contacté (téléphone). Affichées dans un cadre dédié sur le dashboard.
    notifications_pending = list(
        Reservation.objects.filter(
            status=ReservationStatus.READY_FOR_PICKUP,
            notified_at__isnull=True,
        )
        .select_related("record", "member", "fulfilled_by_item")
        .order_by("ready_since", "created_at")
    )

    return render(request, "core/dashboard.html", {
        "kpi_active_loans": active_loans,
        "kpi_overdue": overdue,
        "kpi_reservations_ready": reservations_ready,
        "kpi_records": BibliographicRecord.objects.count(),
        "kpi_items": Item.objects.count(),
        "kpi_members": Member.objects.count(),
        "trend": trend,
        "trend_max": trend_max,
        "top_month": top_month,
        "top_year": top_year,
        "members_month": members_month,
        "members_year": members_year,
        "growth_month": growth_month,
        "growth_year": growth_year,
        "system_status": reports.system_status(),
        "reminders": reminders,
        "reminders_total": overdue_total,
        "notifications_pending": notifications_pending,
        "today": today,
    })


@login_required
def global_search(request):
    """Aiguille la barre de recherche unique. SPEC §6.1.

    Codes (EAN13 290/291, ISBN) → fiche directe ; texte → liste catalogue FTS.
    """
    raw = (request.GET.get("q") or "").strip()
    if not raw:
        return redirect("core:dashboard")
    kind, value = classify_query(raw)
    if kind == "item":
        item = Item.objects.filter(ean13=value).select_related("record").first()
        if item:
            return redirect("catalog:record_detail", pk=item.record_id)
    elif kind == "member":
        member = Member.objects.filter(card_number=value).first()
        if member:
            return redirect("members:detail", pk=member.pk)
    elif kind == "isbn":
        record = (
            BibliographicRecord.objects.filter(Q(isbn_13=value) | Q(isbn_10=value))
            .first()
        )
        if record:
            return redirect("catalog:record_detail", pk=record.pk)
    # texte libre, ou code non trouvé → liste catalogue (FTS + filtres)
    return redirect(f"{reverse('catalog:record_list')}?{urlencode({'q': raw})}")


@login_required
def help_page(request):
    """Sprint 15 : l'aide est désormais le site MkDocs servi à `<SCRIPT_NAME>/docs/`.
    On redirige les anciens liens et le bouton "?" vers ce site externe."""
    from django.http import HttpResponseRedirect
    from django.conf import settings as dj_settings

    script_name = dj_settings.FORCE_SCRIPT_NAME or ""
    return HttpResponseRedirect(script_name.rstrip("/") + "/docs/")


@login_required
def advanced_index(request):
    """Index « Avancé » : tous les outils Sprint 4 (rapports, impression,
    paramètres, comptes, diagnostic) groupés avec une phrase d'explication
    par lien. Visible des librarians+ ; sections superadmin masquées sinon.
    """
    return render(request, "core/advanced.html", {})


@require_POST
@login_required
def toggle_advanced(request):
    """Bascule le mode simple/avancé de l'utilisateur. SPEC §10.3."""
    user = request.user
    user.always_show_advanced = not user.always_show_advanced
    user.save(update_fields=["always_show_advanced"])
    next_url = request.POST.get("next") or reverse("core:dashboard")
    return redirect(next_url)
