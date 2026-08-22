"""Vues d'impression (§6.7) : étiquettes exemplaires et cartes membres."""
from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.catalog.models import Item
from apps.members.models import Member

from .services import (
    _roll_settings,
    render_item_labels_pdf,
    render_item_labels_roll_pdf,
    render_member_cards_pdf,
    render_member_cards_roll_pdf,
    render_spine_labels_roll_pdf,
    spine_label_text,
)


def _pdf_response(pdf: bytes, filename: str) -> HttpResponse:
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = f'inline; filename="{filename}"'
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def labels_picker(request):
    """Écran de sélection : choisit les exemplaires à étiqueter (par filtre)."""
    qs = Item.objects.select_related("record", "location").order_by("-created_at")
    location = request.GET.get("location") or ""
    if location:
        qs = qs.filter(location__code=location)
    # FEAT-046 : n'imprimer que les étiquettes d'un lot de catalogage donné.
    catalog_session = request.GET.get("catalog_session") or ""
    session_label = ""
    if catalog_session.isdigit():
        from apps.catalog.models import ScanSession
        qs = qs.filter(catalog_session_id=int(catalog_session))
        sess = ScanSession.objects.filter(pk=int(catalog_session)).first()
        if sess:
            session_label = sess.label or f"#{sess.pk}"
    pending = request.GET.get("pending") == "1"
    if pending:
        # exemplaires créés sans étiquette imprimée — non tracé en v1, fallback : derniers 100
        qs = qs[:100]
    elif catalog_session.isdigit():
        qs = qs[:1000]
    else:
        qs = qs[:500]
    return render(request, "printing/labels_picker.html", {
        "items": qs, "location": location, "pending": pending,
        "catalog_session": catalog_session, "session_label": session_label,
        "roll": _roll_settings(),
    })


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def labels_pdf(request):
    items = _selected_items(request)
    if not items:
        messages.error(request, _("Aucun exemplaire sélectionné."))
        return redirect("printing:labels")
    return _pdf_response(render_item_labels_pdf(items), "labels.pdf")


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def cards_picker(request):
    qs = Member.objects.all().order_by("-registration_date")[:500]
    return render(request, "printing/cards_picker.html", {
        "members": qs, "roll": _roll_settings(),
    })


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def cards_pdf(request):
    members = _selected_members(request)
    if not members:
        messages.error(request, _("Aucun usager sélectionné."))
        return redirect("printing:cards")
    return _pdf_response(render_member_cards_pdf(members), "cards.pdf")


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def labels_roll_pdf(request):
    """FEAT-062 : PDF ruban continu, une étiquette par page."""
    items = _selected_items(request)
    if not items:
        messages.error(request, _("Aucun exemplaire sélectionné."))
        return redirect("printing:labels")
    return _pdf_response(render_item_labels_roll_pdf(items), "labels-ruban.pdf")


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def cards_roll_pdf(request):
    """FEAT-062 : PDF ruban continu, une carte membre par page."""
    members = _selected_members(request)
    if not members:
        messages.error(request, _("Aucun usager sélectionné."))
        return redirect("printing:cards")
    return _pdf_response(render_member_cards_roll_pdf(members), "cartes-ruban.pdf")


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def spine_labels_roll_pdf(request):
    """FEAT-068 : étiquettes de tranche, une cote de catégorie par page."""
    items = _selected_items(request)
    if not items:
        messages.error(request, _("Aucun exemplaire sélectionné."))
        return redirect("printing:labels")
    printable = [item for item in items if spine_label_text(item)]
    if not printable:
        messages.error(
            request,
            _("Aucun exemplaire sélectionné n'a de catégorie abrégée : "
              "renseignez l'abréviation de la catégorie avant d'imprimer."),
        )
        return redirect("printing:labels")
    return _pdf_response(
        render_spine_labels_roll_pdf(printable), "etiquettes-tranche.pdf"
    )


def _selected_items(request) -> list:
    return list(
        Item.objects.filter(pk__in=_extract_ids(request))
        .select_related("record", "record__category", "location")
        .prefetch_related("record__authors")
    )


def _selected_members(request) -> list:
    return list(
        Member.objects.filter(pk__in=_extract_ids(request)).select_related("category")
    )


def _extract_ids(request) -> list[int]:
    raw = request.GET.getlist("ids") or request.POST.getlist("ids")
    if not raw and request.method == "POST":
        # tolère un champ unique séparé par virgules
        raw = request.POST.get("ids", "").split(",")
    out = []
    for v in raw:
        try:
            out.append(int(v))
        except (TypeError, ValueError):
            pass
    return out
