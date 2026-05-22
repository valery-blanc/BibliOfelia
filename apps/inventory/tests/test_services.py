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


def test_build_report_classifies_divergences(record, locations):
    a1, b2 = locations
    present = Item.objects.create(record=record, location=a1)
    missing = Item.objects.create(record=record, location=a1)
    misplaced = Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )
    record_scan(session, present.ean13)
    record_scan(session, misplaced.ean13)
    record_scan(session, "9990000000017")

    report = build_report(session)
    assert [i.pk for i in report["present"]] == [present.pk]
    assert [i.pk for i in report["missing"]] == [missing.pk]
    assert [i.pk for i in report["misplaced"]] == [misplaced.pk]
    assert report["unknown"] == ["9990000000017"]


def test_session_status_transitions():
    session = InventorySession.objects.create()
    close_session(session)
    assert session.status == InventoryStatus.CLOSED
    assert session.closed_at is not None
    reopen_session(session)
    assert session.status == InventoryStatus.OPEN
    finalize_session(session)
    assert session.status == InventoryStatus.FINALIZED
