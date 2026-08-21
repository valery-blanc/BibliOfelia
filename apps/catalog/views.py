"""Vues du catalogue : notices, exemplaires, recherche filtrée. SPEC §6.1."""
from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.accounts.models import Role
from apps.accounts.permissions import require_role
from apps.core.issn import ISSN_EAN13_PREFIX, issn_from_ean13
from apps.core.search import classify_query, fts_search
from apps.loans.models import LoanStatus, ReservationStatus

from .forms import (
    BibliographicRecordForm,
    CategoryForm,
    LanguageForm,
    ItemBulkCreateForm,
    ItemForm,
    LocationForm,
    ProvenanceForm,
    ScanCatalogSessionForm,
)
from .languages import language_choices
from .lookup import find_item
from .models import (
    BibliographicRecord,
    Category,
    DocumentType,
    ExcelCatalogJob,
    ExcelJobMode,
    Item,
    ItemState,
    ItemStatus,
    Language,
    Location,
    Provenance,
    RetiredItemCode,
    ScanInputMode,
    ScanItem,
    ScanKind,
    ScanSession,
    ScanSessionState,
)
from .openlibrary import lookup_isbn, lookup_isbn_multi, lookup_issn_multi, normalize_isbn

READ_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN, Role.READONLY)
WRITE_ROLES = (Role.LIBRARIAN, Role.SUPERADMIN)

# FEAT-073 : « sélectionner tous les résultats » peut viser des centaines de
# lignes. On plafonne ce que la page de confirmation **affiche** ; la sélection,
# elle, reste entière.
PREVIEW_LIMIT = 100

_ACTIVE_ITEM_STATUSES = (
    ItemStatus.AVAILABLE,
    ItemStatus.ON_LOAN,
    ItemStatus.RESERVED_FOR_PICKUP,
    ItemStatus.IN_REPAIR,
)


# ─── FEAT-073 : filtres du catalogue, réutilisables hors de l'affichage ────
# Extraits de `record_list` pour que les actions de masse puissent reconstruire
# exactement la même recherche quand l'utilisateur coche « tous les résultats » :
# sans ça, « sélectionner tout » ne pourrait porter que sur la page visible.


def filtered_records(params):
    """Notices correspondant aux filtres. Retourne `(queryset, relevance)`.

    `relevance` est l'ordre FTS (ou None) : l'affichage en a besoin, les actions
    de masse l'ignorent.
    """
    records = BibliographicRecord.objects.select_related("category").prefetch_related(
        "authors"
    )
    relevance = None

    q = (params.get("q") or "").strip()
    if q:
        kind, value = classify_query(q)
        # FEAT-063 : le code externe n'a pas de forme reconnaissable (il est
        # classé « text »), on tente donc la résolution d'exemplaire d'abord.
        item = find_item(q)
        if item is not None:
            records = records.filter(pk=item.record_id)
        elif kind == "isbn":
            records = records.filter(Q(isbn_13=value) | Q(isbn_10=value))
        elif kind == "issn":
            records = records.filter(issn=value)
        elif kind in ("item", "member"):
            # Code d'exemplaire ou carte d'usager qui ne correspond à rien :
            # pas de repli plein texte, ce serait du bruit.
            records = records.none()
        else:
            ids = fts_search(value)
            records = records.filter(pk__in=ids)
            relevance = {pk: i for i, pk in enumerate(ids)}

    if params.get("category"):
        records = records.filter(category_id=params["category"])
    if params.get("language"):
        records = records.filter(language=params["language"])
    if params.get("document_type"):
        records = records.filter(document_type=params["document_type"])
    q_tag = (params.get("q_tag") or "").strip()
    if q_tag:
        records = records.filter(tags__name__icontains=q_tag).distinct()

    # Emplacement et provenance qualifient l'exemplaire, pas la notice : en mode
    # notice on garde celles qui ont **au moins un** exemplaire qui correspond.
    if params.get("mode") != "items":
        if params.get("location"):
            records = records.filter(items__location_id=params["location"]).distinct()
        if params.get("provenance"):
            records = records.filter(
                items__provenance_id=params["provenance"]
            ).distinct()
    return records, relevance


def filtered_items(params, records=None):
    """Exemplaires correspondant aux filtres (mode « exemplaires »)."""
    if records is None:
        records, _relevance = filtered_records(params)
    items = (
        Item.objects.filter(record__in=records.values("pk"))
        .select_related("record", "record__category", "location", "provenance")
        .prefetch_related("record__authors")
    )
    if params.get("location"):
        items = items.filter(location_id=params["location"])
    if params.get("provenance"):
        items = items.filter(provenance_id=params["provenance"])
    return items


def _selected_pks(request, kind: str) -> list[int]:
    """Identifiants visés par une action de masse.

    Deux intentions bien distinctes (FEAT-073) :
    - cases cochées → les `ids` postés ;
    - « sélectionner tous les résultats » → **toute la recherche**, pages
      suivantes comprises, reconstruite depuis les filtres transmis dans
      `back_qs`. Se contenter des cases visibles ferait croire à l'utilisateur
      qu'il a tout traité alors qu'il n'aurait touché que 25 lignes.
    """
    if request.POST.get("select_all") == "1":
        params = QueryDict(request.POST.get("back_qs") or "")
        records, _relevance = filtered_records(params)
        if kind == "items":
            return list(filtered_items(params, records).values_list("pk", flat=True))
        return list(records.values_list("pk", flat=True))
    return [int(x) for x in request.POST.getlist("ids") if x.isdigit()]


