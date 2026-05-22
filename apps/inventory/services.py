"""Logique de récolement : périmètre, pointage, rapport de divergences.
SPEC §6.5.
"""
from __future__ import annotations

from django.utils import timezone

from apps.catalog.models import Item, ItemStatus
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
    return scan, created


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
    return {
        "expected_count": len(expected_ids),
        "scanned_count": len(scanned_item_ids) + len(unknown),
        "present": [items[i] for i in present_ids if i in items],
        "missing": [items[i] for i in missing_ids if i in items],
        "misplaced": [items[i] for i in misplaced_ids if i in items],
        "unknown": unknown,
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
