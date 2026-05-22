"""Tests de l'API OfeliaScan. SPEC §6.10 / SPEC-CORR-001.

Vérifie que le contrat figé est respecté : noms de champs OAuth 2.0, rotation
des refresh tokens, format d'erreur uniforme, endpoints d'appairage et de
lookup ISBN.
"""
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role, User
from apps.catalog.models import Author, BibliographicRecord

PASSWORD = "ofelia-test-pwd"
OAUTH_FIELDS = {"access_token", "refresh_token", "token_type", "expires_in"}


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="scanner", password=PASSWORD, role=Role.CONTRIBUTOR_API
    )


@pytest.fixture
def client():
    return APIClient()


def _login(client, username="scanner", password=PASSWORD):
    return client.post(
        "/api/v1/auth/login",
        {"username": username, "password": password},
        format="json",
    )


def _authenticate(client):
    token = _login(client).json()["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")


@pytest.mark.django_db
class TestAuthLogin:
    def test_login_returns_oauth_fields(self, client, user):
        resp = _login(client)
        assert resp.status_code == 200
        data = resp.json()
        assert OAUTH_FIELDS <= set(data)
        assert data["token_type"] == "Bearer"
        assert isinstance(data["expires_in"], int) and data["expires_in"] > 0

    def test_login_bad_credentials_returns_401_error_format(self, client, user):
        resp = client.post(
            "/api/v1/auth/login",
            {"username": "scanner", "password": "wrong"},
            format="json",
        )
        assert resp.status_code == 401
        assert set(resp.json()["error"]) == {"code", "message", "details"}


@pytest.mark.django_db
class TestAuthRefresh:
    def test_refresh_returns_new_rotated_tokens(self, client, user):
        login = _login(client).json()
        resp = client.post(
            "/api/v1/auth/refresh",
            {"refresh_token": login["refresh_token"]},
            format="json",
        )
        assert resp.status_code == 200
        data = resp.json()
        assert OAUTH_FIELDS <= set(data)
        assert data["refresh_token"] != login["refresh_token"]

    def test_old_refresh_token_blacklisted_after_rotation(self, client, user):
        login = _login(client).json()
        client.post(
            "/api/v1/auth/refresh",
            {"refresh_token": login["refresh_token"]},
            format="json",
        )
        resp = client.post(
            "/api/v1/auth/refresh",
            {"refresh_token": login["refresh_token"]},
            format="json",
        )
        assert resp.status_code == 401

    def test_refresh_invalid_token_returns_401(self, client):
        resp = client.post(
            "/api/v1/auth/refresh", {"refresh_token": "not-a-jwt"}, format="json"
        )
        assert resp.status_code == 401


@pytest.mark.django_db
class TestAuthLogout:
    def test_logout_blacklists_refresh_tokens(self, client, user):
        login = _login(client).json()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {login['access_token']}")
        resp = client.post("/api/v1/auth/logout")
        assert resp.status_code == 204

        client.credentials()
        refresh = client.post(
            "/api/v1/auth/refresh",
            {"refresh_token": login["refresh_token"]},
            format="json",
        )
        assert refresh.status_code == 401

    def test_logout_requires_auth(self, client):
        assert client.post("/api/v1/auth/logout").status_code == 401


@pytest.mark.django_db
class TestPairingInfo:
    def test_pairing_info_no_auth_required(self, client):
        resp = client.get("/api/v1/pairing/info")
        assert resp.status_code == 200
        assert {"box_name", "library_name", "version", "base_url"} <= set(resp.json())

    def test_base_url_is_absolute_with_trailing_slash(self, client):
        base_url = client.get("/api/v1/pairing/info").json()["base_url"]
        assert base_url.startswith("http")
        assert base_url.endswith("/")

    def test_base_url_override_from_setting(self, client, settings):
        settings.API_BASE_URL = "http://192.168.0.147/bibliofelia/api/v1/"
        base_url = client.get("/api/v1/pairing/info").json()["base_url"]
        assert base_url == "http://192.168.0.147/bibliofelia/api/v1/"


@pytest.mark.django_db
class TestHealth:
    def test_health_requires_auth(self, client):
        assert client.get("/api/v1/health").status_code == 401

    def test_health_returns_status_ok(self, client, user):
        _authenticate(client)
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.django_db
class TestIsbnLookup:
    def test_isbn_requires_auth(self, client):
        assert client.get("/api/v1/isbn/9782070360024").status_code == 401

    def test_isbn_found_in_local_cache(self, client, user):
        record = BibliographicRecord.objects.create(
            title="L'Étranger",
            isbn_13="9782070360024",
            publisher="Gallimard",
            publication_year=1972,
            language="fr",
        )
        record.authors.add(Author.objects.create(full_name="Albert Camus"))
        _authenticate(client)
        resp = client.get("/api/v1/isbn/9782070360024")
        assert resp.status_code == 200
        data = resp.json()
        assert data["isbn"] == "9782070360024"
        assert data["source"] == "cache"
        assert data["cached"] is True
        assert data["publication_year"] == 1972
        assert "Albert Camus" in data["authors"]

    def test_isbn_not_found_returns_404_error_format(self, client, user, monkeypatch):
        monkeypatch.setattr("apps.api.views.lookup_isbn", lambda isbn: None)
        _authenticate(client)
        resp = client.get("/api/v1/isbn/9782070612758")
        assert resp.status_code == 404
        assert set(resp.json()["error"]) == {"code", "message", "details"}

    def test_isbn_openlibrary_fallback(self, client, user, monkeypatch):
        monkeypatch.setattr(
            "apps.api.views.lookup_isbn",
            lambda isbn: {
                "title": "Le Petit Prince",
                "authors_text": "Antoine de Saint-Exupéry",
                "publisher": "Gallimard",
                "publication_year": "1943",
            },
        )
        _authenticate(client)
        resp = client.get("/api/v1/isbn/9782070612758")
        assert resp.status_code == 200
        data = resp.json()
        assert data["source"] == "openlibrary"
        assert data["cached"] is False
        assert data["publication_year"] == 1943
        assert data["authors"] == ["Antoine de Saint-Exupéry"]