@require_role(*READ_ROLES)
def record_list(request):
    """Catalogue : recherche filtrée, par notice ou par exemplaire. SPEC §6.1.

    `q` peut être :
    - un code Ofelia d'exemplaire (EAN13 290…) → la notice de cet exemplaire
    - un code Ofelia externe (FEAT-063) → idem
    - un ISBN 10/13 → filtre direct sur `isbn_13`/`isbn_10`
    - un ISSN (préfixe EAN13 977 ou saisi « 1828-552X ») → filtre sur `issn` (FEAT-052)
    - du texte libre → FTS5 sur titre/sous-titre/auteurs/résumé

    FEAT-064 : `mode=items` renvoie une ligne **par exemplaire** au lieu d'une
    ligne par notice. C'est le seul moyen de voir qu'un même titre a un
    exemplaire acheté et un exemplaire prêté par une autre bibliothèque — et
    donc de ne rendre que les seconds.
    """
    items_mode = request.GET.get("mode") == "items"
    q = (request.GET.get("q") or "").strip()
    records, relevance = filtered_records(request.GET)

    if items_mode:
        items = filtered_items(request.GET, records)
        if relevance is not None:
            rows = list(items)
            rows.sort(key=lambda it: (relevance.get(it.record_id, 1 << 30), it.internal_id))
        else:
            rows = items.order_by("record__title", "internal_id")
    else:
        rows = list(records)
        if relevance is not None:
            rows.sort(key=lambda r: relevance.get(r.pk, 1 << 30))
        else:
            rows.sort(key=lambda r: r.title.lower())

    paginator = Paginator(rows, 25)
    page = paginator.get_page(request.GET.get("page"))
    # Querystring sans `page` : permet aux liens de pagination de conserver
    # tous les filtres actifs (q, mode, category, document_type, language,
    # location, provenance, q_tag).
    base_params = request.GET.copy()
    base_params.pop("page", None)
    base_qs = base_params.urlencode()
    context = {
        "page_obj": page,
        "items_mode": items_mode,
        "q": q,
        "q_tag": (request.GET.get("q_tag") or "").strip(),
        "base_qs": base_qs,
        "total": paginator.count,
        "categories": Category.objects.all(),
        "locations": Location.objects.all(),
        "provenances": Provenance.objects.all(),
        "document_types": DocumentType.choices,
        # FEAT-070 : le filtre langue liste les langues du catalogue, pas les
        # 4 langues de l'interface — sinon un livre en allemand est infiltrable.
        "languages": language_choices(include_blank=False),
        "selected": {
            key: request.GET.get(key) or ""
            for key in ("category", "language", "document_type", "location", "provenance")
        },
    }
    return render(request, "catalog/record_list.html", context)


@require_role(*READ_ROLES)
def record_detail(request, pk):
    from apps.loans.models import Reservation, ReservationStatus
    from apps.loans.services import pickup_expiration_for

    record = get_object_or_404(
        BibliographicRecord.objects.prefetch_related("authors", "tags", "items__location"),
        pk=pk,
    )
    items = list(record.items.all())
    # FEAT-034 : pour chaque exemplaire en RESERVED_FOR_PICKUP, joindre la
    # réservation active pour afficher membre + date d'expiration côté UI.
    held_ids = [it.pk for it in items if it.status == ItemStatus.RESERVED_FOR_PICKUP]
    reservations_by_item: dict[int, Reservation] = {}
    if held_ids:
        for res in (
            Reservation.objects.filter(
                fulfilled_by_item_id__in=held_ids,
                status=ReservationStatus.READY_FOR_PICKUP,
            )
            .select_related("member")
        ):
            reservations_by_item[res.fulfilled_by_item_id] = res
    for it in items:
        res = reservations_by_item.get(it.pk)
        it.active_reservation = res
        it.reservation_expires_on = pickup_expiration_for(res) if res else None
    # FEAT-034 : liste d'attente niveau notice (PENDING + READY_FOR_PICKUP
    # non rattachées à un exemplaire visible). FIFO par date de création.
    pending_reservations = (
        Reservation.objects.filter(
            record=record,
            status__in=[ReservationStatus.PENDING, ReservationStatus.READY_FOR_PICKUP],
        )
        .select_related("member", "fulfilled_by_item")
        .order_by("created_at")
    )
    return render(
        request,
        "catalog/record_detail.html",
        {
            "record": record,
            "items": items,
            "pending_reservations": pending_reservations,
        },
    )


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
            # FEAT-063 : le code externe n'est acceptable que sur un exemplaire
            # unique (le formulaire refuse la combinaison code + copies > 1).
            external_code = form.cleaned_data.get("external_code") or ""
            for index in range(copies):
                Item.objects.create(
                    record=record,
                    external_code=external_code if index == 0 else "",
                    **base,
                )
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


_OPEN_LOAN_STATUSES = (LoanStatus.ACTIVE, LoanStatus.OVERDUE)
_OPEN_RESERVATION_STATUSES = (
    ReservationStatus.PENDING,
    ReservationStatus.READY_FOR_PICKUP,
)


@require_POST
@require_role(*WRITE_ROLES)
def item_delete(request, pk):
    """FEAT-027 : suppression définitive d'un exemplaire.

    Aucun blocage : prêts actifs → LOST (cas du vol), réservations actives
    → CANCELLED, prêts passés supprimés (CASCADE manuel car Loan.item=PROTECT).
    """
    item = get_object_or_404(Item, pk=pk)
    record_pk = item.record_id
    with transaction.atomic():
        item.loans.filter(status__in=_OPEN_LOAN_STATUSES).update(
            status=LoanStatus.LOST,
            return_date=timezone.now(),
        )
        item.fulfilled_reservations.filter(
            status__in=_OPEN_RESERVATION_STATUSES
        ).update(status=ReservationStatus.CANCELLED)
        item.loans.all().delete()
        item.delete()
    messages.success(request, _("Exemplaire supprimé."))
    return redirect("catalog:record_detail", pk=record_pk)


