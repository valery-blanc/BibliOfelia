"""Vues du catalogue : notices, exemplaires, recherche filtrée. SPEC §6.1."""
from __future__ import annotations

from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.core.search import fts_search

from .forms import BibliographicRecordForm, ItemBulkCreateForm, ItemForm
from .models import (
    BibliographicRecord,
    Category,
    DocumentType,
    Item,
    ItemStatus,
)
from .openlibrary import lookup_isbn

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)

_ACTIVE_ITEM_STATUSES = (
    ItemStatus.AVAILABLE,
    ItemStatus.ON_LOAN,
    ItemStatus.RESERVED_FOR_PICKUP,
    ItemStatus.IN_REPAIR,
)


@require_role(*READ_ROLES)
def record_list(request):
    """Liste + recherche filtrée des notices. SPEC §6.1 (Recherche)."""
    q = (request.GET.get("q") or "").strip()
    records = BibliographicRecord.objects.select_related("category").prefetch_related(
        "authors"
    )
    relevance = None
    if q:
        ids = fts_search(q)
        records = records.filter(pk__in=ids)
        relevance = {pk: i for i, pk in enumerate(ids)}

    category = request.GET.get("category") or ""
    if category:
        records = records.filter(category_id=category)
    language = request.GET.get("language") or ""
    if language:
        records = records.filter(language=language)
    doc_type = request.GET.get("document_type") or ""
    if doc_type:
        records = records.filter(document_type=doc_type)

    records = list(records)
    if relevance is not None:
        records.sort(key=lambda r: relevance.get(r.pk, 1 << 30))
    else:
        records.sort(key=lambda r: r.title.lower())

    paginator = Paginator(records, 25)
    page = paginator.get_page(request.GET.get("page"))
    context = {
        "page_obj": page,
        "q": q,
        "total": len(records),
        "categories": Category.objects.all(),
        "document_types": DocumentType.choices,
        "selected": {
            "category": category,
            "language": language,
            "document_type": doc_type,
        },
    }
    return render(request, "catalog/record_list.html", context)


@require_role(*READ_ROLES)
def record_detail(request, pk):
    record = get_object_or_404(
        BibliographicRecord.objects.prefetch_related("authors", "tags", "items"),
        pk=pk,
    )
    return render(request, "catalog/record_detail.html", {"record": record})


def _render_record_form(request, form, form_action, title, show_lookup=False):
    context = {
        "form": form,
        "form_action": form_action,
        "form_title": title,
        "show_lookup": show_lookup,
    }
    if request.htmx:
        return render(request, "catalog/_record_form.html", context)
    return render(request, "catalog/record_form.html", context)


@require_role(*WRITE_ROLES)
def record_create(request):
    if request.method == "POST":
        form = BibliographicRecordForm(request.POST, request.FILES)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()
            form.save_m2m()
            form.sync_authors(record)
            messages.success(request, _("Notice créée."))
            return redirect("catalog:record_detail", pk=record.pk)
    else:
        form = BibliographicRecordForm()
    return _render_record_form(
        request, form, reverse("catalog:record_create"), _("Nouvelle notice"),
        show_lookup=True,
    )


@require_role(*WRITE_ROLES)
def record_edit(request, pk):
    record = get_object_or_404(BibliographicRecord, pk=pk)
    if request.method == "POST":
        form = BibliographicRecordForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, _("Notice mise à jour."))
            return redirect("catalog:record_detail", pk=record.pk)
    else:
        form = BibliographicRecordForm(instance=record)
    return _render_record_form(
        request, form, reverse("catalog:record_edit", args=[pk]), _("Modifier la notice")
    )


@require_role(*WRITE_ROLES)
def isbn_lookup(request):
    """Endpoint HTMX : pré-remplit le formulaire notice depuis OpenLibrary."""
    isbn = request.GET.get("isbn_13") or request.GET.get("isbn") or ""
    data = lookup_isbn(isbn)
    if data:
        form = BibliographicRecordForm(initial=data)
        messages.success(request, _("Notice trouvée sur OpenLibrary."))
    else:
        form = BibliographicRecordForm(initial={"isbn_13": isbn})
        messages.warning(
            request, _("Aucune réponse d'OpenLibrary — saisissez la notice à la main.")
        )
    return render(
        request,
        "catalog/_record_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:record_create"),
            "form_title": _("Nouvelle notice"),
            "show_lookup": True,
        },
    )


@require_role(*WRITE_ROLES)
def record_delete(request, pk):
    record = get_object_or_404(BibliographicRecord, pk=pk)
    active = record.items.filter(status__in=_ACTIVE_ITEM_STATUSES)
    if request.method == "POST":
        if active.exists():
            messages.error(
                request,
                _("Suppression impossible : des exemplaires actifs sont rattachés."),
            )
            return redirect("catalog:record_detail", pk=pk)
        record.delete()
        messages.success(request, _("Notice supprimée."))
        return redirect("catalog:record_list")
    return render(
        request,
        "catalog/record_confirm_delete.html",
        {"record": record, "blocked": active.exists()},
    )


@require_role(*WRITE_ROLES)
def item_create(request, record_pk):
    record = get_object_or_404(BibliographicRecord, pk=record_pk)
    if request.method == "POST":
        form = ItemBulkCreateForm(request.POST)
        if form.is_valid():
            copies = form.cleaned_data["copies"]
            base = {
                k: form.cleaned_data[k]
                for k in (
                    "location", "state", "acquisition_date",
                    "acquisition_source", "donor", "notes",
                )
            }
            for _i in range(copies):
                Item.objects.create(record=record, **base)
            messages.success(
                request, _("%(n)s exemplaire(s) ajouté(s).") % {"n": copies}
            )
            return redirect("catalog:record_detail", pk=record.pk)
    else:
        form = ItemBulkCreateForm()
    return render(
        request, "catalog/item_form.html", {"form": form, "record": record}
    )


@require_role(*WRITE_ROLES)
def item_edit(request, pk):
    item = get_object_or_404(Item.objects.select_related("record"), pk=pk)
    if request.method == "POST":
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, _("Exemplaire mis à jour."))
            return redirect("catalog:record_detail", pk=item.record_id)
    else:
        form = ItemForm(instance=item)
    return render(
        request, "catalog/item_form.html", {"form": form, "item": item, "record": item.record}
    )


@require_POST
@require_role(*WRITE_ROLES)
def item_discard(request, pk):
    """Suppression logique d'un exemplaire : passage en statut « pilonné »."""
    item = get_object_or_404(Item, pk=pk)
    if item.status in (ItemStatus.ON_LOAN, ItemStatus.RESERVED_FOR_PICKUP):
        messages.error(request, _("Impossible : l'exemplaire est prêté ou réservé."))
    else:
        item.status = ItemStatus.DISCARDED
        item.save(update_fields=["status"])
        messages.success(request, _("Exemplaire retiré du fonds."))
    return redirect("catalog:record_detail", pk=item.record_id)
