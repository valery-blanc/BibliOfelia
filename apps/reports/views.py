"""Vues des rapports. SPEC §6.6, FEAT-093.

Trois vues génériques — écran, PDF, Excel — qui résolvent un `slug` dans le
registre `builders.REPORTS`. C'est ce qui garantit qu'un écran a toujours ses
deux exports et qu'un export montre toujours ce que l'écran montre.

Les exports CSV de données brutes (FEAT-040) restent à côté : ce sont des
fichiers de reprise pour un tableur, pas des rapports.
"""
from __future__ import annotations

import csv
from datetime import date

from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.loans.models import ReservationStatus

from . import builders, periods, services
from .excel import render_report_xlsx
from .pdf import render_report_pdf

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)

# Paramètres à recopier dans les liens d'export : sans eux, le PDF ne
# reproduirait pas l'écran qu'on vient de regarder.
CARRIED_PARAMS = ("p", "start", "end", "threshold", "days", "category", "member_category")


def _csv_response(filename: str) -> HttpResponse:
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


def _carried_query(params) -> str:
    from urllib.parse import urlencode

    return urlencode({k: params[k] for k in CARRIED_PARAMS if params.get(k)})


def _build(slug: str, request):
    """Résout le rapport et le construit. Renvoie `(spec, page, avertissement)`."""
    spec = builders.get(slug)
    if spec is None:
        raise Http404(_("Ce rapport n'existe pas."))
    warning = ""
    period = None
    if spec.needs_period:
        period, warning = periods.parse(request.GET)
    page = spec.builder(period, request.GET)
    page.query = _carried_query(request.GET)
    return spec, page, warning


@require_role(*READ_ROLES)
def reports_index(request):
    """Le hub : d'abord ce qu'on fait, ensuite ce qu'on montre."""
    work = [
        {"spec": spec, "count": spec.counter() if spec.counter else None}
        for spec in builders.in_group(builders.GROUP_WORK)
    ]
    return render(request, "reports/index.html", {
        "work": work,
        "stats": builders.in_group(builders.GROUP_STATS),
    })


@require_role(*READ_ROLES)
def report_view(request, slug):
    spec, page, warning = _build(slug, request)
    # Les réglages propres à l'écran (catégorie, seuil) doivent survivre à un
    # changement de période : sinon choisir « 2025 » remet le filtre à zéro.
    filter_params = {
        key: request.GET[key]
        for key in CARRIED_PARAMS
        if key not in ("p", "start", "end") and request.GET.get(key)
    }
    from urllib.parse import urlencode

    return render(request, "reports/page.html", {
        "spec": spec,
        "page": page,
        "warning": warning,
        "shortcuts": periods.shortcuts() if spec.needs_period else [],
        "filter_params": filter_params,
        "filter_query": ("&" + urlencode(filter_params)) if filter_params else "",
    })


def _requested_block(page, request):
    """Le sous-rapport visé par `?block=`, ou None pour l'écran entier.

    Une clé inconnue (lien périmé, tableau renommé) renvoie l'écran complet
    plutôt qu'un 404 : l'utilisateur obtient plus que ce qu'il demandait, jamais
    une erreur.
    """
    key = (request.GET.get("block") or "").strip()
    return page.block(key) if key else None


@require_role(*READ_ROLES)
def report_pdf(request, slug):
    _spec, page, _warning = _build(slug, request)
    block = _requested_block(page, request)
    resp = HttpResponse(render_report_pdf(page, block), content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="{page.filename("pdf", block)}"'
    return resp


@require_role(*READ_ROLES)
def report_xlsx(request, slug):
    _spec, page, _warning = _build(slug, request)
    block = _requested_block(page, request)
    resp = HttpResponse(
        render_report_xlsx(page, block),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    resp["Content-Disposition"] = f'attachment; filename="{page.filename("xlsx", block)}"'
    return resp


# ─── Anciennes adresses : conservées pour ne pas casser les liens du guide ──


def overdue_list(request):
    return redirect("reports:view", slug="overdue")


def reservations_pickup_list(request):
    return redirect("reports:view", slug="pickup")


def inactive_list(request):
    return redirect("reports:view", slug="inactive")


def annual_pdf(request):
    """Le rapport annuel d'avant FEAT-093 : la vue d'ensemble sur l'année."""
    year = request.GET.get("year") or date.today().year
    return redirect(f"/reports/overview.pdf?p=custom&start={year}-01-01&end={year}-12-31")


# ─── Exports CSV de données brutes (FEAT-040), inchangés ───────────────────


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def loans_csv(request):
    period, _warning = periods.parse(request.GET)
    loans = services.loans_period(period.start, period.end)
    resp = _csv_response(
        f"loans_{period.start.isoformat()}_{period.end.isoformat()}.csv"
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
