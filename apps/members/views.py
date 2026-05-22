"""Vues usagers : inscription, fiche, historique, carte, renouvellement.
SPEC §6.2.
"""
from __future__ import annotations

from collections import Counter

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.loans.models import LoanStatus

from .forms import MemberForm
from .models import Member, MemberCategory, MemberStatus
from .notifications import member_alerts
from .services import (
    days_until_expiration,
    is_expiring_soon,
    renew_card,
    replace_card,
)

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)

_ACTIVE_LOAN_STATUSES = (LoanStatus.ACTIVE, LoanStatus.OVERDUE)


@require_role(*READ_ROLES)
def member_list(request):
    q = (request.GET.get("q") or "").strip()
    members = Member.objects.select_related("category")
    if q:
        members = members.filter(
            Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(card_number__icontains=q)
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
        Member.objects.select_related("category", "parent_account"), pk=pk
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
            "dependents": member.dependents.all(),
            "days_left": days_until_expiration(member),
            "expiring_soon": is_expiring_soon(member),
            "alerts": member_alerts(member),
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
        if form.is_valid():
            member = form.save()
            messages.success(
                request,
                _("Usager inscrit — carte n° %(card)s.") % {"card": member.card_number},
            )
            return redirect("members:detail", pk=member.pk)
    else:
        form = MemberForm()
    return render(
        request, "members/member_form.html", {"form": form, "form_title": _("Nouvel usager")}
    )


@require_role(*WRITE_ROLES)
def member_edit(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if request.method == "POST":
        form = MemberForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, _("Fiche usager mise à jour."))
            return redirect("members:detail", pk=member.pk)
    else:
        form = MemberForm(instance=member)
    return render(
        request,
        "members/member_form.html",
        {"form": form, "member": member, "form_title": _("Modifier l'usager")},
    )


@require_POST
@require_role(*WRITE_ROLES)
def member_replace_card(request, pk):
    member = get_object_or_404(Member, pk=pk)
    new_number = replace_card(member)
    messages.success(
        request, _("Nouvelle carte émise : n° %(card)s.") % {"card": new_number}
    )
    return redirect("members:detail", pk=member.pk)


@require_POST
@require_role(*WRITE_ROLES)
def member_renew(request, pk):
    member = get_object_or_404(Member, pk=pk)
    new_date = renew_card(member)
    messages.success(
        request,
        _("Carte renouvelée jusqu'au %(date)s.") % {"date": new_date},
    )
    return redirect("members:detail", pk=member.pk)
