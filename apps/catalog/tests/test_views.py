"""Tests vues catalogue. SPEC §6.1 (Task #6)."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item, ItemStatus, Location

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
def record():
    return BibliographicRecord.objects.create(title="Fondation")


def test_record_list_visible_to_readonly(client, readonly, record):
    client.force_login(readonly)
    resp = client.get("/fr/catalog/")
    assert resp.status_code == 200
    assert b"Fondation" in resp.content


def test_record_create_forbidden_for_readonly(client, readonly):
    client.force_login(readonly)
    resp = client.get("/fr/catalog/new/")
    assert resp.status_code == 403


def test_record_create_post(client, librarian):
    client.force_login(librarian)
    resp = client.post(
        "/fr/catalog/new/",
        {"title": "Le Meilleur des mondes", "language": "fr", "document_type": "book",
         "authors_text": "Aldous Huxley"},
    )
    assert resp.status_code == 302
    record = BibliographicRecord.objects.get(title="Le Meilleur des mondes")
    assert record.created_by_id == librarian.pk
    assert record.authors.count() == 1


def test_item_bulk_create(client, librarian, record):
    client.force_login(librarian)
    resp = client.post(
        f"/fr/catalog/{record.pk}/items/new/",
        {"copies": 4, "state": "good", "acquisition_date": "2026-05-21",
         "acquisition_source": "donation"},
    )
    assert resp.status_code == 302
    assert record.items.count() == 4
    eans = {it.ean13 for it in record.items.all()}
    assert len(eans) == 4  # chaque exemplaire a un EAN13 distinct


def test_item_discard_sets_status(client, librarian, record):
    item = Item.objects.create(record=record, location=Location.objects.create(code="A1"))
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/items/{item.pk}/discard/")
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.status == ItemStatus.DISCARDED


def test_item_discard_blocked_when_on_loan(client, librarian, record):
    item = Item.objects.create(record=record, status=ItemStatus.ON_LOAN)
    client.force_login(librarian)
    client.post(f"/fr/catalog/items/{item.pk}/discard/")
    item.refresh_from_db()
    assert item.status == ItemStatus.ON_LOAN


def test_record_delete_blocked_with_active_items(client, librarian, record):
    Item.objects.create(record=record, status=ItemStatus.AVAILABLE)
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/{record.pk}/delete/")
    assert resp.status_code == 302
    assert BibliographicRecord.objects.filter(pk=record.pk).exists()


def test_record_delete_succeeds_without_items(client, librarian, record):
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/{record.pk}/delete/")
    assert resp.status_code == 302
    assert not BibliographicRecord.objects.filter(pk=record.pk).exists()