def _summarize_for_bulk_delete(records):
    """Calcule pour chaque notice : nb items, nb prêts actifs, nb résa actives."""
    summaries = []
    for record in records:
        items = list(record.items.all())
        active_loans = sum(1 for i in items if i.status == ItemStatus.ON_LOAN)
        active_reservations = record.reservations.filter(
            status__in=_OPEN_RESERVATION_STATUSES
        ).count()
        summaries.append({
            "record": record,
            "item_count": len(items),
            "active_loans": active_loans,
            "active_reservations": active_reservations,
        })
    return summaries


@require_POST
@require_role(Role.SUPERADMIN)
def record_bulk_delete_confirm(request):
    """FEAT-026 : page de confirmation pour la suppression en masse."""
    ids = _selected_pks(request, "records")
    records = (
        BibliographicRecord.objects
        .filter(pk__in=ids)
        .prefetch_related("items", "reservations")
        .order_by("title")
    )
    total = records.count()
    summaries = _summarize_for_bulk_delete(records[:PREVIEW_LIMIT])
    return render(
        request,
        "catalog/record_bulk_delete.html",
        {
            "summaries": summaries,
            "ids": ids,
            "count": total,
            "hidden_count": max(0, total - PREVIEW_LIMIT),
        },
    )


# ─── FEAT-069 : affectation en masse depuis la page catalogue ──────────────
# Plus de page de confirmation : la barre d'action porte les menus déroulants et
# poste directement ici. Sentinelle « keep » = ne pas modifier, chaîne vide =
# vider le champ — sans elle, les deux seraient indiscernables.

_KEEP = "keep"


def _chosen(request, field: str, model):
    """Lit un menu d'affectation. Retourne `(faut_il_modifier, objet_ou_None)`.

    `keep` (défaut) → on ne touche pas au champ ; chaîne vide → on le vide ;
    identifiant → on affecte l'objet. Un identifiant inconnu est traité comme un
    vidage plutôt que comme une erreur : la liste vient d'un menu déroulant, une
    valeur invalide ne peut venir que d'un objet supprimé entre-temps.
    """
    # `get(field, _KEEP)` et non `get(field) or _KEEP` : une chaîne vide est un
    # choix explicite (« vider »), pas une absence.
    raw = request.POST.get(field, _KEEP).strip()
    if raw == _KEEP:
        return False, None
    if not raw.isdigit():
        return True, None
    return True, model.objects.filter(pk=int(raw)).first()


@require_POST
@require_role(*WRITE_ROLES)
def record_bulk_assign(request):
    """Affecte catégorie et/ou emplacement aux notices visées.

    La catégorie appartient à la notice ; l'emplacement, lui, est porté par les
    exemplaires : on l'applique donc à **tous** les exemplaires des notices
    visées (comportement FEAT-041 conservé).
    """
    ids = _selected_pks(request, "records")
    done = []
    with transaction.atomic():
        change_cat, category = _chosen(request, "category", Category)
        if change_cat:
            n = BibliographicRecord.objects.filter(pk__in=ids).update(
                category_id=category.pk if category else None
            )
            done.append(
                _("%(n)s notice(s) → catégorie %(v)s") % {"n": n, "v": category.name}
                if category
                else _("%(n)s notice(s) sans catégorie") % {"n": n}
            )
        change_loc, location = _chosen(request, "location", Location)
        if change_loc:
            n = Item.objects.filter(record_id__in=ids).update(
                location_id=location.pk if location else None
            )
            done.append(
                _("%(n)s exemplaire(s) → emplacement %(v)s") % {"n": n, "v": location.code}
                if location
                else _("%(n)s exemplaire(s) sans emplacement") % {"n": n}
            )
    if done:
        messages.success(request, " · ".join(str(d) for d in done))
    else:
        messages.info(request, _("Rien à modifier : aucun menu n'a été changé."))
    return redirect(_back_to_catalog(request))


@require_POST
@require_role(*WRITE_ROLES)
def item_bulk_assign(request):
    """Affecte une provenance aux exemplaires visés."""
    ids = _selected_pks(request, "items")
    change, provenance = _chosen(request, "provenance", Provenance)
    if not change:
        messages.info(request, _("Rien à modifier : aucun menu n'a été changé."))
        return redirect(_back_to_catalog(request))
    n = Item.objects.filter(pk__in=ids).update(
        provenance_id=provenance.pk if provenance else None
    )
    messages.success(
        request,
        _("%(n)s exemplaire(s) → provenance %(v)s") % {"n": n, "v": provenance.code}
        if provenance
        else _("%(n)s exemplaire(s) sans provenance") % {"n": n},
    )
    return redirect(_back_to_catalog(request))


def _back_to_catalog(request) -> str:
    """Retour au catalogue en conservant les filtres actifs."""
    qs = (request.POST.get("back_qs") or "").lstrip("?")
    base = reverse("catalog:record_list")
    return f"{base}?{qs}" if qs else base


