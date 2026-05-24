"""Tests endpoint `GET /api/locations` (FEAT-032).

Liste lecture-seule pour le picker OfeliaScan.
"""
from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.catalog.models import Location

PASSWORD = "ofelia-test-pwd"


@pytest.fixture
def scanner(db):
    return User.objects.create_user(
        username="scanner", password=PASSWORD, role=Role.CONTRIBUTOR_API
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
class TestLocationListAPI:
    def test_requires_auth(self, client):
        assert client.get("/api/v1/locations").status_code == 401

    def test_empty_list(self, client, scanner):
        _auth(client)
        resp = client.get("/api/v1/locations")
        assert resp.status_code == 200
        assert resp.json() == {"locations": []}

    def test_returns_sorted_by_code(self, client, scanner):
        Location.objects.create(code="Z1")
        Location.objects.create(code="A1", description="Salle adulte")
        Location.objects.create(code="JEU")
        _auth(client)
        resp = client.get("/api/v1/locations")
        assert resp.status_code == 200
        codes = [loc["code"] for loc in resp.json()["locations"]]
        assert codes == ["A1", "JEU", "Z1"]

    def test_returns_parent_code(self, client, scanner):
        jeu = Location.objects.create(code="JEU")
        Location.objects.create(code="BD", parent=jeu, description="BD jeunesse")
        _auth(client)
        resp = client.get("/api/v1/locations")
        assert resp.status_code == 200
        data = {loc["code"]: loc for loc in resp.json()["locations"]}
        assert data["BD"]["parent_code"] == "JEU"
        assert data["JEU"]["parent_code"] is None
        assert data["BD"]["description"] == "BD jeunesse"

    def test_payload_shape(self, client, scanner):
        Location.objects.create(code="A1", description="Salle adulte")
        _auth(client)
        resp = client.get("/api/v1/locations")
        loc = resp.json()["locations"][0]
        assert set(loc.keys()) == {"code", "description", "parent_code"}
