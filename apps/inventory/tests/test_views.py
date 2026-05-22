"""Tests vues de récolement. SPEC §6.5 (Task #10)."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item, ItemStatus
from apps.inventory.models import InventoryScope, InventorySession, InventoryStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def item():
    record = BibliographicRecord.objects.create(title="Atlas")
    return Item.objects.create(record=record)


def test_session_create(client, librarian):
    client.force_login(librarian)
    resp = client.post("/fr/inventory/new/", {"label": "Été 2026", "scope_type": "all"})
    assert resp.status_code == 302
    assert InventorySession.objects.filter(label="Été 2026").exists()


def test_session_detail(client, librarian):
    session = InventorySession.objects.create(scope_type=InventoryScope.ALL)
    client.force_login(librarian)
    assert client.get(f"/fr/inventory/{session.pk}/").status_code == 200


def test_add_scan(client, librarian, item):
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": item.ean13})
    assert resp.status_code == 302
    assert session.scans.filter(item=item).exists()


def test_add_scan_rejected_when_closed(client, librarian, item):
    session = InventorySession.objects.create(status=InventoryStatus.CLOSED)
    client.force_login(librarian)
    client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": item.ean13})
    assert session.scans.count() == 0


def test_session_close_redirects_to_report(client, librarian):
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.post(f"/fr/inventory/{session.pk}/close/")
    assert resp.status_code == 302
    assert resp.url.endswith(f"/fr/inventory/{session.pk}/report/")
    session.refresh_from_db()
    assert session.status == InventoryStatus.CLOSED


def test_report_resolve_marks_item_lost(client, librarian, item):
    session = InventorySession.objects.create(status=InventoryStatus.CLOSED)
    client.force_login(librarian)
    resp = client.post(
        f"/fr/inventory/{session.pk}/resolve/", {"item_pk": item.pk}
    )
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.status == ItemStatus.LOST
