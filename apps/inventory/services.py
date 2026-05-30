"""Logique de récolement : périmètre, pointage, rapport de divergences.
SPEC §6.5.
"""
from __future__ import annotations

from collections import defaultdict

from django.db import models
from django.utils import timezone

from apps.catalog.models import BibliographicRecord, Item, ItemStatus
from apps.core.search import normalize_code

from .models import InventoryScan, InventoryScope, InventorySession, InventoryStatus


# Exemplaires censés être physiquement présents lors d'un récolement. Les
# exemplaires prêtés (chez l'usager), perdus, en réparation ou pilonnés ne sont
# pas attendus au pointage et ne doivent pas remonter en « manquants ».
_EXPECTED_STATUSES = (ItemStatus.AVAILABLE, ItemStatus.RESERVED_FOR_PICKUP)


def scope_items(session: InventorySession):
    """Exemplaires attendus dans le périmètre de la session.

    Seuls les exemplaires censés se trouver dans la bibliothèque (disponibles ou
    mis de côté) sont attendus ; un exemplaire prêté n'est pas « manquant »."""
    qs = Item.objects.filter(status__in=_EXPECTED_STATUSES).select_related("record")
    if session.scope_type == InventoryScope.LOCATION and session.scope_location_id:
        qs = qs.filter(location_id=session.scope_location_id)
    elif session.scope_type == InventoryScope.CATEGORY and session.scope_category_id:
        qs = qs.filter(record__category_id=session.scope_category_id)
    return qs


def record_scan(session: InventorySession, raw_ean: str, device: str = ""):
    """Enregistre un pointage. Retourne (scan, created)."""
    ean = normalize_code(raw_ean)
    item = Item.objects.filter(ean13=ean).first()
    scan, created = InventoryScan.objects.get_or_create(
        session=session,
        ean13=ean,
        defaults={"item": item, "device": device},
    )
    maybe_relocate(item, session)
    return scan, created


def maybe_relocate(item: Item | None, session: InventorySession) -> bool:
    """FEAT-033 : si la session est scopée sur une location et que
    l'exemplaire scanné n'y est pas (ou n'a pas d'emplacement), on le force
    vers `session.scope_location`. Retourne True si déplacé.

    Logique : pendant un récolement sur l'emplacement X, on tient
    physiquement les livres en main à cet endroit — donc ils y sont, point.
    Le scan terrain est la source de vérité.

    Ne fait rien pour `scope_type=all` ou `scope_type=category` (pas de
    location-cible évidente). Ne fait rien si l'EAN ne matche aucun Item.
    """
    if item is None:
        return False
    if session.scope_type != InventoryScope.LOCATION:
        return False
    if not session.scope_location_id:
        return False
    if item.location_id == session.scope_location_id:
        return False
    item.location_id = session.scope_location_id
    item.save(update_fields=["location"])
    InventorySession.objects.filter(pk=session.pk).update(
        relocate_count=models.F("relocate_count") + 1
    )
    # Garder l'instance Python à jour pour les appelants (tests, vue
    # `record_scan` qui retourne ensuite la session).
    session.relocate_count = (session.relocate_count or 0) + 1
    return True


def build_report(session: InventorySession) -> dict:
    """Rapport de récolement : présents, manquants, mal rangés, inconnus.
    SPEC §6.5 (Rapport)."""
    expected_ids = set(scope_items(session).values_list("id", flat=True))
    scanned_item_ids: set[int] = set()
    unknown: list[str] = []
    for scan in session.scans.all():
        if scan.item_id:
            scanned_item_ids.add(scan.item_id)
        else:
            unknown.append(scan.ean13)

    present_ids = scanned_item_ids & expected_ids
    missing_ids = expected_ids - scanned_item_ids
    misplaced_ids = scanned_item_ids - expected_ids

    items = {
        it.id: it
        for it in Item.objects.filter(
            id__in=present_ids | missing_ids | misplaced_ids
        ).select_related("record", "location")
    }

    # FEAT-045 : regroupement par notice des exemplaires attendus (présents +
    # manquants), trié par auteur puis titre. Chaque code Ofelia est marqué
    # trouvé (vert) ou manquant (rouge) dans le template.
    expected_by_record: dict[int, list[Item]] = defaultdict(list)
    for iid in present_ids | missing_ids:
        it = items.get(iid)
        if it:
            expected_by_record[it.record_id].append(it)
    records = {
        r.id: r
        for r in BibliographicRecord.objects.filter(
            id__in=expected_by_record.keys()
        ).prefetch_related("authors")
    }
    by_record = []
    for rid, its in expected_by_record.items():
        rec = records.get(rid)
        if rec is None:
            continue
        author = ", ".join(a.full_name for a in rec.authors.all())
        its_sorted = sorted(its, key=lambda i: i.ean13)
        by_record.append(
            {
                "record": rec,
                "author": author,
                "title": rec.title,
                "items": [
                    {
                        "ean13": i.ean13,
                        "internal_id": i.internal_id,
                        "found": i.id in present_ids,
                    }
                    for i in its_sorted
                ],
                "found_count": sum(1 for i in its if i.id in present_ids),
                "total": len(its),
            }
        )
    by_record.sort(key=lambda r: (r["author"].lower(), r["title"].lower()))

    return {
        "expected_count": len(expected_ids),
        "scanned_count": len(scanned_item_ids) + len(unknown),
        "present": [items[i] for i in present_ids if i in items],
        "missing": [items[i] for i in missing_ids if i in items],
        "misplaced": [items[i] for i in misplaced_ids if i in items],
        "unknown": unknown,
        "by_record": by_record,
    }


def session_progress(session: InventorySession) -> dict:
    """Compteurs temps réel pour la page de session."""
    expected = scope_items(session).count()
    scanned = session.scans.count()
    return {"expected": expected, "scanned": scanned}


def close_session(session: InventorySession) -> None:
    session.status = InventoryStatus.CLOSED
    session.closed_at = timezone.now()
    session.save(update_fields=["status", "closed_at"])


def reopen_session(session: InventorySession) -> None:
    session.status = InventoryStatus.OPEN
    session.closed_at = None
    session.save(update_fields=["status", "closed_at"])


def finalize_session(session: InventorySession) -> None:
    session.status = InventoryStatus.FINALIZED
    if session.closed_at is None:
        session.closed_at = timezone.now()
    session.save(update_fields=["status", "closed_at"])