@require_POST
@require_role(Role.SUPERADMIN)
def record_bulk_delete(request):
    """FEAT-026 : exécution de la suppression en masse.

    Pour chaque notice : prêts actifs sur les items → LOST, résa actives
    sur la notice → CANCELLED, CASCADE manuel des prêts/consultations, puis
    delete (qui cascade les items via Item.record=CASCADE).
    """
    ids = _selected_pks(request, "records")
    qs = BibliographicRecord.objects.filter(pk__in=ids)
    deleted = 0
    user = request.user if request.user.is_authenticated else None
    with transaction.atomic():
        for record in qs:
            from apps.loans.models import Loan, InHouseConsultation, Reservation
            Loan.objects.filter(
                item__record=record, status__in=_OPEN_LOAN_STATUSES
            ).update(status=LoanStatus.LOST, return_date=timezone.now())
            Reservation.objects.filter(
                record=record, status__in=_OPEN_RESERVATION_STATUSES
            ).update(status=ReservationStatus.CANCELLED)
            Loan.objects.filter(item__record=record).delete()
            InHouseConsultation.objects.filter(item__record=record).delete()
            # FEAT-043 : tombstone explicite (reason=bulk_delete, retired_by)
            # avant le CASCADE (le signal pre_delete utilise get_or_create
            # donc ne réécrira pas ces lignes).
            for item in record.items.all():
                if not item.internal_id:
                    continue
                RetiredItemCode.objects.get_or_create(
                    internal_id=item.internal_id,
                    defaults={
                        "ean13": item.ean13 or "",
                        "record_title_snapshot": (record.title or "")[:255],
                        "retired_by": user,
                        "reason": RetiredItemCode.REASON_BULK_DELETE,
                    },
                )
            record.delete()
            deleted += 1
    messages.success(request, _("%(n)s notice(s) supprimée(s).") % {"n": deleted})
    return redirect("catalog:record_list")


# ─── FEAT-032 : gestion des emplacements (Location) ────────────────────────


@require_role(*WRITE_ROLES)
def location_list(request):
    """Liste des emplacements avec compteur d'exemplaires rattachés."""
    locations = (
        Location.objects.select_related("parent")
        .annotate(items_count=Count("items"))
        .order_by("code")
    )
    return render(
        request,
        "catalog/location_list.html",
        {"locations": locations, "total": locations.count()},
    )


@require_role(*WRITE_ROLES)
def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Emplacement créé."))
            return redirect("catalog:location_list")
    else:
        form = LocationForm()
    return render(
        request,
        "catalog/location_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:location_create"),
            "form_title": _("Nouvel emplacement"),
        },
    )


@require_role(*WRITE_ROLES)
def location_edit(request, pk):
    location = get_object_or_404(Location, pk=pk)
    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, _("Emplacement mis à jour."))
            return redirect("catalog:location_list")
    else:
        form = LocationForm(instance=location)
    return render(
        request,
        "catalog/location_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:location_edit", args=[pk]),
            "form_title": _("Modifier l'emplacement"),
            "location": location,
        },
    )


@require_role(*WRITE_ROLES)
def location_delete(request, pk):
    location = get_object_or_404(
        Location.objects.annotate(items_count=Count("items")), pk=pk
    )
    children_count = location.children.count()
    if request.method == "POST":
        # SET_NULL côté Item.location et InventorySession.scope_location :
        # les exemplaires rattachés perdent leur emplacement, l'historique des
        # sessions de récolement est conservé.
        location.delete()
        messages.success(request, _("Emplacement supprimé."))
        return redirect("catalog:location_list")
    return render(
        request,
        "catalog/location_confirm_delete.html",
        {
            "location": location,
            "items_count": location.items_count,
            "children_count": children_count,
        },
    )


# ─── FEAT-070 : gestion des langues ────────────────────────────────────────
# Une seule liste pour la langue des documents et les langues parlées des
# usagers. Extensible : un fonds peut contenir n'importe quelle langue.


@require_role(*WRITE_ROLES)
def language_list(request):
    """Liste des langues, triée par libellé traduit, avec le nombre de notices.

    `BibliographicRecord.language` est un code libre (les sources en ligne en
    renvoient de toutes sortes) : le compteur se fait par code, pas par clé
    étrangère.
    """
    rows = list(Language.objects.all())
    counts = dict(
        BibliographicRecord.objects.filter(language__in=[lang.code for lang in rows])
        .values_list("language")
        .annotate(n=Count("pk"))
    )
    for lang in rows:
        lang.records_count = counts.get(lang.code, 0)
    rows.sort(key=lambda lang: str(lang).lower())
    return render(
        request,
        "catalog/language_list.html",
        {"languages": rows, "total": len(rows)},
    )


@require_role(*WRITE_ROLES)
def language_create(request):
    if request.method == "POST":
        form = LanguageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Langue ajoutée."))
            return redirect("catalog:language_list")
    else:
        form = LanguageForm()
    return render(
        request,
        "catalog/language_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:language_create"),
            "form_title": _("Nouvelle langue"),
        },
    )


@require_role(*WRITE_ROLES)
def language_edit(request, pk):
    language = get_object_or_404(Language, pk=pk)
    if request.method == "POST":
        form = LanguageForm(request.POST, instance=language)
        if form.is_valid():
            form.save()
            messages.success(request, _("Langue mise à jour."))
            return redirect("catalog:language_list")
    else:
        form = LanguageForm(instance=language)
    return render(
        request,
        "catalog/language_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:language_edit", args=[pk]),
            "form_title": _("Modifier la langue"),
            "language": language,
        },
    )


@require_role(*WRITE_ROLES)
def language_delete(request, pk):
    """Retirer une langue de la liste ne touche à aucune notice.

    `BibliographicRecord.language` est un code libre : les notices gardent le
    leur, il s'affichera brut au lieu du libellé traduit.
    """
    language = get_object_or_404(Language, pk=pk)
    records_count = BibliographicRecord.objects.filter(language=language.code).count()
    if request.method == "POST":
        language.delete()
        messages.success(request, _("Langue retirée de la liste."))
        return redirect("catalog:language_list")
    return render(
        request,
        "catalog/language_confirm_delete.html",
        {"language": language, "records_count": records_count},
    )


# ─── FEAT-067 : gestion des catégories ─────────────────────────────────────
# Les catégories n'étaient modifiables que dans /admin/, jamais montré aux
# bibliothécaires : sans cet écran, l'abréviation de rayon ne serait saisissable
# par personne sur le terrain.


