"""Vues des rapports (§6.6).

- Index : liste des rapports disponibles
- Liste des retards (imprimable)
- Liste des inactifs (membres + livres)
- Export CSV prêts par période
- Rapport annuel PDF
"""
from __future__ import annotations

import csv
from datetime import date

from django.http import HttpResponse
from django.shortcuts import render

from apps.accounts.models import Role
from apps.accounts.permissions import require_role

from . import services
from .forms import PeriodForm, YearForm
from .pdf import render_annual_pdf


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
