"""Vues usagers : inscription, fiche, historique, carte, renouvellement,
désactivation, suppression. SPEC §6.2.
"""
from __future__ import annotations

from collections import Counter
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.catalog.models import ItemStatus
from apps.finance.money import format_amount
from apps.finance.services import (
    create_membership_invoice,
    member_account,
    reconcile_membership_invoices,
)
from apps.loans.models import LoanStatus, ReservationStatus

from .forms import MemberFamilyFormSet, MemberForm
from .models import Member, MemberCategory, MemberStatus
from .notifications import member_alerts
from .services import (
    CardStillValid,
    can_renew,
    days_until_expiration,
    is_expiring_soon,
    renew_card,
    replace_card,
)

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)

_ACTIVE_LOAN_STATUSES = (LoanStatus.ACTIVE, LoanStatus.OVERDUE)


def _membership_change_messages(request, result: dict) -> None:
    """Retours de `reconcile_membership_invoices` après un changement de catégorie."""
    cancelled = result.get("cancelled") or []
    created = result.get("created")
    if cancelled and created:
        messages.info(
            request,
            _("Cotisation recalculée : facture %(old)s annulée, %(new)s émise (%(amount)s).")
            % {
                "old": cancelled[0].number,
                "new": created.number,
                "amount": format_amount(created.total_amount),
            },
        )
        return
    if cancelled:
        messages.info(
            request,
            _("Facture de cotisation %(num)s annulée : la nouvelle catégorie n'en a pas.")
            % {"num": cancelled[0].number},
        )
        return
    if created is not None:
        messages.info(
            request,
            _("Facture de cotisation %(num)s émise (%(amount)s).")
            % {
                "num": created.number,
                "amount": format_amount(created.total_amount),
            },
        )


@require_role(*READ_ROLES)
def member_list(request):
    q = (request.GET.get("q") or "").strip()
    members = Member.objects.select_related("category")
    if q:
        # FEAT-081 : `replaces_card_number` dans la recherche, sinon scanner une
        # ancienne carte sur cet écran ne remonte aucune ligne — alors que le
        # prêt, lui, reconnaît la même carte.
        members = members.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(card_number__icontains=q)
            | Q(replaces_card_number__icontains=q)
        )
    category = request.GET.get("category") or ""
    if category:
        members = members.filter(category_id=category)
    status = request.GET.get("status") or ""
    if status:
        members = members.filter(status=status)

    paginator = Paginator(members.order_by("last_name", "first_name"), 25)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "members/member_list.html",
        {
            "page_obj": page,
            "q": q,
            "categories": MemberCategory.objects.all(),
            "statuses": MemberStatus.choices,
            "selected": {"category": category, "status": status},
        },
    )


@require_role(*READ_ROLES)
def member_detail(request, pk):
    member = get_object_or_404(
        Member.objects.select_related("category").prefetch_related("family"), pk=pk
    )
    active_loans = (
        member.loans.filter(status__in=_ACTIVE_LOAN_STATUSES)
        .select_related("item__record")
        .order_by("due_date")
    )
    return render(
        request,
        "members/member_detail.html",
        {
            "member": member,
            "active_loans": active_loans,
            "active_count": active_loans.count(),
            "days_left": days_until_expiration(member),
            "expiring_soon": is_expiring_soon(member),
            "alerts": member_alerts(member),
            # BUG-041 : le gabarit grise le bouton quand la carte est encore
            # valable pour plus de 30 jours.
            "can_renew": can_renew(member),
            # FEAT-084 : encadré « Compte » (à jour / à régler / en retard).
            "account": member_account(member),
        },
    )


@require_role(*READ_ROLES)
def member_history(request, pk):
    """Historique de prêt complet d'un usager. SPEC §6.2."""
    member = get_object_or_404(Member, pk=pk)
    loans = member.loans.select_related("item__record__category").order_by("-loan_date")
    active = [loan for loan in loans if loan.status in _ACTIVE_LOAN_STATUSES]
    past = [loan for loan in loans if loan.status not in _ACTIVE_LOAN_STATUSES]
    by_category = Counter(
        (loan.item.record.category.name if loan.item.record.category else _("Sans catégorie"))
        for loan in loans
    )
    return render(
        request,
        "members/member_history.html",
        {
            "member": member,
            "active_loans": active,
            "past_loans": past,
            "consultations": member.consultations.select_related("item__record"),
            "stats_by_category": sorted(by_category.items()),
            "total_loans": len(loans),
        },
    )


@require_role(*WRITE_ROLES)
def member_create(request):
    if request.method == "POST":
        form = MemberForm(request.POST, request.FILES)
        family = MemberFamilyFormSet(request.POST)
        if form.is_valid() and family.is_valid():
            member = form.save()
            family.instance = member
            family.save()
            messages.success(
                request,
                _("Usager inscrit — carte n° %(card)s.") % {"card": member.card_number},
            )
            # FEAT-084 : cotisation facturée à l'inscription, du montant porté
            # par la catégorie. Une catégorie gratuite n'émet rien.
            invoice = create_membership_invoice(member, user=request.user)
            if invoice is not None:
                messages.info(
                    request,
                    _("Facture de cotisation %(num)s émise (%(amount)s).")
                    % {
                        "num": invoice.number,
                        "amount": format_amount(invoice.total_amount),
                    },
                )
            return redirect("members:detail", pk=member.pk)
    else:
        form = MemberForm()
        family = MemberFamilyFormSet()
    return render(
        request,
        "members/member_form.html",
        {"form": form, "family": family, "form_title": _("Nouvel usager")},
    )