@require_role(*WRITE_ROLES)
def category_list(request):
    """Liste des catégories avec leur cote et le nombre de notices."""
    categories = (
        Category.objects.select_related("parent")
        .annotate(records_count=Count("records"))
        .order_by("code")
    )
    return render(
        request,
        "catalog/category_list.html",
        {"categories": categories, "total": categories.count()},
    )


@require_role(*WRITE_ROLES)
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie créée."))
            return redirect("catalog:category_list")
    else:
        form = CategoryForm()
    return render(
        request,
        "catalog/category_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:category_create"),
            "form_title": _("Nouvelle catégorie"),
        },
    )


@require_role(*WRITE_ROLES)
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Catégorie mise à jour."))
            return redirect("catalog:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(
        request,
        "catalog/category_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:category_edit", args=[pk]),
            "form_title": _("Modifier la catégorie"),
            "category": category,
        },
    )


@require_role(*WRITE_ROLES)
def category_delete(request, pk):
    """Supprimer une catégorie ne supprime aucune notice (SET_NULL)."""
    category = get_object_or_404(
        Category.objects.annotate(records_count=Count("records")), pk=pk
    )
    children_count = category.children.count()
    if request.method == "POST":
        category.delete()
        messages.success(request, _("Catégorie supprimée."))
        return redirect("catalog:category_list")
    return render(
        request,
        "catalog/category_confirm_delete.html",
        {
            "category": category,
            "records_count": category.records_count,
            "children_count": children_count,
        },
    )


# ─── FEAT-064 : gestion des provenances ────────────────────────────────────


@require_role(*WRITE_ROLES)
def provenance_list(request):
    """Liste des provenances avec le nombre d'exemplaires rattachés."""
    provenances = Provenance.objects.annotate(items_count=Count("items")).order_by("code")
    return render(
        request,
        "catalog/provenance_list.html",
        {"provenances": provenances, "total": provenances.count()},
    )


@require_role(*WRITE_ROLES)
def provenance_create(request):
    if request.method == "POST":
        form = ProvenanceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Provenance créée."))
            return redirect("catalog:provenance_list")
    else:
        form = ProvenanceForm()
    return render(
        request,
        "catalog/provenance_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:provenance_create"),
            "form_title": _("Nouvelle provenance"),
        },
    )


@require_role(*WRITE_ROLES)
def provenance_edit(request, pk):
    provenance = get_object_or_404(Provenance, pk=pk)
    if request.method == "POST":
        form = ProvenanceForm(request.POST, instance=provenance)
        if form.is_valid():
            form.save()
            messages.success(request, _("Provenance mise à jour."))
            return redirect("catalog:provenance_list")
    else:
        form = ProvenanceForm(instance=provenance)
    return render(
        request,
        "catalog/provenance_form.html",
        {
            "form": form,
            "form_action": reverse("catalog:provenance_edit", args=[pk]),
            "form_title": _("Modifier la provenance"),
            "provenance": provenance,
        },
    )


@require_role(*WRITE_ROLES)
def provenance_delete(request, pk):
    """Suppression d'une provenance — refusée tant que des exemplaires la portent.

    Item.provenance est en PROTECT : effacer une provenance encore utilisée
    ferait disparaître la seule trace de « à qui appartient ce livre ». On
    renvoie donc l'utilisateur vers la liste des exemplaires concernés.
    """
    provenance = get_object_or_404(
        Provenance.objects.annotate(items_count=Count("items")), pk=pk
    )
    if request.method == "POST":
        if provenance.items_count:
            messages.error(
                request,
                _("Impossible : %(n)s exemplaire(s) portent encore cette provenance.")
                % {"n": provenance.items_count},
            )
            return redirect("catalog:provenance_list")
        provenance.delete()
        messages.success(request, _("Provenance supprimée."))
        return redirect("catalog:provenance_list")
    return render(
        request,
        "catalog/provenance_confirm_delete.html",
        {"provenance": provenance, "items_count": provenance.items_count},
    )


# ─── FEAT-064 : actions de masse sur les exemplaires ───────────────────────
# Le mode « exemplaires » du catalogue coche des Item, pas des notices : ces
# vues sont le pendant de record_bulk_* pour ce mode.


def _selected_items_qs(request):
    ids = _selected_pks(request, "items")
    return ids, (
        Item.objects.filter(pk__in=ids)
        .select_related("record", "location", "provenance")
        .order_by("record__title", "internal_id")
    )


@require_POST
@require_role(Role.SUPERADMIN)
def item_bulk_delete_confirm(request):
    """Page de confirmation : ce qui sera supprimé, et ce que ça entraîne.

    Les identifiants sont réinjectés en clair dans le formulaire plutôt que de
    rejouer la recherche au moment de valider : ce qui a été confirmé est
    exactement ce qui sera supprimé, même si le catalogue bouge entre-temps.
    Seul **l'affichage** est plafonné, pour qu'une sélection de 900 exemplaires
    ne produise pas une page interminable.
    """
    ids, items = _selected_items_qs(request)
    items = list(items)
    on_loan = sum(1 for it in items if it.status == ItemStatus.ON_LOAN)
    reserved = sum(1 for it in items if it.status == ItemStatus.RESERVED_FOR_PICKUP)
    return render(
        request,
        "catalog/item_bulk_delete.html",
        {
            "items": items[:PREVIEW_LIMIT],
            "hidden_count": max(0, len(items) - PREVIEW_LIMIT),
            "ids": ids,
            "count": len(items),
            "on_loan": on_loan,
            "reserved": reserved,
        },
    )


