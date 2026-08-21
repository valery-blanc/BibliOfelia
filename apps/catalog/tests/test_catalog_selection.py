"""FEAT-073 — boutons de recherche, sélection étendue, provenance lisible."""
from __future__ import annotations

import pytest
from django.urls import reverse

from apps.accounts.models import Role, User
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
def superadmin(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="boss", password="x", role=Role.SUPERADMIN
    )
    client.force_login(user)
    return user


@pytest.fixture
def borrowed():
    return Provenance.objects.create(code="BM-GE", label="Prêt Bibliothèque de Genève")


@pytest.fixture
def many_records(borrowed):
    """40 notices d'un exemplaire chacune : la pagination (25) coupe donc."""
    out = []
    for i in range(40):
        record = BibliographicRecord.objects.create(title=f"Titre {i:02d}")
        Item.objects.create(record=record, provenance=borrowed)
        out.append(record)
    return out


# ── Deux boutons au lieu d'une case ────────────────────────────────────────


def test_the_checkbox_is_gone(client, librarian):
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert "Chercher les exemplaires" not in body


def test_both_search_buttons_are_offered(client, librarian):
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert "Rechercher des notices" in body
    assert "Rechercher des exemplaires" in body
    assert 'name="mode" value="items"' in body
    assert 'name="mode" value="records"' in body


def test_default_view_is_records_without_any_filter(client, librarian, many_records):
    resp = client.get(reverse("catalog:record_list"))
    assert resp.context["items_mode"] is False
    assert resp.context["total"] == 40


def test_the_items_button_switches_mode(client, librarian, many_records):
    resp = client.get(reverse("catalog:record_list"), {"mode": "items"})
    assert resp.context["items_mode"] is True


def test_the_records_button_comes_back(client, librarian, many_records):
    resp = client.get(reverse("catalog:record_list"), {"mode": "records"})
    assert resp.context["items_mode"] is False


def test_filters_survive_the_mode_switch(client, librarian, borrowed):
    cat = Category.objects.create(code="AD FIC", name="Adultes Fiction")
    kept = BibliographicRecord.objects.create(title="Fondation", category=cat)
    Item.objects.create(record=kept, provenance=borrowed)
    other = BibliographicRecord.objects.create(title="Dune")
    Item.objects.create(record=other)

    resp = client.get(
        reverse("catalog:record_list"), {"mode": "items", "category": cat.pk}
    )
    assert [it.record_id for it in resp.context["page_obj"]] == [kept.pk]


# ── Les deux cases « tout sélectionner » ───────────────────────────────────


def test_both_select_all_checkboxes_are_offered(client, librarian, many_records):
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert "résultats visibles" in body
    assert "résultats de la recherche" in body
    assert "toutes les pages" in body


def test_the_all_results_checkbox_is_hidden_on_a_single_page(client, librarian):
    """Sur une seule page, la seconde case ferait doublon avec la première."""
    BibliographicRecord.objects.create(title="Fondation")
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert "résultat visible" in body   # singulier : une seule ligne
    assert "toutes les pages" not in body


def test_select_all_assigns_beyond_the_first_page(client, librarian, many_records):
    """Le cas qui motive la feature : 40 notices, 25 par page."""
    cat = Category.objects.create(code="AD FIC", name="Adultes Fiction")
    resp = client.post(
        reverse("catalog:record_bulk_assign"),
        {"select_all": "1", "back_qs": "", "category": cat.pk, "location": "keep"},
    )
    assert resp.status_code == 302
    assert BibliographicRecord.objects.filter(category=cat).count() == 40


def test_select_all_respects_the_active_filters(client, librarian, many_records):
    """« Tous les résultats » veut dire « de cette recherche », pas « du catalogue »."""
    cat = Category.objects.create(code="AD FIC", name="Adultes Fiction")
    client.post(
        reverse("catalog:record_bulk_assign"),
        {
            "select_all": "1",
            "back_qs": "q=Titre 0",
            "category": cat.pk,
            "location": "keep",
        },
    )
    touched = BibliographicRecord.objects.filter(category=cat).count()
    assert 0 < touched < 40


def test_select_all_on_items(client, librarian, many_records):
    other = Provenance.objects.create(code="OFELIA", label="Acheté par Ofelia")
    resp = client.post(
        reverse("catalog:item_bulk_assign"),
        {"select_all": "1", "back_qs": "mode=items", "provenance": other.pk},
    )
    assert resp.status_code == 302
    assert Item.objects.filter(provenance=other).count() == 40


def test_ticked_boxes_still_work(client, librarian, many_records):
    """Sans `select_all`, seules les cases cochées sont touchées."""
    cat = Category.objects.create(code="AD FIC", name="Adultes Fiction")
    client.post(
        reverse("catalog:record_bulk_assign"),
        {
            "ids": [many_records[0].pk, many_records[1].pk],
            "category": cat.pk,
            "location": "keep",
        },
    )
    assert BibliographicRecord.objects.filter(category=cat).count() == 2


def test_select_all_reaches_the_delete_confirmation(client, superadmin, many_records):
    resp = client.post(
        reverse("catalog:item_bulk_delete_confirm"),
        {"select_all": "1", "back_qs": "mode=items"},
    )
    assert resp.status_code == 200
    assert resp.context["count"] == 40


def test_the_confirmation_page_caps_what_it_displays(client, superadmin):
    """900 lignes affichées feraient une page interminable ; la sélection reste entière."""
    from apps.catalog.views import PREVIEW_LIMIT

    for i in range(PREVIEW_LIMIT + 5):
        record = BibliographicRecord.objects.create(title=f"T{i}")
        Item.objects.create(record=record)
    resp = client.post(
        reverse("catalog:item_bulk_delete_confirm"),
        {"select_all": "1", "back_qs": "mode=items"},
    )
    assert resp.context["count"] == PREVIEW_LIMIT + 5
    assert len(resp.context["items"]) == PREVIEW_LIMIT
    assert resp.context["hidden_count"] == 5
    assert len(resp.context["ids"]) == PREVIEW_LIMIT + 5


def test_select_all_deletes_everything_it_announced(client, superadmin, many_records):
    resp = client.post(
        reverse("catalog:item_bulk_delete"),
        {"select_all": "1", "back_qs": "mode=items"},
    )
    assert resp.status_code == 302
    assert Item.objects.count() == 0
    # Les notices, elles, restent au catalogue.
    assert BibliographicRecord.objects.count() == 40


# ── Provenance en toutes lettres ───────────────────────────────────────────


def test_the_filter_shows_the_full_provenance(client, librarian, borrowed):
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert "Prêt Bibliothèque de Genève" in body


def test_the_items_column_shows_the_full_provenance(client, librarian, many_records):
    body = client.get(
        reverse("catalog:record_list"), {"mode": "items"}
    ).content.decode()
    assert "Prêt Bibliothèque de Genève" in body


def test_a_provenance_without_label_falls_back_to_its_code(client, librarian):
    """Le code reste le repère quand aucun nom complet n'a été saisi."""
    Provenance.objects.create(code="DON")
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert ">DON<" in body