@require_role(*WRITE_ROLES)
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    # Avant `is_valid()` : ModelForm._post_clean écrit déjà la nouvelle
    # catégorie sur l'instance, et on perdrait l'ancienne.
    old_category_id = member.category_id
    if request.method == "POST":
        form = MemberForm(request.POST, request.FILES, instance=member)
        family = MemberFamilyFormSet(request.POST, instance=member)
        if form.is_valid() and family.is_valid():
            form.save()
            family.save()
            messages.success(request, _("Fiche usager mise à jour."))
            # BUG-042 : la cotisation suit la catégorie. Sans ça, passer
            # d'Adulte (20 CHF) à Employé (0) laisse la facture d'Adulte
            # ouverte, et l'encadré Compte affiche encore « Cotisation 20 CHF ».
            if member.category_id != old_category_id:
                result = reconcile_membership_invoices(
                    member, user=request.user
                )
                _membership_change_messages(request, result)
            return redirect("members:detail", pk=member.pk)
    else:
        form = MemberForm(instance=member)
        family = MemberFamilyFormSet(instance=member)
    return render(
        request,
        "members/member_form.html",
        {
            "form": form,
            "family": family,
            "member": member,
            "form_title": _("Modifier l'usager"),
        },
    )


@require_POST
@require_role(*WRITE_ROLES)
def member_replace_card(request, pk):
    member = get_object_or_404(Member, pk=pk)
    old_number = member.card_number
    new_number = replace_card(member)
    messages.success(
        request, _("Nouvelle carte émise : n° %(card)s.") % {"card": new_number}
    )
    # FEAT-081 : le numéro change en base, mais la carte physique dans la poche
    # de l'usager porte encore l'ancien. Sans ce rappel, on découvre le décalage
    # au comptoir, des jours plus tard, en scannant une carte qui n'est plus la
    # bonne. L'ancien numéro reste reconnu partout (`find_member`) et signalé.
    messages.warning(
        request,
        _("La carte n° %(old)s est désormais l'ancienne : imprimez la nouvelle "
          "carte et remettez-la à l'usager. En attendant, l'ancienne reste "
          "reconnue au scan et le signale.") % {"old": old_number},
    )
    return redirect("members:detail", pk=member.pk)


@require_POST
@require_role(*WRITE_ROLES)
def member_renew(request, pk):
    member = get_object_or_404(Member, pk=pk)
    try:
        new_date, invoice = renew_card(member, user=request.user)
    except CardStillValid as exc:
        # BUG-041 : le bouton est grisé, mais un POST direct ne doit pas non
        # plus empiler les années.
        messages.warning(
            request,
            _("Carte déjà valable jusqu'au %(date)s : rien à renouveler.")
            % {"date": exc.expiration_date},
        )
        return redirect("members:detail", pk=member.pk)
    messages.success(
        request,
        _("Carte renouvelée jusqu'au %(date)s.") % {"date": new_date},
    )
    if invoice is not None:
        messages.info(
            request,
            _("Facture de cotisation %(num)s émise.") % {"num": invoice.number},
        )
    return redirect("members:detail", pk=member.pk)


@require_POST
@require_role(*WRITE_ROLES)
def member_toggle_active(request, pk):
    """FEAT-028 : toggle ACTIVE ↔ SUSPENDED. Réactive aussi EXPIRED/CLOSED."""
    member = get_object_or_404(Member, pk=pk)
    if member.status == MemberStatus.ACTIVE:
        member.status = MemberStatus.SUSPENDED
        msg = _("Usager désactivé.")
    else:
        member.status = MemberStatus.ACTIVE
        if member.expiration_date and member.expiration_date < date.today():
            months = member.category.card_validity_months or 12
            member.expiration_date = date.today() + relativedelta(months=months)
        msg = _("Usager réactivé.")
    member.save(update_fields=["status", "expiration_date"])
    messages.success(request, msg)
    return redirect("members:detail", pk=member.pk)


_ACTIVE_RESERVATION_STATUSES = (
    ReservationStatus.PENDING,
    ReservationStatus.READY_FOR_PICKUP,
)


@require_role(Role.SUPERADMIN)
def member_delete(request, pk):
    """FEAT-029 : suppression d'un membre (admin).

    Aucun blocage : prêts actifs → RETURNED + items libérés, réservations
    actives → CANCELLED, dépendants détachés, prêts/résa/consultations
    passés → CASCADE manuel (Loan/Reservation.member=PROTECT), puis delete.
    """
    member = get_object_or_404(Member, pk=pk)
    active_loans = member.loans.filter(status__in=_ACTIVE_LOAN_STATUSES)
    active_reservations = member.reservations.filter(
        status__in=_ACTIVE_RESERVATION_STATUSES
    )
    past_loans_count = member.loans.exclude(
        status__in=_ACTIVE_LOAN_STATUSES
    ).count()
    if request.method == "POST":
        with transaction.atomic():
            active_reservations.update(status=ReservationStatus.CANCELLED)
            for loan in list(active_loans.select_related("item")):
                loan.status = LoanStatus.RETURNED
                loan.return_date = timezone.now()
                loan.save(update_fields=["status", "return_date"])
                if loan.item.status == ItemStatus.ON_LOAN:
                    loan.item.status = ItemStatus.AVAILABLE
                    loan.item.save(update_fields=["status"])
            member.loans.all().delete()
            member.reservations.all().delete()
            member.consultations.all().delete()
            full_name = member.full_name
            member.delete()
        messages.success(request, _("Usager %(n)s supprimé.") % {"n": full_name})
        return redirect("members:list")

    return render(
        request,
        "members/member_confirm_delete.html",
        {
            "member": member,
            "active_loans": active_loans,
            "active_reservations_count": active_reservations.count(),
            "past_loans_count": past_loans_count,
        },
    )
