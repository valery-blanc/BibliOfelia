"""Tests FEAT-033 : réassignation automatique des exemplaires au récolement.

Quand une session est scopée sur une location et qu'un exemplaire est scanné,
sa `location` est forcée vers `session.scope_location` (s'il n'y est pas
déjà). Comportement systématique, pas de toggle.
"""
from __future__ import annotations

import pytest

from apps.catalog.models import BibliographicRecord, Item, Location
from apps.inventory.models import InventoryScope, InventorySession
from apps.inventory.services import record_scan

pytestmark = pytest.mark.django_db


@pytest.fixture
def record():
    return BibliographicRecord.objects.create(title="Encyclopédie")


@pytest.fixture
def locations():
    return Location.objects.create(code="A1"), Location.objects.create(code="B2")


def test_relocate_moves_item_from_other_location(record, locations):
    """Item catalogué en B2, session scopée A1 : le scan le déplace en A1."""
    a1, b2 = locations
    item = Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )

    record_scan(session, item.ean13)

    item.refresh_from_db()
    session.refresh_from_db()
    assert item.location_id == a1.pk
    assert session.relocate_count == 1


def test_relocate_assigns_location_to_unassigned_item(record, locations):
    """Item sans emplacement : le scan lui en donne un (cas du baptême)."""
    a1, _ = locations
    item = Item.objects.create(record=record, location=None)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )

    record_scan(session, item.ean13)

    item.refresh_from_db()
    session.refresh_from_db()
    assert item.location_id == a1.pk
    assert session.relocate_count == 1


def test_no_relocate_when_already_correct(record, locations):
    """Item déjà en A1 : pas de save, compteur reste à 0."""
    a1, _ = locations
    item = Item.objects.create(record=record, location=a1)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )

    record_scan(session, item.ean13)

    item.refresh_from_db()
    session.refresh_from_db()
    assert item.location_id == a1.pk
    assert session.relocate_count == 0


def test_no_relocate_scope_all(record, locations):
    """scope_type=all : pas de location-cible, pas de réassignation."""
    a1, b2 = locations
    item = Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(scope_type=InventoryScope.ALL)

    record_scan(session, item.ean13)

    item.refresh_from_db()
    session.refresh_from_db()
    assert item.location_id == b2.pk
    assert session.relocate_count == 0


def test_no_relocate_scope_category(record, locations):
    """scope_type=category : pas de location-cible, pas de réassignation."""
    a1, b2 = locations
    item = Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.CATEGORY, scope_category=None
    )

    record_scan(session, item.ean13)

    item.refresh_from_db()
    session.refresh_from_db()
    assert item.location_id == b2.pk
    assert session.relocate_count == 0


def test_no_relocate_for_unknown_ean(locations):
    """EAN scanné qui ne matche aucun Item : pas de crash, pas de relocate."""
    a1, _ = locations
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )

    scan, created = record_scan(session, "2909999999998")

    session.refresh_from_db()
    assert scan.item_id is None
    assert session.relocate_count == 0


def test_relocate_count_accumulates_across_scans(record, locations):
    """Plusieurs items mal-rangés scannés successivement : compteur cumule."""
    a1, b2 = locations
    items = [
        Item.objects.create(record=record, location=b2)
        for _ in range(3)
    ]
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )

    for item in items:
        record_scan(session, item.ean13)

    session.refresh_from_db()
    assert session.relocate_count == 3
    for item in items:
        item.refresh_from_db()
        assert item.location_id == a1.pk


def test_replay_same_scan_does_not_double_count(record, locations):
    """Rejouer le même scan (idempotence get_or_create) : compteur stable."""
    a1, b2 = locations
    item = Item.objects.create(record=record, location=b2)
    session = InventorySession.objects.create(
        scope_type=InventoryScope.LOCATION, scope_location=a1
    )

    record_scan(session, item.ean13)  # relocate B2 → A1, count=1
    record_scan(session, item.ean13)  # déjà en A1, count reste à 1

    session.refresh_from_db()
    assert session.relocate_count == 1
