"""Tests vues de récolement. SPEC §6.5 (Task #10)."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item
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


def test_session_create_redirects_to_report_scan(client, librarian):
    """FEAT-045 : la création redirige vers le rapport en mode scan."""
    client.force_login(librarian)
    resp = client.post("/fr/inventory/new/", {"label": "Été 2026", "scope_type": "all"})
    assert resp.status_code == 302
    session = InventorySession.objects.get(label="Été 2026")
    assert resp.url.endswith(f"/fr/inventory/{session.pk}/report/?scan=1")


def test_session_create_location_requires_location(client, librarian):
    """FEAT-045 : scope=location sans emplacement → formulaire invalide."""
    client.force_login(librarian)
    resp = client.post(
        "/fr/inventory/new/", {"label": "X", "scope_type": "location"}
    )
    assert resp.status_code == 200  # re-render avec erreur
    assert not InventorySession.objects.filter(label="X").exists()


def test_session_detail_route_gone(client, librarian):
    """FEAT-045 : l'ancienne page détail n'existe plus."""
    session = InventorySession.objects.create(scope_type=InventoryScope.ALL)
    client.force_login(librarian)
    assert client.get(f"/fr/inventory/{session.pk}/").status_code == 404


def test_add_scan_returns_json(client, librarian, item):
    """FEAT-045 : endpoint JSON, exemplaire reconnu."""
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": item.ean13})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["created"] is True
    assert data["known"] is True
    assert data["counts"]["scanned"] == 1
    assert session.scans.filter(item=item).exists()


def test_add_scan_unknown_code(client, librarian):
    """FEAT-045 : code hors catalogue → known=false mais enregistré."""
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.post(
        f"/fr/inventory/{session.pk}/scan/", {"ean": "2909999999992"}
    )
    data = resp.json()
    assert data["ok"] is True
    assert data["known"] is False
    assert data["item"] is None


def test_add_scan_idempotent(client, librarian, item):
    """FEAT-045 : re-scan du même code → created=false (dé-dup serveur)."""
    session = InventorySession.objects.create()
    client.force_login(librarian)
    client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": item.ean13})
    resp = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": item.ean13})
    assert resp.json()["created"] is False
    assert session.scans.count() == 1


def test_form_page_renders(client, librarian):
    """FEAT-045 : la page de création rend (template + JS scope)."""
    client.force_login(librarian)
    assert client.get("/fr/inventory/new/").status_code == 200


def test_report_page_renders_with_scan_panel(client, librarian, item):
    """FEAT-045 : la page rapport rend, panneau de scan présent si session ouverte."""
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.get(f"/fr/inventory/{session.pk}/report/")
    assert resp.status_code == 200
    assert b"js-scan-inventory" in resp.content
    assert b"scan-inventory-config" in resp.content
    # FEAT-045 : la liste des codes déjà pointés est exposée pour la dé-dup client.
    assert b"inv-scanned-eans" in resp.content


def test_add_scan_payload_includes_author(client, librarian):
    """FEAT-045 : le JSON renvoie l'auteur pour l'affichage live dans le viseur."""
    from apps.catalog.models import Author

    record = BibliographicRecord.objects.create(title="Atlas")
    record.authors.add(Author.objects.create(full_name="Élisée Reclus"))
    it = Item.objects.create(record=record)
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": it.ean13})
    data = resp.json()
    assert data["item"]["title"] == "Atlas"
    assert data["item"]["author"] == "Élisée Reclus"


def test_add_scan_rejected_when_closed(client, librarian, item):
    session = InventorySession.objects.create(status=InventoryStatus.CLOSED)
    client.force_login(librarian)
    resp = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": item.ean13})
    assert resp.status_code == 409
    assert session.scans.count() == 0


def test_session_close_redirects_to_report(client, librarian):
    session = InventorySession.objects.create()
    client.force_login(librarian)
    resp = client.post(f"/fr/inventory/{session.pk}/close/")
    assert resp.status_code == 302
    assert resp.url.endswith(f"/fr/inventory/{session.pk}/report/")
    session.refresh_from_db()
    assert session.status == InventoryStatus.CLOSED


def test_resolve_route_gone(client, librarian, item):
    """FEAT-045 : l'action « marquer perdu » du rapport a été retirée."""
    session = InventorySession.objects.create(status=InventoryStatus.CLOSED)
    client.force_login(librarian)
    assert client.post(
        f"/fr/inventory/{session.pk}/resolve/", {"item_pk": item.pk}
    ).status_code == 404


def test_add_scan_copy_index_increments_per_record(client, librarian):
    """FEAT-045 : « exemplaire X » — l'index monte par exemplaire d'une notice."""
    record = BibliographicRecord.objects.create(title="Atlas")
    copy1 = Item.objects.create(record=record)
    copy2 = Item.objects.create(record=record)
    session = InventorySession.objects.create()
    client.force_login(librarian)
    r1 = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": copy1.ean13})
    r2 = client.post(f"/fr/inventory/{session.pk}/scan/", {"ean": copy2.ean13})
    assert r1.json()["item"]["copy_index"] == 1
    assert r2.json()["item"]["copy_index"] == 2
