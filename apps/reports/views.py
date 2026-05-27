"""Vues des rapports (§6.6).

- Index : liste des rapports disponibles
- Liste des retards (imprimable)
- Liste des inactifs (membres + livres)
- Export CSV prêts par période
- Export CSV catalogue complet, prêts/réservations en cours, inactifs (FEAT-040)
- Rapport annuel PDF
"""
from __future__ import annotations

import csv
from datetime import date

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.loans.models import ReservationStatus

from . import services
from .forms import PeriodForm, YearForm
from .pdf import render_annual_pdf


def _csv_response(filename: str) -> HttpResponse:
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
def reports_index(request):
    return render(
        request,
        "reports/index.html",
        {
            "period_form": PeriodForm(),
            "year_form": YearForm(),
        },
    )


@require_role(Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
def overdue_list(request):
    threshold = int(request.GET.get("threshold", 7))
    loans = services.overdue_loans(threshold_days=threshold)
    return render(
        request,
        "reports/overdue_list.html",
        {"loans": loans, "threshold": threshold, "today": date.today()},
    )


@require_role(Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
def reservations_pickup_list(request):
    reservations = services.reservations_ready_for_pickup()
    return render(
        request,
        "reports/reservations_pickup.html",
        {"reservations": reservations, "today": date.today()},
    )


@require_role(Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
def inactive_list(request):
    days = int(request.GET.get("days", 365))
    members = services.inactive_members(days=days)
    items = services.inactive_items(days=days)
    return render(
        request,
        "reports/inactive_list.html",
        {"members": members, "items": items, "days": days},
    )


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def loans_csv(request):
    form = PeriodForm(request.GET or None)
    if not form.is_valid():
        return render(request, "reports/period_error.html", {"form": form}, status=400)
    start = form.cleaned_data["start"]
    end = form.cleaned_data["end"]
    loans = services.loans_period(start, end)
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = (
        f'attachment; filename="loans_{start.isoformat()}_{end.isoformat()}.csv"'
    )
    writer = csv.writer(resp)
    writer.writerow([
        "loan_id", "loan_date", "due_date", "return_date", "status",
        "item_internal_id", "item_ean13", "record_title",
        "member_card", "member_name",
    ])
    for loan in loans.iterator():
        writer.writerow([
            loan.pk,
            loan.loan_date.isoformat() if loan.loan_date else "",
            loan.due_date.isoformat() if loan.due_date else "",
            loan.return_date.isoformat() if loan.return_date else "",
            loan.status,
            loan.item.internal_id,
            loan.item.ean13,
            loan.item.record.title,
            loan.member.card_number,
            f"{loan.member.last_name} {loan.member.first_name}".strip(),
        ])
    return resp


# ─── FEAT-040 : exports CSV ────────────────────────────────────────────────


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def catalog_csv(request):
    """Export CSV de tout le catalogue (1 ligne par exemplaire)."""
    today = date.today().isoformat()
    resp = _csv_response(f"catalog_{today}.csv")
    writer = csv.writer(resp)
    writer.writerow([
        "item_internal_id", "item_ean13", "item_state", "item_status",
        "item_location_code", "item_acquisition_date", "item_acquisition_source",
        "item_donor",
        "record_id", "record_title", "record_subtitle", "record_authors",
        "record_publisher", "record_publication_year", "record_language",
        "record_isbn_13", "record_isbn_10", "record_category", "record_tags",
        "record_document_type", "record_series_name", "record_series_volume",
        "record_summary",
    ])
    for item in services.catalog_full_csv_rows().iterator(chunk_size=500):
        rec = item.record
        authors = "; ".join(a.full_name for a in rec.authors.all())
        tags = "; ".join(t.name for t in rec.tags.all())
        writer.writerow([
            item.internal_id,
            item.ean13,
            item.state,
            item.status,
            item.location.code if item.location else "",
            item.acquisition_date.isoformat() if item.acquisition_date else "",
            item.acquisition_source,
            item.donor,
            rec.pk,
            rec.title,
            rec.subtitle,
            authors,
            rec.publisher,
            rec.publication_year or "",
            rec.language,
            rec.isbn_13 or "",
            rec.isbn_10 or "",
            rec.category.name if rec.category else "",
            tags,
            rec.document_type,
            rec.series_name,
            rec.series_volume,
            rec.summary,
        ])
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def active_loans_reservations_csv(request):
    """Export CSV des prêts en cours + réservations en cours (2 sections)."""
    today = date.today().isoformat()
    resp = _csv_response(f"active_loans_reservations_{today}.csv")
    writer = csv.writer(resp)
    writer.writerow([
        "kind", "id", "status", "created_at",
        "member_card", "member_name", "record_title", "item_internal_id",
        "due_or_expiry_date",
    ])
    for loan in services.active_loans_for_export().iterator():
        writer.writerow([
            "loan",
            loan.pk,
            loan.status,
            loan.loan_date.isoformat() if loan.loan_date else "",
            loan.member.card_number,
            f"{loan.member.last_name} {loan.member.first_name}".strip(),
            loan.item.record.title,
            loan.item.internal_id,
            loan.due_date.isoformat() if loan.due_date else "",
        ])
    for res in services.active_reservations_for_export().iterator():
        deadline = ""
        if res.status == ReservationStatus.READY_FOR_PICKUP:
            from apps.loans.services import pickup_expiration_for

            d = pickup_expiration_for(res)
            deadline = d.isoformat() if d else ""
        writer.writerow([
            "reservation",
            res.pk,
            res.status,
            res.created_at.isoformat() if res.created_at else "",
            res.member.card_number,
            f"{res.member.last_name} {res.member.first_name}".strip(),
            res.record.title,
            res.fulfilled_by_item.internal_id if res.fulfilled_by_item else "",
            deadline,
        ])
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def inactive_members_csv(request):
    days = int(request.GET.get("days", 365))
    members = services.inactive_members(days=days)
    today = date.today().isoformat()
    resp = _csv_response(f"inactive_members_{days}d_{today}.csv")
    writer = csv.writer(resp)
    writer.writerow([
        "card_number", "last_name", "first_name", "registration_date",
        "last_activity",
    ])
    for m in members:
        if m.last_activity:
            last = m.last_activity.date().isoformat()
        else:
            last = _("Aucune activité")
        writer.writerow([
            m.card_number,
            m.last_name,
            m.first_name,
            m.registration_date.isoformat() if m.registration_date else "",
            last,
        ])
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def inactive_items_csv(request):
    days = int(request.GET.get("days", 365))
    items = services.inactive_items(days=days)
    today = date.today().isoformat()
    resp = _csv_response(f"inactive_items_{days}d_{today}.csv")
    writer = csv.writer(resp)
    writer.writerow([
        "internal_id", "ean13", "record_title", "last_activity",
    ])
    for it in items:
        if it.last_activity:
            last = it.last_activity.date().isoformat()
        else:
            last = _("Aucune activité")
        writer.writerow([
            it.internal_id,
            it.ean13,
            it.record.title,
            last,
        ])
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def annual_pdf(request):
    from apps.core.models import Setting

    form = YearForm(request.GET or None)
    if not form.is_valid():
        return render(request, "reports/period_error.html", {"form": form}, status=400)
    year = form.cleaned_data["year"]
    report = services.annual_report(year)
    library_name = Setting.get("library_name", "BibliOfelia")
    pdf = render_annual_pdf(report, library_name=library_name)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="annual_{year}.pdf"'
    return resp
