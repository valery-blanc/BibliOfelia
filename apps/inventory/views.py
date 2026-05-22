"""Vues de récolement. SPEC §6.5."""
from __future__ import annotations

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.catalog.models import Item, ItemStatus

from .forms import InventorySessionForm
from .models import InventorySession, InventoryStatus
from .services import (
    build_report,
    close_session,
    finalize_session,
    record_scan,
    reopen_session,
    session_progress,
)

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)


@require_role(*READ_ROLES)
def session_list(request):
    sessions = InventorySession.objects.select_related(
        "scope_location", "scope_category"
    )
    open_sessions = [s for s in sessions if s.status == InventoryStatus.OPEN]
    closed_sessions = [s for s in sessions if s.status != InventoryStatus.OPEN]
    return render(
        request,
        "inventory/session_list.html",
        {"open_sessions": open_sessions, "closed_sessions": closed_sessions},
    )


@require_role(*WRITE_ROLES)
def session_create(request):
    if request.method == "POST":
        form = InventorySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.save()
            messages.success(request, _("Session de récolement créée."))
            return redirect("inventory:detail", pk=session.pk)
    else:
        form = InventorySessionForm()
    return render(request, "inventory/session_form.html", {"form": form})


@require_role(*READ_ROLES)
def session_detail(request, pk):
    session = get_object_or_404(
        InventorySession.objects.select_related("scope_location", "scope_category"),
        pk=pk,
    )
    return render(
        request,
        "inventory/session_detail.html",
        {
            "session": session,
            "progress": session_progress(session),
            "scans": session.scans.select_related("item__record")[:100],
        },
    )


@require_POST
@require_role(*WRITE_ROLES)
def add_scan(request, pk):
    session = get_object_or_404(InventorySession, pk=pk)
    if not session.is_open:
        messages.error(request, _("Cette session est clôturée."))
        return redirect("inventory:detail", pk=pk)
    _scan, created = record_scan(session, request.POST.get("ean", ""))
    if created:
        messages.success(request, _("Exemplaire pointé."))
    else:
        messages.warning(request, _("Cet exemplaire a déjà été pointé."))
    return redirect("inventory:detail", pk=pk)


@require_POST
@require_role(*WRITE_ROLES)
def session_close(request, pk):
    session = get_object_or_404(InventorySession, pk=pk)
    close_session(session)
    messages.success(request, _("Récolement clôturé — consultez le rapport."))
    return redirect("inventory:report", pk=pk)


@require_POST
@require_role(*WRITE_ROLES)
def session_reopen(request, pk):
    session = get_object_or_404(InventorySession, pk=pk)
    if session.status == InventoryStatus.FINALIZED:
        messages.error(request, _("Une session validée ne peut pas être rouverte."))
    else:
        reopen_session(session)
        messages.success(request, _("Récolement rouvert."))
    return redirect("inventory:detail", pk=pk)


@require_POST
@require_role(*WRITE_ROLES)
def session_finalize(request, pk):
    session = get_object_or_404(InventorySession, pk=pk)
    finalize_session(session)
    messages.success(request, _("Récolement validé définitivement."))
    return redirect("inventory:report", pk=pk)


@require_role(*READ_ROLES)
def session_report(request, pk):
    session = get_object_or_404(InventorySession, pk=pk)
    return render(
        request,
        "inventory/session_report.html",
        {"session": session, "report": build_report(session)},
    )


@require_POST
@require_role(*WRITE_ROLES)
def resolve_missing(request, pk):
    """Action sur une divergence : marquer un exemplaire manquant comme perdu."""
    session = get_object_or_404(InventorySession, pk=pk)
    item = get_object_or_404(Item, pk=request.POST.get("item_pk"))
    item.status = ItemStatus.LOST
    item.save(update_fields=["status"])
    messages.success(
        request, _("%(id)s marqué perdu.") % {"id": item.internal_id}
    )
    return redirect("inventory:report", pk=session.pk)
