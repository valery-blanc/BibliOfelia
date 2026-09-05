"""Tests vues usagers. SPEC §6.2 (Task #7)."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

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


def test_member_new_pre_fills_today_and_today_plus_one_year(client, librarian):
    """FEAT-037 : à la création, registration_date = today et
    expiration_date = today + 1 an déjà remplis dans le form."""
    from dateutil.relativedelta import relativedelta

    client.force_login(librarian)
    resp = client.get("/fr/members/new/")
    body = resp.content.decode()
    today_iso = date.today().isoformat()
    plus1_iso = (date.today() + relativedelta(years=1)).isoformat()
    assert f'value="{today_iso}"' in body
    assert f'value="{plus1_iso}"' in body


def test_member_edit_pre_fills_dates_in_iso_format(client, librarian, member):
    """BUG-015 : les inputs type=date doivent être pré-remplis au format ISO
    (sinon le navigateur affiche un input vide → effacement involontaire)."""
    member.birth_date = date(1980, 5, 12)
    member.registration_date = date(2026, 1, 15)
    member.expiration_date = date(2027, 1, 15)
    member.save()
    client.force_login(librarian)
    resp = client.get(f"/fr/members/{member.pk}/edit/")
    body = resp.content.decode()
    assert 'value="1980-05-12"' in body
    assert 'value="2026-01-15"' in body
    assert 'value="2027-01-15"' in body


# FEAT-072 : le formulaire usager embarque le formset de la famille — un POST
# navigateur envoie toujours ces compteurs, les tests aussi.
CHILDREN_MGMT = {
    "family-TOTAL_FORMS": "0",
    "family-INITIAL_FORMS": "0",
    "family-MIN_NUM_FORMS": "0",
    "family-MAX_NUM_FORMS": "1000",
}

def test_member_edit_preserves_dates_on_blank_resubmit(client, librarian, member, category):
    """BUG-015 régression : éditer sans toucher aux dates ne doit pas les effacer."""
    member.birth_date = date(1980, 5, 12)
    member.registration_date = date(2026, 1, 15)
    member.expiration_date = date(2027, 1, 15)
    member.save()
    client.force_login(librarian)
    resp = client.post(
        f"/fr/members/{member.pk}/edit/",
        {
            "first_name": member.first_name,
            "last_name": member.last_name,
            "category": category.pk,
            "birth_date": "1980-05-12",
            "registration_date": "2026-01-15",
            "expiration_date": "2027-01-15",
            **CHILDREN_MGMT,
        },
    )
    assert resp.status_code == 302
    member.refresh_from_db()
    assert member.birth_date == date(1980, 5, 12)
    assert member.registration_date == date(2026, 1, 15)
    assert member.expiration_date == date(2027, 1, 15)


def test_member_create_generates_card(client, librarian, category):
    client.force_login(librarian)
    resp = client.post(
        "/fr/members/new/",
        {
            "first_name": "Ada",
            "last_name": "Lovelace",
            "category": category.pk,
            "registration_date": date.today().isoformat(),
            **CHILDREN_MGMT,
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
    assert "cards-roll.pdf" not in resp.content.decode()


def test_member_detail_offers_the_62mm_card_print(client, librarian, member):
    """FEAT-090 : imprimer la carte ruban depuis la fiche, sans le picker."""
    client.force_login(librarian)
    resp = client.get(f"/fr/members/{member.pk}/")
    body = resp.content.decode()
    assert "Imprimer la carte (62 mm)" in body
    assert f"/fr/printing/cards-roll.pdf?ids={member.pk}" in body


def test_editing_category_cancels_unpaid_membership_invoice(
    client, librarian, member, category
):
    """BUG-042 : passer à une catégorie gratuite annule la cotisation ouverte."""
    from apps.finance.models import InvoiceStatus
    from apps.finance.services import create_membership_invoice

    category.membership_fee = Decimal("20.00")
    category.save(update_fields=["membership_fee"])
    invoice = create_membership_invoice(member, user=librarian)
    assert invoice is not None
    free = MemberCategory.objects.create(code="EMPLOYE", name="Employé")
    client.force_login(librarian)
    resp = client.post(
        f"/fr/members/{member.pk}/edit/",
        {
            "first_name": member.first_name,
            "last_name": member.last_name,
            "category": free.pk,
            "registration_date": (member.registration_date or date.today()).isoformat(),
            **CHILDREN_MGMT,
        },
    )
    assert resp.status_code == 302
    invoice.refresh_from_db()
    member.refresh_from_db()
    assert member.category_id == free.pk
    assert invoice.status == InvoiceStatus.CANCELLED
    detail = client.get(f"/fr/members/{member.pk}/")
    body = detail.content.decode()
    assert "À jour sur ses paiements" in body
    assert "Cotisation" not in body


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
    from html import unescape

    from dateutil.relativedelta import relativedelta

    client.force_login(librarian)
    resp = client.post(f"/fr/members/{member.pk}/renew/", follow=True)
    assert resp.redirect_chain[-1][0].endswith(f"/members/{member.pk}/edit/")
    member.refresh_from_db()
    expected = date.today() + relativedelta(months=12)
    assert member.expiration_date == expected
    body = unescape(resp.content.decode())
    assert "Nouvelle date d'expiration" in body
    assert expected.strftime("%d/%m/%Y") in body


def test_replace_card_view(client, librarian, member):
    old = member.card_number
    client.force_login(librarian)
    resp = client.post(f"/fr/members/{member.pk}/replace-card/")
    assert resp.status_code == 302
    member.refresh_from_db()
    assert member.card_number != old
    assert member.replaces_card_number == old


def test_replace_and_renew_live_on_edit_not_detail(client, librarian, member):
    """FEAT-092 : trop facile à déclencher depuis la fiche — déplacés sur Modifier."""
    client.force_login(librarian)
    detail = client.get(f"/fr/members/{member.pk}/").content.decode()
    edit = client.get(f"/fr/members/{member.pk}/edit/").content.decode()
    assert "Remplacer la carte" not in detail
    assert "Renouveler la carte" not in detail
    assert "Remplacer la carte" in edit
    assert "Renouveler la carte" in edit
    assert member.card_number in edit
    assert "advanced-section" in edit and " open>" in edit
    assert "invalidé" in edit
