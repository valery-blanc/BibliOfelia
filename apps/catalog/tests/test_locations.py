"""Tests vues Location (FEAT-032).

CRUD librarian + permissions + comportement SET_NULL à la suppression.
"""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item, Location

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def readonly(django_user_model):
    return django_user_model.objects.create_user(
        username="lecteur", password="motdepasse123", role=Role.READONLY
    )


@pytest.fixture
def location():
    return Location.objects.create(code="A1", description="Salle adulte")


def test_list_visible_to_librarian(client, librarian, location):
    client.force_login(librarian)
    resp = client.get("/fr/catalog/locations/")
    assert resp.status_code == 200
    assert b"A1" in resp.content


def test_list_forbidden_to_readonly(client, readonly):
    client.force_login(readonly)
    resp = client.get("/fr/catalog/locations/")
    assert resp.status_code == 403


def test_list_redirect_for_anonymous(client):
    resp = client.get("/fr/catalog/locations/")
    assert resp.status_code in (302, 301)


def test_create_location(client, librarian):
    client.force_login(librarian)
    resp = client.post(
        "/fr/catalog/locations/new/",
        {"code": "B2", "description": "Réserve", "parent": ""},
    )
    assert resp.status_code == 302
    assert Location.objects.filter(code="B2").exists()


def test_create_duplicate_code_same_parent_rejected(client, librarian, location):
    client.force_login(librarian)
    resp = client.post(
        "/fr/catalog/locations/new/",
        {"code": "A1", "description": "Doublon", "parent": ""},
    )
    assert resp.status_code == 200
    # le form a une erreur, donc pas de création
    assert Location.objects.filter(code="A1").count() == 1


def test_create_duplicate_code_different_parent_allowed(client, librarian, location):
    """A1 racine + A1 enfant de JEU → OK grâce à la contrainte (code, parent) unique."""
    jeu = Location.objects.create(code="JEU")
    client.force_login(librarian)
    resp = client.post(
        "/fr/catalog/locations/new/",
        {"code": "A1", "description": "A1 jeunesse", "parent": jeu.pk},
    )
    assert resp.status_code == 302
    assert Location.objects.filter(code="A1").count() == 2


def test_edit_location(client, librarian, location):
    client.force_login(librarian)
    resp = client.post(
        f"/fr/catalog/locations/{location.pk}/edit/",
        {"code": "A1", "description": "Salle adulte rayon 1", "parent": ""},
    )
    assert resp.status_code == 302
    location.refresh_from_db()
    assert location.description == "Salle adulte rayon 1"


def test_edit_parent_self_rejected(client, librarian, location):
    """On ne peut pas proposer self comme parent (exclu du queryset)."""
    client.force_login(librarian)
    resp = client.post(
        f"/fr/catalog/locations/{location.pk}/edit/",
        {"code": "A1", "description": "", "parent": location.pk},
    )
    # le queryset exclut self, donc le form rejette la valeur
    assert resp.status_code == 200
    location.refresh_from_db()
    assert location.parent is None


def test_delete_location_releases_items(client, librarian, location):
    """Suppression : SET_NULL sur Item.location → l'exemplaire perd sa loc."""
    rec = BibliographicRecord.objects.create(title="Fondation")
    item = Item.objects.create(record=rec, location=location)
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/locations/{location.pk}/delete/")
    assert resp.status_code == 302
    assert not Location.objects.filter(pk=location.pk).exists()
    item.refresh_from_db()
    assert item.location is None


def test_delete_confirm_shows_items_count(client, librarian, location):
    rec = BibliographicRecord.objects.create(title="Fondation")
    Item.objects.create(record=rec, location=location)
    Item.objects.create(record=rec, location=location)
    client.force_login(librarian)
    resp = client.get(f"/fr/catalog/locations/{location.pk}/delete/")
    assert resp.status_code == 200
    assert b"2" in resp.content  # le compteur d'exemplaires