@require_POST
@require_role(Role.SUPERADMIN)
def item_bulk_delete(request):
    """Suppression définitive d'exemplaires (rendre un fonds prêté, par ex.).

    Même traitement que la suppression unitaire (FEAT-027) : prêts en cours
    → LOST, réservations servies par ces exemplaires → CANCELLED, historique de
    prêts et consultations effacé (Loan.item est en PROTECT), et tombstone du
    code Ofelia (FEAT-043) pour qu'une étiquette déjà collée ne soit jamais
    réattribuée.
    """
    from apps.loans.models import InHouseConsultation, Loan, Reservation

    ids = _selected_pks(request, "items")
    user = request.user if request.user.is_authenticated else None
    items = list(Item.objects.filter(pk__in=ids).select_related("record"))
    with transaction.atomic():
        Loan.objects.filter(item_id__in=ids, status__in=_OPEN_LOAN_STATUSES).update(
            status=LoanStatus.LOST, return_date=timezone.now()
        )
        Reservation.objects.filter(
            fulfilled_by_item_id__in=ids, status__in=_OPEN_RESERVATION_STATUSES
        ).update(status=ReservationStatus.CANCELLED)
        Loan.objects.filter(item_id__in=ids).delete()
        InHouseConsultation.objects.filter(item_id__in=ids).delete()
        for item in items:
            if not item.internal_id:
                continue
            RetiredItemCode.objects.get_or_create(
                internal_id=item.internal_id,
                defaults={
                    "ean13": item.ean13 or "",
                    "record_title_snapshot": (item.record.title or "")[:255],
                    "retired_by": user,
                    "reason": RetiredItemCode.REASON_BULK_DELETE,
                },
            )
        Item.objects.filter(pk__in=ids).delete()
    messages.success(
        request, _("%(n)s exemplaire(s) supprimé(s).") % {"n": len(items)}
    )
    return redirect(f"{reverse('catalog:record_list')}?mode=items")


# ─── FEAT-046 : catalogage en scan caméra continu ──────────────────────────
# Miroir du récolement (FEAT-045) mais en création : on scanne des ISBN, on
# édite les notices détectées, puis `finalize_scan_session()` les matérialise.

# Seuil temporel : même ISBN re-vu après ce délai = exemplaire supplémentaire ;
# en deçà = double-lecture (livre tenu en vue) ignorée. Choisi > au refire du
# moteur caméra (~0,8 s) pour qu'un livre simplement maintenu ne miscompte pas.
CATALOGING_NEW_COPY_GAP_SECONDS = 3

_VALID_ITEM_STATES = {choice for choice, _label in ItemState.choices}


@require_role(*WRITE_ROLES)
def scan_session_list(request):
    """Liste des lots de catalogage (en cours + validés)."""
    sessions = ScanSession.objects.annotate(n_items=Count("items")).order_by("-started_at")
    open_sessions = [s for s in sessions if s.state == ScanSessionState.OPEN]
    done_sessions = [s for s in sessions if s.state != ScanSessionState.OPEN]
    return render(
        request,
        "catalog/scan_session_list.html",
        {"open_sessions": open_sessions, "done_sessions": done_sessions},
    )


def _scan_session_create(request, input_mode):
    """Démarre un lot : défauts catégorie/emplacement puis va au hub de scan.

    `input_mode` (FEAT-054) distingue le catalogage caméra du catalogage à la
    douchette USB ; il est stocké sur la session pour que le hub sache quel outil
    de saisie présenter (bouton caméra vs champ piloté par le keyboard-wedge).
    """
    if request.method == "POST":
        form = ScanCatalogSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.created_by = request.user
            session.input_mode = input_mode
            session.save()
            messages.success(request, _("Lot de catalogage démarré."))
            return redirect(reverse("catalog:scan_session", args=[session.pk]) + "?scan=1")
    else:
        form = ScanCatalogSessionForm()
    return render(
        request,
        "catalog/scan_session_form.html",
        {"form": form, "input_mode": input_mode},
    )


@require_role(*WRITE_ROLES)
def scan_session_create(request):
    """Catalogage caméra (FEAT-046)."""
    return _scan_session_create(request, ScanInputMode.CAMERA)


@require_role(*WRITE_ROLES)
def scan_douchette_create(request):
    """Catalogage à la douchette USB (FEAT-054)."""
    return _scan_session_create(request, ScanInputMode.DOUCHETTE)


@require_role(*WRITE_ROLES)
def scan_session(request, pk):
    """Hub de scan + édition des items détectés avant envoi au catalogue."""
    session = get_object_or_404(ScanSession, pk=pk)
    items = list(session.items.select_related("category").order_by("id"))
    # FEAT-046 : le hub édite l'emplacement par lot via un <select> de Location
    # (pk) alors que ScanItem stocke un `location_code` (texte). On résout le pk
    # courant pour pré-remplir le hidden input de chaque ligne.
    loc_by_code = {loc.code: loc.pk for loc in Location.objects.all()}
    for it in items:
        it.location_pk = loc_by_code.get(it.location_code, "")
        # FEAT-058 : lot validé consulté en lecture seule → lien vers la notice
        # effectivement créée/complétée par `finalize_scan_session`.
        it.record_pk = (it.processing_result or {}).get("record_id")
    return render(
        request,
        "catalog/scan_session.html",
        {
            "session": session,
            "items": items,
            "categories": Category.objects.all().order_by("code"),
            "locations": Location.objects.all().order_by("code"),
            "languages": language_choices(include_blank=False),
            "states": ItemState.choices,
            "finalized": session.state != ScanSessionState.OPEN,
            "input_mode": session.input_mode,
        },
    )


