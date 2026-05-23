"""Tests du handoff single-scan (FEAT-023).

POST /scan-handoff (création par librarian via session),
GET /scan-handoff/{token} (polling navigateur),
POST /scan-handoff/{token} (callback OfeliaScan via JWT).
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.api.models import ScanHandoff, ScanHandoffState

PASSWORD = "ofelia-test-pwd"


@pytest.fixture
def librarian(db):
    return User.objects.create_user(
        username="lib", password=PASSWORD, role=Role.LIBRARIAN
    )


@pytest.fixture
def other_librarian(db):
    return User.objects.create_user(
        username="lib2", password=PASSWORD, role=Role.LIBRARIAN
    )


@pytest.fixture
def superadmin(db):
    return User.objects.create_user(
        username="admin", password=PASSWORD, role=Role.SUPERADMIN
    )


@pytest.fixture
def scanner(db):
    return User.objects.create_user(
        username="scanner", password=PASSWORD, role=Role.CONTRIBUTOR_API
    )


@pytest.fixture
def client():
    return APIClient()


def _jwt(client, username):
    resp = client.post(
        "/api/v1/auth/login",
        {"username": username, "password": PASSWORD},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access_token']}")


@pytest.mark.django_db
class TestCreate:
    def test_anonymous_gets_401(self, client):
        assert client.post("/api/v1/scan-handoff").status_code == 401

    def test_contributor_api_gets_403(self, client, scanner):
        _jwt(client, "scanner")
        resp = client.post("/api/v1/scan-handoff", {}, format="json")
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "forbidden"

    def test_librarian_creates_handoff_via_session(self, client, librarian):
        client.force_authenticate(user=librarian)
        resp = client.post(
            "/api/v1/scan-handoff", {"target_kind": "book"}, format="json"
        )
        assert resp.status_code == 201
        data = resp.json()
        assert {
            "token", "state", "deep_link", "android_intent_url",
            "expires_at", "target_kind",
        } <= set(data)
        assert data["state"] == "pending"
        assert data["target_kind"] == "book"
        assert data["deep_link"].startswith("ofeliascan://scan-one?token=")
        assert f"token={data['token']}" in data["deep_link"]
        assert "kind=book" in data["deep_link"]
        assert ScanHandoff.objects.filter(token=data["token"]).exists()

    def test_android_intent_url_includes_package_and_scheme(self, client, librarian):
        client.force_authenticate(user=librarian)
        resp = client.post(
            "/api/v1/scan-handoff", {"target_kind": "card"}, format="json"
        )
        intent = resp.json()["android_intent_url"]
        assert intent.startswith("intent://scan-one?token=")
        assert "kind=card" in intent
        assert "#Intent;" in intent
        assert "scheme=ofeliascan" in intent
        assert "package=org.zitoon.ofeliascan" in intent
        assert intent.endswith(";end")

    def test_default_target_kind_is_auto(self, client, librarian):
        client.force_authenticate(user=librarian)
        resp = client.post("/api/v1/scan-handoff", {}, format="json")
        assert resp.status_code == 201
        data = resp.json()
        assert data["target_kind"] == "auto"
        assert "kind=auto" in data["deep_link"]
        assert "kind=auto" in data["android_intent_url"]


@pytest.mark.django_db
class TestGetStatus:
    def _make(self, user):
        return ScanHandoff.objects.create(
            created_by=user, target_kind="auto"
        )

    def test_creator_can_poll(self, client, librarian):
        h = self._make(librarian)
        client.force_authenticate(user=librarian)
        resp = client.get(f"/api/v1/scan-handoff/{h.token}")
        assert resp.status_code == 200
        assert resp.json()["state"] == "pending"

    def test_other_librarian_gets_404(self, client, librarian, other_librarian):
        h = self._make(librarian)
        client.force_authenticate(user=other_librarian)
        resp = client.get(f"/api/v1/scan-handoff/{h.token}")
        assert resp.status_code == 404

    def test_superadmin_can_poll_any(self, client, librarian, superadmin):
        h = self._make(librarian)
        client.force_authenticate(user=superadmin)
        resp = client.get(f"/api/v1/scan-handoff/{h.token}")
        assert resp.status_code == 200

    def test_anonymous_gets_401(self, client, librarian):
        h = self._make(librarian)
        resp = client.get(f"/api/v1/scan-handoff/{h.token}")
        assert resp.status_code == 401

    def test_unknown_token_returns_404(self, client, librarian):
        client.force_authenticate(user=librarian)
        resp = client.get("/api/v1/scan-handoff/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_expired_handoff_reports_expired_state(self, client, librarian):
        h = self._make(librarian)
        ScanHandoff.objects.filter(pk=h.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        client.force_authenticate(user=librarian)
        resp = client.get(f"/api/v1/scan-handoff/{h.token}")
        assert resp.status_code == 200
        assert resp.json()["state"] == "expired"


@pytest.mark.django_db
class TestSubmit:
    def _make(self, user):
        return ScanHandoff.objects.create(
            created_by=user, target_kind="auto"
        )

    def test_jwt_user_can_submit_value(self, client, librarian, scanner):
        h = self._make(librarian)
        _jwt(client, "scanner")
        resp = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": "9782070612758", "kind": "isbn"},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["state"] == "completed"
        assert data["value"] == "9782070612758"
        assert data["value_kind"] == "isbn"
        h.refresh_from_db()
        assert h.state == ScanHandoffState.COMPLETED
        assert h.completed_by_id == scanner.id

    def test_submit_normalizes_code(self, client, librarian, scanner):
        h = self._make(librarian)
        _jwt(client, "scanner")
        resp = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": " 978-2-07-061275-8 ", "kind": "isbn"},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["value"] == "9782070612758"

    def test_cancelled_submission_marks_cancelled(self, client, librarian, scanner):
        h = self._make(librarian)
        _jwt(client, "scanner")
        resp = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"cancelled": True},
            format="json",
        )
        assert resp.status_code == 200
        assert resp.json()["state"] == "cancelled"

    def test_double_submit_returns_409(self, client, librarian, scanner):
        h = self._make(librarian)
        _jwt(client, "scanner")
        first = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": "290000000001", "kind": "item"},
            format="json",
        )
        assert first.status_code == 200
        second = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": "X", "kind": "manual"},
            format="json",
        )
        assert second.status_code == 409
        assert second.json()["error"]["code"] == "already_completed"

    def test_submit_after_ttl_returns_410(self, client, librarian, scanner):
        h = self._make(librarian)
        ScanHandoff.objects.filter(pk=h.pk).update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        _jwt(client, "scanner")
        resp = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": "9782070612758", "kind": "isbn"},
            format="json",
        )
        assert resp.status_code == 410
        assert resp.json()["error"]["code"] == "expired"

    def test_submit_without_value_or_cancel_returns_400(
        self, client, librarian, scanner
    ):
        h = self._make(librarian)
        _jwt(client, "scanner")
        resp = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": "", "kind": "manual"},
            format="json",
        )
        assert resp.status_code == 400

    def test_anonymous_cannot_submit(self, client, librarian):
        h = self._make(librarian)
        resp = client.post(
            f"/api/v1/scan-handoff/{h.token}",
            {"value": "9782070612758", "kind": "isbn"},
            format="json",
        )
        assert resp.status_code == 401


@pytest.mark.django_db
class TestRoundTrip:
    def test_browser_creates_scanner_submits_browser_polls(
        self, client, librarian, scanner
    ):
        # 1. Le navigateur (session librarian) crée le handoff
        client.force_authenticate(user=librarian)
        create = client.post(
            "/api/v1/scan-handoff", {"target_kind": "book"}, format="json"
        ).json()
        token = create["token"]

        # 2. Premier poll : pending
        poll = client.get(f"/api/v1/scan-handoff/{token}")
        assert poll.json()["state"] == "pending"

        # 3. OfeliaScan (JWT contributor_api) soumet
        scanner_client = APIClient()
        _jwt(scanner_client, "scanner")
        submit = scanner_client.post(
            f"/api/v1/scan-handoff/{token}",
            {"value": "9782070612758", "kind": "isbn"},
            format="json",
        )
        assert submit.status_code == 200

        # 4. Second poll : completed avec la valeur
        poll2 = client.get(f"/api/v1/scan-handoff/{token}").json()
        assert poll2["state"] == "completed"
        assert poll2["value"] == "9782070612758"
        assert poll2["value_kind"] == "isbn"
