"""Coordonnées complètes de l'usager. FEAT-083."""
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
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


def _post_data(category, **overrides):
    data = {
        "first_name": "Ada", "last_name": "Lovelace",
        "category": category.pk,
        "registration_date": date.today().isoformat(),
        "family-TOTAL_FORMS": "0", "family-INITIAL_FORMS": "0",
        "family-MIN_NUM_FORMS": "0", "family-MAX_NUM_FORMS": "1000",
    }
    data.update(overrides)
    return data


def test_contact_fields_are_saved(client, librarian, category):
    client.force_login(librarian)
    resp = client.post("/fr/members/new/", _post_data(
        category,
        email="ada@example.org",
        contact_phone="+41 22 000 00 00",
        address_street="12 rue des Lilas",
        address_extra="Bâtiment B, 3e étage",
        address_postal_code="1218",
        address_city="Le Grand-Saconnex",
        address_state="Genève",
        address_country="Suisse",
    ))
    assert resp.status_code == 302
    member = Member.objects.get(last_name="Lovelace")
    assert member.email == "ada@example.org"
    assert member.address_city == "Le Grand-Saconnex"
    assert member.address_state == "Genève"


def test_address_lines_skip_empty_parts(category):
    member = Member.objects.create(
        first_name="Sans", last_name="Complement", category=category,
        address_street="12 rue des Lilas",
        address_postal_code="1218", address_city="Le Grand-Saconnex",
        address_country="Suisse",
    )
    assert member.address_lines == [
        "12 rue des Lilas", "1218 Le Grand-Saconnex", "Suisse",
    ]


def test_address_lines_is_empty_without_address(category):
    member = Member.objects.create(
        first_name="Sans", last_name="Adresse", category=category
    )
    assert member.address_lines == []


def test_invalid_email_is_refused(client, librarian, category):
    client.force_login(librarian)
    resp = client.post(
        "/fr/members/new/", _post_data(category, email="pas-une-adresse")
    )
    assert resp.status_code == 200
    assert Member.objects.filter(last_name="Lovelace").count() == 0


def test_comment_is_capped_at_500_characters(client, librarian, category):
    """Val demandait « un champ commentaire libre optionnel (500 caractères) ».
    Le champ existant `notes` est réutilisé, plafonné par le formulaire."""
    client.force_login(librarian)
    resp = client.post("/fr/members/new/", _post_data(category, notes="x" * 501))
    assert resp.status_code == 200
    assert Member.objects.filter(last_name="Lovelace").count() == 0

    resp = client.post("/fr/members/new/", _post_data(category, notes="x" * 500))
    assert resp.status_code == 302


def test_existing_long_notes_stay_readable(category):
    """La limite est côté formulaire : une note plus ancienne et plus longue
    ne doit pas devenir invalide."""
    member = Member.objects.create(
        first_name="Vieille", last_name="Fiche", category=category,
        notes="y" * 900,
    )
    member.full_clean()  # ne lève pas : le modèle n'a pas de max_length
    assert len(member.notes) == 900


def test_country_is_prefilled_from_the_library(client, librarian, category):
    from apps.core.models import Setting

    Setting.set("library_identity", {"name": "Ofelia", "country": "Venezuela"})
    client.force_login(librarian)
    resp = client.get("/fr/members/new/")
    assert resp.status_code == 200
    assert b"Venezuela" in resp.content


def test_member_detail_shows_email_and_address(client, librarian, category):
    member = Member.objects.create(
        first_name="Marie", last_name="Curie", category=category,
        email="marie@example.org", address_street="1 rue Pierre",
        address_city="Paris",
    )
    client.force_login(librarian)
    resp = client.get(f"/fr/members/{member.pk}/")
    assert b"marie@example.org" in resp.content
    assert b"1 rue Pierre" in resp.content