def _bump_existing(item: ScanItem, now) -> tuple[ScanItem, str]:
    """Re-lecture d'un ISBN déjà présent dans le lot : > seuil = exemplaire
    supplémentaire, sinon ignoré. `scanned_at` est rafraîchi à chaque vue, donc
    un livre tenu en vue en continu n'incrémente jamais (seul un retrait puis une
    re-présentation > seuil le fait)."""
    delta = (now - item.scanned_at).total_seconds()
    item.scanned_at = now
    if delta > CATALOGING_NEW_COPY_GAP_SECONDS:
        item.copy_count += 1
        item.save(update_fields=["scanned_at", "copy_count"])
        return item, "incremented"
    item.save(update_fields=["scanned_at"])
    return item, "ignored"


def _scan_item_label(item: ScanItem) -> str:
    """Libellé affiché dans le viseur : titre — auteur, sinon ISBN · langue."""
    author = ", ".join(item.metadata_authors or [])
    if item.metadata_title:
        return item.metadata_title + (" — " + author if author else "")
    return _("ISBN %(isbn)s · %(lang)s") % {
        "isbn": item.scanned_value,
        "lang": item.metadata_language or "fr",
    }


@transaction.non_atomic_requests
@require_POST
@require_role(*WRITE_ROLES)
def scan_add(request, pk):
    """Endpoint JSON appelé par `scan-cataloging.js` pour chaque code confirmé.

    Règle des exemplaires multiples : 1er scan = ScanItem (copy_count=1) ;
    même ISBN re-vu ≤ 3 s = ignoré ; > 3 s = copy_count+1 (« exemplaire X »).

    `non_atomic_requests` (settings `ATOMIC_REQUESTS = True`) : sans ça, toute la
    vue tourne dans une transaction qui ne committe qu'au retour de la réponse,
    et le `lookup_isbn` (HTTP lent) la tient ouverte → la ligne créée est
    invisible aux POST concurrents (caméra ré-émettant le même code ~0,6 s plus
    tard) → doublons (BUG 2026-05-31). En autocommit, chaque `create()` est
    visible immédiatement et la réconciliation/le bump fonctionnent.
    """
    session = get_object_or_404(ScanSession, pk=pk)
    if session.state != ScanSessionState.OPEN:
        return JsonResponse({"ok": False, "error": _("Ce lot est déjà validé.")}, status=409)

    code = normalize_isbn(request.POST.get("ean", ""))
    # Codes Ofelia : 290 = exemplaire déjà catalogué, 291 = carte membre.
    if len(code) == 13 and code[:3] in ("290", "291"):
        label = _("Déjà catalogué") if code[:3] == "290" else _("Carte membre — pas un livre")
        return JsonResponse({"ok": True, "action": "rejected", "isbn": code, "label": str(label)})
    if len(code) not in (10, 13):
        return JsonResponse({"ok": False, "error": _("Code invalide.")}, status=400)

    # FEAT-052 : périodique (EAN-13 préfixe 977). On extrait l'ISSN embarqué et
    # on interroge les sources ISSN au lieu des sources ISBN.
    is_issn = len(code) == 13 and code.startswith(ISSN_EAN13_PREFIX)
    issn = issn_from_ean13(code) if is_issn else None
    if is_issn and not issn:
        return JsonResponse({"ok": False, "error": _("Code invalide.")}, status=400)

    now = timezone.now()
    existing = session.items.filter(scanned_value=code).order_by("id").first()
    if existing:
        item, action = _bump_existing(existing, now)
    else:
        # On crée la ligne AVANT le lookup ISBN (rapide, sans HTTP) puis on
        # réconcilie. Sinon, le lookup (requête OpenLibrary, lente) s'intercale
        # entre le SELECT et l'INSERT : la caméra ré-émet le même code ~0,6 s
        # plus tard, son SELECT précède l'INSERT du 1er POST → doublon (BUG
        # 2026-05-31). La réconciliation garde l'id minimal de façon
        # déterministe → robuste même en concurrence, sans contrainte DB.
        item = ScanItem.objects.create(
            session=session,
            local_id=f"cam-{uuid.uuid4().hex[:12]}",
            scan_kind=(
                ScanKind.ISSN if is_issn
                else ScanKind.ISBN if len(code) == 10
                else ScanKind.EAN13
            ),
            scanned_value=code,
            metadata_language=(translation.get_language() or "fr")[:10],
            category=session.default_category,
            location_code=session.default_location.code if session.default_location_id else "",
            scanned_at=now,
            copy_count=1,
        )
        first = session.items.filter(scanned_value=code).order_by("id").first()
        if first.pk != item.pk:
            # Un POST concurrent a déjà créé la ligne : on annule la nôtre et on
            # traite ce scan comme une re-lecture du même livre.
            item.delete()
            item, action = _bump_existing(first, now)
        else:
            # Multi-sources (OpenLibrary + Google Books + BnF + BNE) : bien
            # meilleure couverture FR que la seule OpenLibrary (FEAT-046).
            # FEAT-052 : pour un périodique, sources ISSN (BnF/BNE) via l'ISSN.
            data = (lookup_issn_multi(issn) if is_issn else lookup_isbn_multi(code)) or {}
            authors_text = data.get("authors_text", "") or ""
            year = data.get("publication_year") or ""
            item.metadata_title = data.get("title", "") or ""
            item.metadata_authors = [a.strip() for a in authors_text.split(";") if a.strip()]
            item.metadata_publisher = data.get("publisher", "") or ""
            item.metadata_year = int(year) if str(year).isdigit() else None
            item.save(
                update_fields=[
                    "metadata_title", "metadata_authors",
                    "metadata_publisher", "metadata_year",
                ]
            )
            action = "created"

    if action == "incremented":
        label = _("exemplaire %(n)s") % {"n": item.copy_count}
    else:
        label = _scan_item_label(item)
    return JsonResponse(
        {
            "ok": True,
            "action": action,
            "isbn": code,
            "scanitem_id": item.pk,
            "copy_count": item.copy_count,
            "title": item.metadata_title,
            "author": ", ".join(item.metadata_authors or []),
            "language": item.metadata_language,
            "label": str(label),
            "count": session.items.count(),
        }
    )


