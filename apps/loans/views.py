"""Vues prêts / retours / consultations / réservations. SPEC §6.3 et §6.4."""
from __future__ import annotations

from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.catalog.models import BibliographicRecord, Item
from apps.core.search import normalize_code
from apps.members.models import Member
from apps.members.notifications import member_alerts

from .forms import ConsultationForm, ReservationForm
from .models import Loan, LoanStatus, Reservation, ReservationStatus
from .services import (
    cancel_reservation,
    check_item_loanable,
    create_loan,
    create_reservation,
    declare_lost,
    renew_loan,
    return_item,
)

WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)
_OPEN_LOAN_STATUSES = (LoanStatus.ACTIVE, LoanStatus.OVERDUE)


@require_role(*WRITE_ROLES)
def lend(request):
    if request.method == "POST":
        return _lend_post(request)

    member = None
    member_pk = request.session.get("lend_member")
    if member_pk:
        member = Member.objects.filter(pk=member_pk).select_related("category").first()
    basket_ids = request.session.get("lend_basket", [])
    basket = list(
        Item.objects.filter(pk__in=basket_ids).select_related("record")
    )
    context = {
        "member": member,
        "basket": basket,
        "alerts": [a.message for a in member_alerts(member)] if member else [],
        "active_loans": (
            member.loans.filter(status__in=_OPEN_LOAN_STATUSES).select_related(
                "item__record"
            )
            if member
            else []
        ),
    }
    return render(request, "loans/lend.html", context)


def _lend_post(request):
    action = request.POST.get("action")

    if action == "set_member":
        card = normalize_code(request.POST.get("card", ""))
        member = Member.objects.filter(card_number=card).first()
        if not member:
            member = Member.objects.filter(
                replaces_card_number=card
            ).first()
        if member:
            request.session["lend_member"] = member.pk
            request.session["lend_basket"] = []
        else:
            messages.error(request, _("Aucun usager pour cette carte."))
        return redirect("loans:lend")

    if action == "cancel":
        request.session.pop("lend_member", None)
        request.session.pop("lend_basket", None)
        return redirect("loans:lend")

    member_pk = request.session.get("lend_member")
    member = Member.objects.filter(pk=member_pk).select_related("category").first()
    if not member:
        messages.error(request, _("Scannez d'abord une carte d'usager."))
        return redirect("loans:lend")
    basket = request.session.get("lend_basket", [])

    if action == "add_item":
        ean = normalize_code(request.POST.get("ean", ""))
        item = Item.objects.filter(ean13=ean).select_related("record").first()
        if not item:
            messages.error(request, _("Exemplaire introuvable : %(ean)s.") % {"ean": ean})
        elif item.pk in basket:
            messages.warning(request, _("Cet exemplaire est déjà dans la liste."))
        else:
            check = check_item_loanable(item, member, basket_count=len(basket))
            if not check.ok:
                for err in check.errors:
                    messages.error(request, err)
            else:
                for warning in check.warnings:
                    messages.warning(request, warning)
                basket.append(item.pk)
                request.session["lend_basket"] = basket
        return redirect("loans:lend")

    if action == "remove_item":
        item_pk = int(request.POST.get("item_pk", 0))
        request.session["lend_basket"] = [pk for pk in basket if pk != item_pk]
        return redirect("loans:lend")

    if action == "validate":
        if not basket:
            messages.error(request, _("Aucun exemplaire à prêter."))
            return redirect("loans:lend")
        notes = request.POST.get("notes", "").strip()
        created = 0
        for item in Item.objects.filter(pk__in=basket).select_related("record"):
            check = check_item_loanable(item, member)
            if check.ok:
                create_loan(item, member, request.user, notes=notes)
                created += 1
            else:
                messages.error(
                    request,
                    _("%(title)s : %(err)s")
                    % {
                        "title": item.record.title,
                        "err": " ".join(str(e) for e in check.errors),
                    },
                )
        request.session.pop("lend_member", None)
        request.session.pop("lend_basket", None)
        messages.success(request, _("%(n)s prêt(s) enregistré(s).") % {"n": created})
        return redirect("members:detail", pk=member.pk)

    return redirect("loans:lend")


