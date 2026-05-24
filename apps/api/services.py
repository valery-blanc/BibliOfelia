"""Services métier de l'API OfeliaScan. SPEC §6.10 / FEAT-021.

`finalize_scan_session()` matérialise les `ScanItem` d'une session en
`BibliographicRecord` + `Item` : matching par ISBN si possible, sinon
création. Sync v1, dans une transaction atomique.
"""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from apps.catalog.models import (
    BibliographicRecord,
    DocumentType,
    Item,
    ItemState,
    Location,
    MetadataQuality,
    MetadataSource,
    ScanItem,
    ScanSession,
    ScanSessionState,
)
from apps.catalog.openlibrary import normalize_isbn

_VALID_ITEM_STATES = {choice for choice, _label in ItemState.choices}


def _lookup_existing(isbn: str) -> BibliographicRecord | None:
    """Cherche un record par isbn_13 puis isbn_10. `isbn` déjà normalisé."""
    if not isbn:
        return None
    if len(isbn) == 13:
        rec = BibliographicRecord.objects.filter(isbn_13=isbn).first()
        if rec:
            return rec
    if len(isbn) == 10:
        rec = BibliographicRecord.objects.filter(isbn_10=isbn).first()
        if rec:
            return rec
    return None


def _resolve_location(code: str) -> Location | None:
    if not code:
        return None
    return Location.objects.filter(code=code).first()


def _resolve_state(value: str) -> str:
    return value if value in _VALID_ITEM_STATES else ItemState.GOOD


def _create_record(item: ScanItem, isbn: str) -> BibliographicRecord:
    """Crée un BibliographicRecord depuis les metadata d'un ScanItem.

    Si OfeliaScan envoie un ISBN sans titre, on stocke un placeholder
    language-neutral : ``ISBN:<isbn> - <dd.mm.aaaa hh.mn>``. Détecté et
    écrasé par FEAT-031 (cf. `apps/catalog/enrichment.py`).
    """
    if not item.metadata_title.strip():
        stamp = timezone.localtime(timezone.now()).strftime("%d.%m.%Y %H.%M")
        title = f"ISBN:{isbn or '??'} - {stamp}"
    else:
        title = item.metadata_title.strip()
    rec = BibliographicRecord.objects.create(
        title=title,
        publisher=item.metadata_publisher or "",
        publication_year=item.metadata_year,
        language=item.metadata_language or "fr",
        isbn_13=isbn if len(isbn) == 13 else None,
        isbn_10=isbn if len(isbn) == 10 else None,
        summary=f"[ScanSession:{item.session.session_id}]",
        document_type=DocumentType.BOOK,
        metadata_source=MetadataSource.SCAN_APP,
        metadata_quality=MetadataQuality.PARTIAL,
        created_by=item.session.created_by,
    )
    # Authors : create_or_get via full_name (cohérent avec demo.py)
    from apps.catalog.models import Author

    for name in item.metadata_authors or []:
        clean = (name or "").strip()
        if not clean:
            continue
        author, _ = Author.objects.get_or_create(full_name=clean)
        rec.authors.add(author)
    return rec


def _add_copies(
    record: BibliographicRecord, item: ScanItem, location: Location | None
) -> list[Item]:
    state = _resolve_state(item.item_state)
    notes_suffix = f"[ScanSession:{item.session.session_id}]"
    created = []
    for _ in range(max(1, item.copy_count)):
        it = Item.objects.create(
            record=record,
            location=location,
            state=state,
            notes=(item.notes or "") + ("\n" if item.notes else "") + notes_suffix,
        )
        created.append(it)
    return created


@transaction.atomic
def finalize_scan_session(session: ScanSession) -> dict:
    """Matérialise les items d'une session de scan. Retourne un résumé."""
    summary = {
        "items_processed": 0,
        "records_created": 0,
        "records_matched": 0,
        "copies_added": 0,
        "errors": [],
    }
    pending = list(session.items.filter(processed=False).select_related("session"))
    for item in pending:
        try:
            isbn = ""
            if item.scan_kind in ("isbn", "ean13") and item.scanned_value:
                normalized = normalize_isbn(item.scanned_value)
                if len(normalized) in (10, 13):
                    isbn = normalized

            record = _lookup_existing(isbn) if isbn else None
            matched = record is not None
            if not record:
                record = _create_record(item, isbn)

            location = _resolve_location(item.location_code)
            copies = _add_copies(record, item, location)

            item.processed = True
            item.processing_result = {
                "record_id": record.pk,
                "matched": matched,
                "copies_created": [it.pk for it in copies],
            }
            item.save(update_fields=["processed", "processing_result"])

            summary["items_processed"] += 1
            summary["records_matched" if matched else "records_created"] += 1
            summary["copies_added"] += len(copies)
        except Exception as exc:  # pragma: no cover (filet de sécurité)
            summary["errors"].append({"local_id": item.local_id, "error": str(exc)})

    session.state = ScanSessionState.FINALIZED
    session.finalized_at = timezone.now()
    session.processing_summary = summary
    session.save(update_fields=["state", "finalized_at", "processing_summary"])
    return summary
