"""FEAT-069 — affectation en masse directement depuis la page catalogue.

Remplace les tests FEAT-041 : les pages de confirmation d'affectation ont
disparu, la barre d'action poste directement. La sentinelle `keep` distingue
« ne pas modifier » de « vider ».
"""
from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import Role
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    Item,
    Location,
    Provenance,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="bib", password="x", role=Role.LIBRARIAN
    )
    client.force_login(user)
    return user


@pytest.fixture
def readonly_user(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="ro", password="x", role=Role.READONLY
    )
    client.force_login(user)
    return user


@pytest.fixture
def cat_a():
    return Category.objects.create(code="A", name="A")


@pytest.fixture
def cat_b():
    return Category.objects.create(code="B", name="B")


@pytest.fixture
def loc_a():
    return Location.objects.create(code="LA")


@pytest.fixture
def loc_b():
    return Location.objects.create(code="LB")


@pytest.fixture
def records(cat_a, loc_a):
    """2 notices en catégorie A, chacune avec 2 exemplaires en LA."""
    out = []
    for title in ("Fondation", "Dune"):
        record = BibliographicRecord.objects.create(title=title, category=cat_a)
        for _ in range(2):
            Item.objects.create(record=record, location=loc_a)
        out.append(record)
    return out


def _ids(records):
    return [r.pk for r in records]


# ── Notices : catégorie + emplacement ──────────────────────────────────────


def test_readonly_cannot_assign(client, readonly_user, records, cat_b):
    resp = client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": _ids(records), "category": cat_b.pk, "location": "keep"},
    )
    assert resp.status_code in (302, 403)
    records[0].refresh_from_db()
    assert records[0].category.code == "A"


def test_assign_category_only(client, librarian, records, cat_b, loc_a):
    resp = client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": _ids(records), "category": cat_b.pk, "location": "keep"},
    )
    assert resp.status_code == 302
    assert BibliographicRecord.objects.filter(category=cat_b).count() == 2
    # L'emplacement laissé sur « ne pas modifier » n'a pas bougé.
    assert Item.objects.filter(location=loc_a).count() == 4


def test_assign_location_touches_every_copy(client, librarian, records, loc_b):
    client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": _ids(records), "category": "keep", "location": loc_b.pk},
    )
    assert Item.objects.filter(location=loc_b).count() == 4


def test_assign_both_at_once(client, librarian, records, cat_b, loc_b):
    client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": _ids(records), "category": cat_b.pk, "location": loc_b.pk},
    )
    assert BibliographicRecord.objects.filter(category=cat_b).count() == 2
    assert Item.objects.filter(location=loc_b).count() == 4


def test_empty_value_clears_the_field(client, librarian, records):
    """Chaîne vide = vider, à distinguer de « ne pas modifier »."""
    client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": _ids(records), "category": "", "location": ""},
    )
    assert BibliographicRecord.objects.filter(category__isnull=True).count() == 2
    assert Item.objects.filter(location__isnull=True).count() == 4


def test_keep_on_everything_changes_nothing(client, librarian, records, cat_a, loc_a):
    resp = client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": _ids(records), "category": "keep", "location": "keep"},
    )
    assert resp.status_code == 302
    assert BibliographicRecord.objects.filter(category=cat_a).count() == 2
    assert Item.objects.filter(location=loc_a).count() == 4


def test_missing_field_defaults_to_keep(client, librarian, records, cat_a):
    """Un menu absent du POST ne doit jamais vider le champ."""
    client.post(reverse("catalog:record_bulk_assign"), {"ids": _ids(records)})
    assert BibliographicRecord.objects.filter(category=cat_a).count() == 2


def test_only_selected_records_change(client, librarian, records, cat_b):
    client.post(
        reverse("catalog:record_bulk_assign"),
        {"ids": [records[0].pk], "category": cat_b.pk, "location": "keep"},
    )
    records[0].refresh_from_db()
    records[1].refresh_from_db()
    assert records[0].category == cat_b
    assert records[1].category.code == "A"


def test_redirect_keeps_the_active_filters(client, librarian, records, cat_b):
    resp = client.post(
        reverse("catalog:record_bulk_assign"),
        {
            "ids": _ids(records),
            "category": cat_b.pk,
            "location": "keep",
            "back_qs": "q=dune&mode=items",
        },
    )
    assert resp.url.endswith("?q=dune&mode=items")


# ── Exemplaires : provenance ───────────────────────────────────────────────


def test_assign_provenance_to_items(client, librarian, records):
    prov = Provenance.objects.create(code="BM-GE", label="Prêt Genève")
    items = list(Item.objects.all()[:2])
    client.post(
        reverse("catalog:item_bulk_assign"),
        {"ids": [i.pk for i in items], "provenance": prov.pk},
    )
    assert Item.objects.filter(provenance=prov).count() == 2


def test_clear_provenance(client, librarian, records):
    prov = Provenance.objects.create(code="BM-GE")
    Item.objects.update(provenance=prov)
    client.post(
        reverse("catalog:item_bulk_assign"),
        {"ids": list(Item.objects.values_list("pk", flat=True)), "provenance": ""},
    )
    assert Item.objects.filter(provenance__isnull=True).count() == 4


def test_keep_provenance_changes_nothing(client, librarian, records):
    prov = Provenance.objects.create(code="BM-GE")
    Item.objects.update(provenance=prov)
    client.post(
        reverse("catalog:item_bulk_assign"),
        {"ids": list(Item.objects.values_list("pk", flat=True)), "provenance": "keep"},
    )
    assert Item.objects.filter(provenance=prov).count() == 4


# ── L'écran ────────────────────────────────────────────────────────────────


def test_catalog_page_carries_the_dropdowns(client, librarian, records, cat_b, loc_b):
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert reverse("catalog:record_bulk_assign") in body
    assert 'name="category"' in body and 'name="location"' in body
    assert "Ne pas modifier" in body


def test_items_mode_carries_the_provenance_dropdown(client, librarian, records):
    Provenance.objects.create(code="BM-GE")
    body = client.get(
        reverse("catalog:record_list"), {"mode": "items"}
    ).content.decode()
    assert reverse("catalog:item_bulk_assign") in body
    assert 'name="provenance"' in body


def test_the_confirmation_pages_are_gone(client, librarian):
    """Les affectations n'ont plus de page intermédiaire (FEAT-069)."""
    from django.urls import NoReverseMatch

    for name in (
        "record_bulk_assign_category_confirm",
        "record_bulk_assign_location_confirm",
        "item_bulk_assign_provenance_confirm",
    ):
        with pytest.raises(NoReverseMatch):
            reverse(f"catalog:{name}")


def test_bulk_delete_keeps_its_confirmation(client, django_user_model, records):
    """Une suppression, elle, mérite qu'on relise la liste."""
    client.force_login(
        django_user_model.objects.create_user(
            username="boss", password="x", role=Role.SUPERADMIN
        )
    )
    resp = client.post(
        reverse("catalog:item_bulk_delete_confirm"),
        {"ids": list(Item.objects.values_list("pk", flat=True))[:1]},
    )
    assert resp.status_code == 200
