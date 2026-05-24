"""Tests des endpoints OfeliaScan « inventory-sessions » (FEAT-021 / Task #20).

Cible : POST /inventory-sessions, /items, /close.

Couvre le contrat (corps enveloppé `{"items":[...]}`, `scanned_value`,
`scanned_at`), scopes location/category, ownership, idempotency.
"""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    Item,
    Location,
)
from apps.inventory.models import InventoryScan, InventorySession, InventoryStatus

PASSWORD = "ofelia-test-pwd"


@pytest.fixture
def scanner(db):
    return User.objects.create_user(
        username="scanner", password=PASSWORD, role=Role.CONTRIBUTOR_API
    )


@pytest.fixture
def other_scanner(db):
    return User.objects.create_user(
        username="scanner2", password=PASSWORD, role=Role.CONTRIBUTOR_API
    )


@pytest.fixture
def client():
    return APIClient()


def _auth(client, username="scanner"):
    resp = client.post(
        "/api/v1/auth/login",
        {"username": username, "password": PASSWORD},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access_token']}")


@pytest.mark.django_db
class TestInventoryCreate:
    def test_requires_auth(self, client):
        assert client.post("/api/v1/inventory-sessions").status_code == 401

    def test_default_scope_all_sets_mobile_created(self, client, scanner):
        _auth(client)
        resp = client.post("/api/v1/inventory-sessions", {}, format="json")
        assert resp.status_code == 201
        sid = resp.json()["session_id"]
        session = InventorySession.objects.get(session_id=sid)
        assert session.mobile_created is True
        assert session.scope_type == "all"
        assert session.created_by_id == scanner.id

    def test_scope_location_code_resolved(self, client, scanner):
        _auth(client)
        Location.objects.create(code="A1")
        resp = client.post(
            "/api/v1/inventory-sessions",
            {"scope_type": "location", "scope_location_code": "A1"},
            format="json",
        )
        assert resp.status_code == 201
        sid = resp.json()["session_id"]
        session = InventorySession.objects.get(session_id=sid)
        assert session.scope_location.code == "A1"

    def test_unknown_location_returns_400(self, client, scanner):
        _auth(client)
        resp = client.post(
            "/api/v1/inventory-sessions",
            {"scope_type": "location", "scope_location_code": "ZZ"},
            format="json",
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "unknown_location"


@pytest.mark.django_db
class TestInventoryItems:
    def test_batch_items_enveloped(self, client, scanner):
        _auth(client)
        rec = BibliographicRecord.objects.create(title="T")
        Item.objects.create(record=rec, ean13="2900000000017")
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        resp = client.post(
            f"/api/v1/inventory-sessions/{sid}/items",
            {
                "items": [
                    {"scanned_value": "2900000000017", "scanned_at": "2026-05-22T14:30:00Z"},
                    {"scanned_value": "2900000000024", "scanned_at": "2026-05-22T14:30:05Z"},
                ]
            },
            format="json",
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {
            "session_id": sid,
            "accepted": 2,
            "duplicates": 0,
            "rejected": [],
        }
        # le 1er scan a matché l'Item, le 2e non
        scans = list(InventoryScan.objects.filter(session__session_id=sid))
        assert len(scans) == 2
        matched = [s for s in scans if s.item_id is not None]
        assert len(matched) == 1

    def test_isbn_fallback_matches_item(self, client, scanner):
        """BUG-008 : scanned_value = ISBN commercial → item résolu via record.isbn_13."""
        _auth(client)
        rec = BibliographicRecord.objects.create(title="T", isbn_13="9782070408504")
        item = Item.objects.create(record=rec, ean13="2900000000099")
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        resp = client.post(
            f"/api/v1/inventory-sessions/{sid}/items",
            {"items": [{"scanned_value": "9782070408504", "scanned_at": "2026-05-22T10:00:00Z"}]},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["accepted"] == 1
        scan = InventoryScan.objects.get(session__session_id=sid)
        assert scan.item_id == item.id

    def test_isbn_multi_copy_each_counted(self, client, scanner):
        """BUG-008 : 3 exemplaires du même ISBN scannés → 3 pointages distincts."""
        _auth(client)
        rec = BibliographicRecord.objects.create(title="T", isbn_13="9782070408504")
        item_a = Item.objects.create(record=rec, ean13="2900000000099")
        item_b = Item.objects.create(record=rec, ean13="2900000000106")
        item_c = Item.objects.create(record=rec, ean13="2900000000113")
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        payload = {
            "items": [
                {"scanned_value": "9782070408504", "scanned_at": "2026-05-22T10:00:00Z"},
                {"scanned_value": "9782070408504", "scanned_at": "2026-05-22T10:00:01Z"},
                {"scanned_value": "9782070408504", "scanned_at": "2026-05-22T10:00:02Z"},
            ]
        }
        resp = client.post(f"/api/v1/inventory-sessions/{sid}/items", payload, format="json")
        assert resp.status_code == 200
        body = resp.json()
        assert body["accepted"] == 3
        assert body["duplicates"] == 0
        scans = InventoryScan.objects.filter(session__session_id=sid)
        matched_item_ids = {s.item_id for s in scans if s.item_id}
        assert matched_item_ids == {item_a.id, item_b.id, item_c.id}

    def test_duplicates_counted(self, client, scanner):
        _auth(client)
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        item = {"scanned_value": "2900000000017", "scanned_at": "2026-05-22T14:30:00Z"}
        client.post(
            f"/api/v1/inventory-sessions/{sid}/items", {"items": [item]}, format="json"
        )
        resp = client.post(
            f"/api/v1/inventory-sessions/{sid}/items", {"items": [item]}, format="json"
        )
        body = resp.json()
        assert body["accepted"] == 0 and body["duplicates"] == 1

    def test_other_user_session_returns_404(self, client, scanner, other_scanner):
        _auth(client, "scanner")
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        client.credentials()
        _auth(client, "scanner2")
        resp = client.post(
            f"/api/v1/inventory-sessions/{sid}/items",
            {"items": [{"scanned_value": "2900000000017",
                        "scanned_at": "2026-05-22T14:30:00Z"}]},
            format="json",
        )
        assert resp.status_code == 404


@pytest.mark.django_db
class TestInventoryRelocate:
    """FEAT-033 : la réassignation auto fonctionne aussi via l'API
    OfeliaScan (la vue n'utilise pas record_scan mais appelle
    maybe_relocate explicitement)."""

    def test_relocate_via_api_batch(self, client, scanner):
        _auth(client)
        rec = BibliographicRecord.objects.create(title="T")
        a1 = Location.objects.create(code="A1")
        b2 = Location.objects.create(code="B2")
        item = Item.objects.create(record=rec, ean13="2900000000017", location=b2)

        resp = client.post(
            "/api/v1/inventory-sessions",
            {"scope_type": "location", "scope_location_code": "A1"},
            format="json",
        )
        sid = resp.json()["session_id"]

        client.post(
            f"/api/v1/inventory-sessions/{sid}/items",
            {"items": [{"scanned_value": "2900000000017",
                        "scanned_at": "2026-05-22T14:30:00Z"}]},
            format="json",
        )

        item.refresh_from_db()
        session = InventorySession.objects.get(session_id=sid)
        assert item.location_id == a1.pk
        assert session.relocate_count == 1


@pytest.mark.django_db
class TestInventoryClose:
    def test_close_sets_state_and_closed_at(self, client, scanner):
        _auth(client)
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        resp = client.post(f"/api/v1/inventory-sessions/{sid}/close")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "closed"
        assert body["closed_at"] is not None
        session = InventorySession.objects.get(session_id=sid)
        assert session.status == InventoryStatus.CLOSED

    def test_close_then_items_returns_409(self, client, scanner):
        _auth(client)
        sid = client.post("/api/v1/inventory-sessions", {}, format="json").json()[
            "session_id"
        ]
        client.post(f"/api/v1/inventory-sessions/{sid}/close")
        resp = client.post(
            f"/api/v1/inventory-sessions/{sid}/items",
            {"items": [{"scanned_value": "2900000000017",
                        "scanned_at": "2026-05-22T14:30:00Z"}]},
            format="json",
        )
        assert resp.status_code == 409
