"""Tests UI base : tag icône, recherche globale, préférences. Task #5."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item, Location
from apps.core.templatetags.biblio_icons import icon, icon_inner
from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db


def test_icon_tag_inlines_svg():
    html = icon("search")
    assert "<svg" in html and "icon-search" in html

def test_icon_tag_unknown_returns_empty():
    assert icon("does-not-exist") == ""

def test_icon_inner_rejects_path_traversal():
    assert icon_inner("../secret") == ""


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def member(db):
    cat = MemberCategory.objects.create(code="AD", name="Adulte")
    return Member.objects.create(first_name="Ada", last_name="Lovelace", category=cat)


def test_search_member_card_redirects_to_detail(client, librarian, member):
    client.force_login(librarian)
    resp = client.get("/fr/search/", {"q": member.card_number})
    assert resp.status_code == 302
    assert resp.url.endswith(f"/members/{member.pk}/")


def test_search_item_ean_redirects_to_record(client, librarian):
    rec = BibliographicRecord.objects.create(title="Test")
    loc = Location.objects.create(code="A1")
    item = Item.objects.create(record=rec, location=loc)
    client.force_login(librarian)
    resp = client.get("/fr/search/", {"q": item.ean13})
    assert resp.status_code == 302
    assert resp.url.endswith(f"/catalog/{rec.pk}/")


def test_search_text_redirects_to_catalog_list(client, librarian):
    client.force_login(librarian)
    resp = client.get("/fr/search/", {"q": "jules verne"})
    assert resp.status_code == 302
    assert "/catalog/" in resp.url and "q=jules" in resp.url


def test_toggle_advanced_flips_preference(client, librarian):
    client.force_login(librarian)
    assert librarian.always_show_advanced is False
    client.post("/fr/preferences/advanced/")
    librarian.refresh_from_db()
    assert librarian.always_show_advanced is True


def test_search_requires_login(client):
    resp = client.get("/fr/search/", {"q": "x"})
    assert resp.status_code == 302
    assert "/accounts/login/" in resp.url