@require_POST
@require_role(*WRITE_ROLES)
def scan_item_delete(request, pk, item_pk):
    """Retire une ligne mal scannée (session ouverte uniquement)."""
    session = get_object_or_404(ScanSession, pk=pk)
    if session.state == ScanSessionState.OPEN:
        session.items.filter(pk=item_pk).delete()
        messages.success(request, _("Ligne retirée."))
    return redirect("catalog:scan_session", pk=pk)


@require_POST
@require_role(*WRITE_ROLES)
def scan_session_commit(request, pk):
    """Enregistre les éditions du hub, puis finalise si `finalize` est présent."""
    session = get_object_or_404(ScanSession, pk=pk)
    if session.state != ScanSessionState.OPEN:
        messages.error(request, _("Ce lot est déjà validé."))
        return redirect("catalog:scan_session", pk=pk)

    # FEAT-046 : titre/auteur/langue sont en lecture seule sur le hub (issus du
    # lookup ISBN). Seuls catégorie / emplacement / état (modifiables par lot) et
    # le nombre d'exemplaires sont persistés ici.
    items = list(session.items.all())
    for it in items:
        sid = str(it.pk)
        cat_raw = request.POST.get(f"category_{sid}", "")
        it.category_id = int(cat_raw) if cat_raw.isdigit() else None
        loc_raw = request.POST.get(f"location_{sid}", "")
        loc = Location.objects.filter(pk=int(loc_raw)).first() if loc_raw.isdigit() else None
        it.location_code = loc.code if loc else ""
        state_raw = request.POST.get(f"state_{sid}", "")
        it.item_state = state_raw if state_raw in _VALID_ITEM_STATES else ""
        try:
            it.copy_count = max(1, min(99, int(request.POST.get(f"copies_{sid}", "1"))))
        except (TypeError, ValueError):
            it.copy_count = 1
        it.save(update_fields=["category", "location_code", "item_state", "copy_count"])

    if request.POST.get("finalize"):
        if not items:
            messages.error(request, _("Aucun livre scanné à envoyer."))
            return redirect("catalog:scan_session", pk=pk)
        from apps.api.services import finalize_scan_session

        summary = finalize_scan_session(session)
        messages.success(
            request,
            _("%(rec)s notice(s) créée(s), %(match)s complétée(s), %(cop)s exemplaire(s) ajouté(s).")
            % {
                "rec": summary.get("records_created", 0),
                "match": summary.get("records_matched", 0),
                "cop": summary.get("copies_added", 0),
            },
        )
        return redirect(reverse("printing:labels") + f"?catalog_session={session.pk}")

    messages.success(request, _("Modifications enregistrées."))
    return redirect("catalog:scan_session", pk=pk)


# ─── Catalogage Excel (FEAT-050) ───────────────────────────────────────────


@require_role(*WRITE_ROLES)
def excel_catalog_index(request):
    """Page de garde : 2 outils (Vérifier / Importer) + jobs récents."""
    jobs = ExcelCatalogJob.objects.filter(created_by=request.user)[:10]
    return render(request, "catalog/excel_catalog/index.html", {"jobs": jobs})


def _start_excel_job(request, mode):
    """Valide l'upload, crée le job et le pousse dans la file django-q2."""
    from django_q.tasks import async_task

    from .excel_catalog import validate_xlsx

    uploaded = request.FILES.get("file")
    if not uploaded:
        messages.error(request, _("Aucun fichier sélectionné."))
        return None
    errors = validate_xlsx(uploaded, mode)
    if errors:
        for err in errors:
            messages.error(request, err)
        return None
    job = ExcelCatalogJob.objects.create(
        mode=mode, uploaded_file=uploaded, created_by=request.user
    )
    async_task(
        "apps.catalog.excel_catalog.run_excel_catalog_job", job.pk,
        q_options={"timeout": 7200, "retry": 9000, "ack_failure": True},
    )
    return job


@require_POST
@require_role(*WRITE_ROLES)
def excel_catalog_verify_create(request):
    job = _start_excel_job(request, ExcelJobMode.VERIFY)
    if job is None:
        return redirect("catalog:excel_catalog_index")
    messages.success(request, _("Vérification lancée. Suivez l'avancement ici."))
    return redirect("catalog:excel_catalog_detail", pk=job.pk)


@require_POST
@require_role(*WRITE_ROLES)
def excel_catalog_import_create(request):
    job = _start_excel_job(request, ExcelJobMode.IMPORT)
    if job is None:
        return redirect("catalog:excel_catalog_index")
    messages.success(request, _("Import lancé. Suivez l'avancement ici."))
    return redirect("catalog:excel_catalog_detail", pk=job.pk)


@require_role(*WRITE_ROLES)
def excel_catalog_detail(request, pk):
    job = ExcelCatalogJob.objects.filter(pk=pk, created_by=request.user).first()
    if not job:
        return redirect("catalog:excel_catalog_index")
    return render(request, "catalog/excel_catalog/detail.html", {"job": job})


@require_role(*WRITE_ROLES)
def excel_catalog_download(request, pk):
    from django.http import FileResponse, Http404

    job = ExcelCatalogJob.objects.filter(pk=pk, created_by=request.user).first()
    if not job or not job.result_file:
        raise Http404
    return FileResponse(
        job.result_file.open("rb"),
        as_attachment=True,
        filename=f"verification-{job.pk}.xlsx",
    )
