"""Tests logique de récolement. SPEC §6.5 (Task #10)."""
from __future__ import annotations

import pytest

from apps.catalog.models import BibliographicRecord, Item, ItemStatus, Location
from apps.inventory.models import InventoryScope, InventorySession, InventoryStatus
from apps.inventory.services import (
    build_report,
    close_session,
    finalize_session,
    record_scan,
    reopen_session,
    scope_items,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def record():
    return BibliographicRecord.objects.create(title="Encyclopédie")


@pytest.fixture
def locations():
    return Location.objects.create(code="A1"), Location.objects.create(code="B2")


def test_scope_items_all(record):
    Item.objects.create(record=record)
    Item.objects.create(record=record, status=ItemStatus.DISCARDED)
    session = InventorySession.objects.create(scope_type=InventoryScope.ALL)
    # les exemplaires pilonnés sont exclus du périmètre
    assert scope_items(session).count() == 1


def test_scope_items_by_location(record, locations):
    a1, b2 = locations
    Item.objects.create(record=record, location=a1)
    Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )
    assert scope_items(session).count() == 1


def test_scope_excludes_on_loan_items(record):
    """Un exemplaire prêté n'est pas attendu au pointage (il est chez l'usager)
    et ne doit donc jamais remonter en « manquant »."""
    Item.objects.create(record=record, status=ItemStatus.AVAILABLE)
    Item.objects.create(record=record, status=ItemStatus.ON_LOAN)
    session = InventorySession.objects.create(scope_type=InventoryScope.ALL)
    assert scope_items(session).count() == 1


def test_record_scan_resolves_item(record):
    item = Item.objects.create(record=record)
    session = InventorySession.objects.create()
    scan, created = record_scan(session, item.ean13)
    assert created is True
    assert scan.item_id == item.pk


def test_record_scan_deduplicates(record):
    item = Item.objects.create(record=record)
    session = InventorySession.objects.create()
    record_scan(session, item.ean13)
    _scan, created = record_scan(session, item.ean13)
    assert created is False
    assert session.scans.count() == 1


def test_record_scan_unknown_code(record):
    session = InventorySession.objects.create()
    scan, _created = record_scan(session, "9990000000017")
    assert scan.item_id is None


def test_build_report_classifies_divergences_scope_category(record, locations):
    """Classification présents / manquants / mal-rangés / inconnus en scope
    catégorie (qui n'active PAS la relocate automatique de FEAT-033)."""
    from apps.catalog.models import Category

    a1, b2 = locations
    cat_a = Category.objects.create(code="A", name="A")
    cat_b = Category.objects.create(code="B", name="B")
    record.category = cat_a
    record.save(update_fields=["category"])
    record_b = BibliographicRecord.objects.create(title="Autre", category=cat_b)

    present = Item.objects.create(record=record, location=a1)
    missing = Item.objects.create(record=record, location=a1)
    misplaced = Item.objects.create(record=record_b, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.CATEGORY, scope_category=cat_a
    )
    record_scan(session, present.ean13)
    record_scan(session, misplaced.ean13)  # bonne catégorie ? non → misplaced
    record_scan(session, "9990000000017")

    report = build_report(session)
    assert [i.pk for i in report["present"]] == [present.pk]
    assert [i.pk for i in report["missing"]] == [missing.pk]
    assert [i.pk for i in report["misplaced"]] == [misplaced.pk]
    assert report["unknown"] == ["9990000000017"]


def test_build_report_with_relocate_in_location_scope(record, locations):
    """FEAT-033 : en scope location, un item mal-rangé scanné est *déplacé*
    automatiquement et devient présent. Plus de catégorie « misplaced » en
    pratique (sauf items déjà déplacés dans une session antérieure)."""
    a1, b2 = locations
    present = Item.objects.create(record=record, location=a1)
    missing = Item.objects.create(record=record, location=a1)
    misplaced = Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )
    record_scan(session, present.ean13)
    record_scan(session, misplaced.ean13)  # B2 → A1 par FEAT-033
    record_scan(session, "9990000000017")

    report = build_report(session)
    session.refresh_from_db()
    assert {i.pk for i in report["present"]} == {present.pk, misplaced.pk}
    assert [i.pk for i in report["missing"]] == [missing.pk]
    assert report["misplaced"] == []
    assert report["unknown"] == ["9990000000017"]
    assert session.relocate_count == 1


def test_build_report_by_record_groups_and_colors(record, locations):
    """FEAT-045 : regroupement par notice, codes trouvés/manquants, tri auteur/titre."""
    from apps.catalog.models import Author

    a1, _b2 = locations
    record.authors.add(Author.objects.create(full_name="Zola"))
    found = Item.objects.create(record=record, location=a1)
    missing = Item.objects.create(record=record, location=a1)

    other = BibliographicRecord.objects.create(title="Aaa")
    other.authors.add(Author.objects.create(full_name="Andersen"))
    other_item = Item.objects.create(record=other, location=a1)

    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )
    record_scan(session, found.ean13)
    record_scan(session, other_item.ean13)

    by_record = build_report(session)["by_record"]
    # Tri par auteur : Andersen avant Zola.
    assert [r["author"] for r in by_record] == ["Andersen", "Zola"]
    zola = next(r for r in by_record if r["author"] == "Zola")
    assert zola["total"] == 2 and zola["found_count"] == 1
    by_code = {it["ean13"]: it["found"] for it in zola["items"]}
    assert by_code[found.ean13] is True
    assert by_code[missing.ean13] is False


def test_session_status_transitions():
    session = InventorySession.objects.create()
    close_session(session)
    assert session.status == InventoryStatus.CLOSED
    assert session.closed_at is not None
    reopen_session(session)
    assert session.status == InventoryStatus.OPEN
    finalize_session(session)
    assert session.status == InventoryStatus.FINALIZED
