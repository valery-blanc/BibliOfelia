"""Vues de récolement. SPEC §6.5."""
from __future__ import annotations

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.core.search import normalize_code

from .forms import InventorySessionForm
from .models import InventorySession, InventoryStatus
from .services import (
    build_report,
    close_session,
    finalize_session,
    record_scan,
    reopen_session,
    scope_items,
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
            return redirect(reverse("inventory:report", args=[session.pk]) + "?scan=1")
    else:
        form = InventorySessionForm()
    return render(request, "inventory/session_form.html", {"form": form})


@require_POST
@require_role(*WRITE_ROLES)
def add_scan(request, pk):
    """Pointage caméra continu (FEAT-045). Endpoint JSON appelé par
    `scan-inventory.js` pour chaque code Ofelia confirmé."""
    session = get_object_or_404(InventorySession, pk=pk)
    if not session.is_open:
        return JsonResponse(
            {"ok": False, "error": _("Cette session est clôturée.")}, status=409
        )
    ean = normalize_code(request.POST.get("ean", ""))
    if not ean:
        return JsonResponse(
            {"ok": False, "error": _("Code vide.")}, status=400
        )
    scan, created = record_scan(session, ean)
    item_payload = None
    if scan.item_id:
        item = scan.item
        authors = ""
        copy_index = None
        if item.record_id:
            authors = ", ".join(a.full_name for a in item.record.authors.all())
            # Nᵉ exemplaire de cette notice pointé dans la session (FEAT-045) :
            # « exemplaire X » affiché pendant le scan pour distinguer les copies.
            copy_index = session.scans.filter(item__record_id=item.record_id).count()
        item_payload = {
            "internal_id": item.internal_id,
            "title": item.record.title if item.record_id else "",
            "author": authors,
            "copy_index": copy_index,
            "location_code": item.location.code if item.location_id else "",
        }
    return JsonResponse(
        {
            "ok": True,
            "created": created,
            "known": scan.item_id is not None,
            "ean": ean,
            "item": item_payload,
            "counts": {
                "expected": scope_items(session).count(),
                "scanned": session.scans.count(),
            },
        }
    )


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
    return redirect("inventory:report", pk=pk)


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
        {
            "session": session,
            "report": build_report(session),
            # FEAT-045 : codes déjà pointés → le scanner les ignore (dé-dup
            # client, y compris au « Continuer l'inventaire »).
            "scanned_eans": list(session.scans.values_list("ean13", flat=True)),
        },
    )
