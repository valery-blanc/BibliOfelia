"""Tests des endpoints OfeliaScan « scan-sessions » (FEAT-021 / Task #20).

Cible : POST /scan-sessions, /items, /finalize.

Couvre le contrat figé par OfeliaScan (corps enveloppé `{"items":[...]}`,
champs `scanned_value` / `metadata_*` / `item_state`, idempotency par
`local_id`, finalize sync = create-or-add-copies).
"""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.catalog.models import (
    Author,
    BibliographicRecord,
    Item,
    Location,
    ScanSession,
)

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
def librarian(db):
    return User.objects.create_user(
        username="lib", password=PASSWORD, role=Role.LIBRARIAN
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


def _create_session(client, label="ma session"):
    return client.post(
        "/api/v1/scan-sessions", {"label": label}, format="json"
    )


@pytest.mark.django_db
class TestScanSessionCreate:
    def test_requires_auth(self, client):
        assert client.post("/api/v1/scan-sessions").status_code == 401

    def test_create_returns_session_id_state_created_at(self, client, scanner):
        _auth(client)
        resp = _create_session(client)
        assert resp.status_code == 201
        data = resp.json()
        assert {"session_id", "state", "created_at"} <= set(data)
        assert data["state"] == "open"
        assert ScanSession.objects.filter(session_id=data["session_id"]).exists()


@pytest.mark.django_db
class TestScanSessionItems:
    def test_batch_envelope_and_metadata_fields_accepted(self, client, scanner):
        _auth(client)
        sid = _create_session(client).json()["session_id"]
        payload = {
            "items": [
                {
                    "local_id": "L1",
                    "scan_kind": "isbn",
                    "scanned_value": "9782070612758",
                    "metadata_title": "Le Petit Prince",
                    "metadata_authors": ["Antoine de Saint-Exupéry"],
                    "metadata_language": "fr",
                    "metadata_publisher": "Gallimard",
                    "metadata_year": 1943,
                    "location_code": "A1",
                    "item_state": "good",
                    "copy_count": 2,
                    "scanned_at": "2026-05-22T14:30:00Z",
                    "notes": "Don de la famille X",
                },
                {
                    "local_id": "L2",
                    "scan_kind": "manual",
                    "scanned_value": "",
                    "metadata_title": "Notice manuelle",
                    "scanned_at": "2026-05-22T14:31:00Z",
                },
            ]
        }
        resp = client.post(
            f"/api/v1/scan-sessions/{sid}/items", payload, format="json"
        )
        assert resp.status_code == 200, resp.content
        body = resp.json()
        assert body == {
            "session_id": sid,
            "accepted": 2,
            "duplicates": 0,
            "rejected": [],
        }

    def test_local_id_idempotency(self, client, scanner):
        _auth(client)
        sid = _create_session(client).json()["session_id"]
        item = {
            "local_id": "L1",
            "scan_kind": "isbn",
            "scanned_value": "9782070612758",
            "scanned_at": "2026-05-22T14:30:00Z",
        }
        client.post(
            f"/api/v1/scan-sessions/{sid}/items", {"items": [item]}, format="json"
        )
        resp = client.post(
            f"/api/v1/scan-sessions/{sid}/items", {"items": [item]}, format="json"
        )
        body = resp.json()
        assert body["accepted"] == 0 and body["duplicates"] == 1

    def test_items_on_finalized_session_returns_409(self, client, scanner):
        _auth(client)
        sid = _create_session(client).json()["session_id"]
        client.post(f"/api/v1/scan-sessions/{sid}/finalize")
        resp = client.post(
            f"/api/v1/scan-sessions/{sid}/items",
            {"items": [{"local_id": "X", "scan_kind": "manual",
                        "scanned_at": "2026-05-22T14:30:00Z"}]},
            format="json",
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "session_closed"

    def test_contributor_cannot_post_to_other_session(
        self, client, scanner, other_scanner
    ):
        # scanner1 crée
        _auth(client, "scanner")
        sid = _create_session(client).json()["session_id"]
        # scanner2 tente d'envoyer dedans
        client.credentials()
        _auth(client, "scanner2")
        resp = client.post(
            f"/api/v1/scan-sessions/{sid}/items",
            {"items": [{"local_id": "X", "scan_kind": "manual",
                        "scanned_at": "2026-05-22T14:30:00Z"}]},
            format="json",
        )
        assert resp.status_code == 404  # ne fuit pas l'existence

    def test_librarian_sees_all_sessions(self, client, scanner, librarian):
        _auth(client, "scanner")
        sid = _create_session(client).json()["session_id"]
        client.credentials()
        _auth(client, "lib")
        resp = client.post(
            f"/api/v1/scan-sessions/{sid}/items",
            {"items": [{"local_id": "X", "scan_kind": "manual",
                        "scanned_at": "2026-05-22T14:30:00Z"}]},
            format="json",
        )
        assert resp.status_code == 200


@pytest.mark.django_db
class TestScanSessionFinalize:
    def test_finalize_creates_record_when_isbn_unknown(self, client, scanner):
        _auth(client)
        Location.objects.create(code="A1")
        sid = _create_session(client).json()["session_id"]
        client.post(
            f"/api/v1/scan-sessions/{sid}/items",
            {"items": [{
                "local_id": "L1", "scan_kind": "isbn",
                "scanned_value": "9782070612758",
                "metadata_title": "Le Petit Prince",
                "metadata_authors": ["Antoine de Saint-Exupéry"],
                "metadata_publisher": "Gallimard",
                "metadata_year": 1943,
                "location_code": "A1",
                "item_state": "good",
                "copy_count": 2,
                "scanned_at": "2026-05-22T14:30:00Z",
            }]},
            format="json",
        )
        resp = client.post(f"/api/v1/scan-sessions/{sid}/finalize")
        assert resp.status_code == 200
        body = resp.json()
        assert body["state"] == "finalized"
        assert body["summary"]["records_created"] == 1
        assert body["summary"]["records_matched"] == 0
        assert body["summary"]["copies_added"] == 2

        rec = BibliographicRecord.objects.get(isbn_13="9782070612758")
        assert rec.title == "Le Petit Prince"
        assert rec.publisher == "Gallimard"
        assert rec.publication_year == 1943
        assert rec.authors.filter(full_name="Antoine de Saint-Exupéry").exists()
        assert Item.objects.filter(record=rec).count() == 2
        assert Item.objects.filter(record=rec, location__code="A1").count() == 2

    def test_finalize_matches_existing_isbn_and_adds_copies(self, client, scanner):
        _auth(client)
        rec = BibliographicRecord.objects.create(
            title="Existant", isbn_13="9782070612758"
        )
        sid = _create_session(client).json()["session_id"]
        client.post(
            f"/api/v1/scan-sessions/{sid}/items",
            {"items": [{
                "local_id": "L1", "scan_kind": "ean13",
                "scanned_value": "9782070612758",
                "copy_count": 3,
                "scanned_at": "2026-05-22T14:30:00Z",
            }]},
            format="json",
        )
        body = client.post(f"/api/v1/scan-sessions/{sid}/finalize").json()
        assert body["summary"]["records_matched"] == 1
        assert body["summary"]["records_created"] == 0
        assert body["summary"]["copies_added"] == 3
        assert Item.objects.filter(record=rec).count() == 3

    def test_finalize_twice_returns_409(self, client, scanner):
        _auth(client)
        sid = _create_session(client).json()["session_id"]
        client.post(f"/api/v1/scan-sessions/{sid}/finalize")
        resp = client.post(f"/api/v1/scan-sessions/{sid}/finalize")
        assert resp.status_code == 409