# ==========================================================================
# Retour (SPEC §6.3)
# ==========================================================================
@require_role(*WRITE_ROLES)
def return_items(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "clear":
            request.session.pop("return_log", None)
            return redirect("loans:return_items")
        if action == "add_item":
            _process_return(request)
            return redirect("loans:return_items")

    overdue_loans = (
        Loan.objects.filter(status__in=_OPEN_LOAN_STATUSES, due_date__lt=date.today())
        .select_related("item__record", "member")
        .order_by("due_date")
    )
    return render(
        request,
        "loans/return.html",
        {
            "return_log": request.session.get("return_log", []),
            "overdue_loans": overdue_loans,
        },
    )


def _process_return(request):
    ean = normalize_code(request.POST.get("ean", ""))
    item = Item.objects.filter(ean13=ean).select_related("record").first()
    if not item:
        messages.error(request, _("Exemplaire introuvable : %(ean)s.") % {"ean": ean})
        return
    result = return_item(item, request.user)
    log = request.session.get("return_log", [])
    entry = {
        "title": item.record.title,
        "internal_id": item.internal_id,
        "kind": result.kind,
        "overdue": result.was_overdue,
        "reservation": result.reservation.member.full_name if result.reservation else "",
    }
    log.insert(0, entry)
    request.session["return_log"] = log
    if result.kind == "no_loan":
        messages.warning(request, _("Aucun prêt actif pour cet exemplaire."))
    elif result.kind == "reintegrated":
        messages.success(request, _("Livre perdu réintégré au fonds."))
    else:
        messages.success(request, _("Retour enregistré : %(t)s.") % {"t": item.record.title})
    if result.reservation:
        messages.warning(
            request,
            _("À mettre de côté pour %(m)s (réservation).")
            % {"m": result.reservation.member.full_name},
        )


# ==========================================================================
# Renouvellement & livre perdu (SPEC §6.3)
# ==========================================================================
@require_POST
@require_role(*WRITE_ROLES)
def renew_loan_view(request, pk):
    loan = get_object_or_404(Loan.objects.select_related("item__record", "member"), pk=pk)
    result = renew_loan(loan)
    if result.ok:
        messages.success(
            request,
            _("Prêt renouvelé jusqu'au %(d)s.") % {"d": result.new_due_date},
        )
    else:
        messages.error(request, result.reason)
    return redirect("members:detail", pk=loan.member_id)


@require_role(*WRITE_ROLES)
def mark_lost(request, pk):
    loan = get_object_or_404(
        Loan.objects.select_related("item__record", "member"), pk=pk
    )
    if request.method == "POST":
        if loan.status in _OPEN_LOAN_STATUSES:
            declare_lost(loan)
            messages.success(request, _("Livre déclaré perdu."))
        else:
            messages.error(request, _("Ce prêt n'est pas actif."))
        return redirect("members:detail", pk=loan.member_id)
    return render(request, "loans/mark_lost.html", {"loan": loan})


# ==========================================================================
# Consultation sur place (SPEC §6.3)
# ==========================================================================
@require_role(*WRITE_ROLES)
def consultation(request):
    if request.method == "POST":
        form = ConsultationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Consultation sur place enregistrée."))
            return redirect("loans:consultation")
    else:
        form = ConsultationForm(initial={"date": date.today, "count": 1})
    return render(request, "loans/consultation.html", {"form": form})


# ==========================================================================
# Réservations (SPEC §6.4)
# ==========================================================================
@require_role(*WRITE_ROLES)
def reservation_list(request):
    ready = (
        Reservation.objects.filter(status=ReservationStatus.READY_FOR_PICKUP)
        .select_related("record", "member", "fulfilled_by_item")
        .order_by("ready_since")
    )
    pending = (
        Reservation.objects.filter(status=ReservationStatus.PENDING)
        .select_related("record", "member")
        .order_by("created_at")
    )
    return render(
        request, "loans/reservations.html", {"ready": ready, "pending": pending}
    )


@require_role(*WRITE_ROLES)
def reservation_create(request, record_pk):
    record = get_object_or_404(BibliographicRecord, pk=record_pk)
    if request.method == "POST":
        form = ReservationForm(request.POST)
        if form.is_valid():
            create_reservation(record, form.cleaned_data["member"])
            messages.success(request, _("Réservation enregistrée."))
            return redirect("catalog:record_detail", pk=record.pk)
    else:
        form = ReservationForm()
    return render(
        request, "loans/reservation_form.html", {"form": form, "record": record}
    )


@require_POST
@require_role(*WRITE_ROLES)
def reservation_cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    cancel_reservation(reservation)
    messages.success(request, _("Réservation annulée."))
    return redirect("loans:reservations")
