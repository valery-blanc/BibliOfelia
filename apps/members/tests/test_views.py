"""Tests vues usagers. SPEC §6.2 (Task #7)."""
from __future__ import annotations

from datetime import date

import pytest

from apps.accounts.models import Role
from apps.members.models import Member, MemberCategory

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
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Marie", last_name="Curie", category=category
    )


def test_member_create_generates_card(client, librarian, category):
    client.force_login(librarian)
    resp = client.post(
        "/fr/members/new/",
        {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "category": category.pk,
            "registration_date": date.today().isoformat(),
        },
    )
    assert resp.status_code == 302
    member = Member.objects.get(last_name="Lovelace")
    assert member.card_number.startswith("291")
    assert member.expiration_date is not None


def test_member_create_forbidden_for_readonly(client, readonly, category):
    client.force_login(readonly)
    assert client.get("/fr/members/new/").status_code == 403


def test_member_detail_accessible(client, readonly, member):
    client.force_login(readonly)
    resp = client.get(f"/fr/members/{member.pk}/")
    assert resp.status_code == 200
    assert b"Curie" in resp.content


def test_member_history_page(client, librarian, member):
    client.force_login(librarian)
    resp = client.get(f"/fr/members/{member.pk}/history/")
    assert resp.status_code == 200


def test_member_list_search_by_name(client, librarian, member):
    client.force_login(librarian)
    resp = client.get("/fr/members/", {"q": "curie"})
    assert resp.status_code == 200
    assert b"Curie" in resp.content


def test_renew_card_view(client, librarian, member):
    client.force_login(librarian)
    resp = client.post(f"/fr/members/{member.pk}/renew/")
    assert resp.status_code == 302


def test_replace_card_view(client, librarian, member):
    old = member.card_number
    client.force_login(librarian)
    resp = client.post(f"/fr/members/{member.pk}/replace-card/")
    assert resp.status_code == 302
    member.refresh_from_db()
    assert member.card_number != old
    assert member.replaces_card_number == old
