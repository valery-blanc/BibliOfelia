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
    render_item_labels_pdf,
    render_member_cards_pdf,
    submit_to_cups,
)


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
    })


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def labels_pdf(request):
    ids = _extract_ids(request)
    items = list(
        Item.objects.filter(pk__in=ids).select_related("record", "location")
        .prefetch_related("record__authors")
    )
    if not items:
        messages.error(request, _("Aucun exemplaire sélectionné."))
        return redirect("printing:labels")
    pdf = render_item_labels_pdf(items)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'inline; filename="labels.pdf"'
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def labels_send(request):
    """Envoie directement à CUPS (Pi). Fallback : redirige vers le PDF."""
    if request.method != "POST":
        return redirect("printing:labels")
    ids = _extract_ids(request)
    items = list(
        Item.objects.filter(pk__in=ids).select_related("record", "location")
        .prefetch_related("record__authors")
    )
    if not items:
        messages.error(request, _("Aucun exemplaire sélectionné."))
        return redirect("printing:labels")
    pdf = render_item_labels_pdf(items)
    result = submit_to_cups(pdf, job_title="BibliOfelia labels")
    if result.sent:
        messages.success(request, _("Job d'impression envoyé (#%(id)s).") % {"id": result.job_id})
        return redirect("printing:labels")
    messages.warning(request, _("Imprimante indisponible : %(e)s") % {"e": result.error})
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'inline; filename="labels.pdf"'
    return resp


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def cards_picker(request):
    qs = Member.objects.all().order_by("-registration_date")[:500]
    return render(request, "printing/cards_picker.html", {"members": qs})


@require_role(Role.LIBRARIAN, Role.SUPERADMIN)
def cards_pdf(request):
    ids = _extract_ids(request)
    members = list(Member.objects.filter(pk__in=ids).select_related("category"))
    if not members:
        messages.error(request, _("Aucun usager sélectionné."))
        return redirect("printing:cards")
    pdf = render_member_cards_pdf(members)
    resp = HttpResponse(pdf, content_type="application/pdf")
    resp["Content-Disposition"] = 'inline; filename="cards.pdf"'
    return resp


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
