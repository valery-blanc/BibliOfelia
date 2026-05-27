"""Tests FEAT-041 — affectation en masse catégorie / emplacement. Sprint 13."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    Item,
    Location,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="bib", password="x", role=Role.LIBRARIAN
    )


@pytest.fixture
def readonly_user(django_user_model):
    return django_user_model.objects.create_user(
        username="ro", password="x", role=Role.READONLY
    )


@pytest.fixture
def cat_a(db):
    return Category.objects.create(code="A", name="A")


@pytest.fixture
def cat_b(db):
    return Category.objects.create(code="B", name="B")


@pytest.fixture
def loc_a(db):
    return Location.objects.create(code="A1")


@pytest.fixture
def loc_b(db):
    return Location.objects.create(code="B1")


@pytest.fixture
def records(cat_a):
    r1 = BibliographicRecord.objects.create(title="R1", category=cat_a)
    r2 = BibliographicRecord.objects.create(title="R2")
    Item.objects.create(record=r1)
    Item.objects.create(record=r1)
    Item.objects.create(record=r2)
    return [r1, r2]


# ─── permissions ───────────────────────────────────────────────────────


def test_readonly_cannot_assign_category(client, readonly_user, records):
    client.force_login(readonly_user)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-category/", {"ids": ids}
    )
    assert resp.status_code in (302, 403)


def test_librarian_sees_confirm(client, librarian, records, cat_b):
    client.force_login(librarian)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-category/", {"ids": ids}
    )
    assert resp.status_code == 200
    assert b"R1" in resp.content


# ─── assign category ───────────────────────────────────────────────────


def test_assign_category_updates_records(client, librarian, records, cat_b):
    client.force_login(librarian)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-category/apply/",
        {"ids": ids, "category": str(cat_b.pk)},
    )
    assert resp.status_code == 302
    for r in records:
        r.refresh_from_db()
        assert r.category_id == cat_b.pk


def test_assign_category_empty_clears_field(client, librarian, records):
    client.force_login(librarian)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-category/apply/",
        {"ids": ids, "category": ""},
    )
    assert resp.status_code == 302
    for r in records:
        r.refresh_from_db()
        assert r.category_id is None


# ─── assign location ───────────────────────────────────────────────────


def test_assign_location_updates_all_items(client, librarian, records, loc_b):
    client.force_login(librarian)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-location/apply/",
        {"ids": ids, "location": str(loc_b.pk)},
    )
    assert resp.status_code == 302
    items = Item.objects.filter(record_id__in=[r.pk for r in records])
    assert items.count() == 3
    assert all(it.location_id == loc_b.pk for it in items)


def test_assign_location_empty_clears(client, librarian, records, loc_a):
    Item.objects.filter(record_id=records[0].pk).update(location=loc_a)
    client.force_login(librarian)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-location/apply/",
        {"ids": ids, "location": ""},
    )
    assert resp.status_code == 302
    assert (
        Item.objects.filter(record_id__in=[r.pk for r in records], location__isnull=False).count()
        == 0
    )


def test_assign_location_confirm_counts_items(client, librarian, records, loc_b):
    client.force_login(librarian)
    ids = [str(r.pk) for r in records]
    resp = client.post(
        "/fr/catalog/bulk-assign-location/", {"ids": ids}
    )
    assert resp.status_code == 200
    assert b"3" in resp.content  # 3 exemplaires
