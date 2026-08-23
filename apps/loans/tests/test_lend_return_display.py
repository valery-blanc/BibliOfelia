"""FEAT-080 — identification complète du livre au prêt et au retour.

Ce que ces tests protègent : au comptoir, le bibliothécaire scanne un code-barres
et doit reconnaître **le livre** et **la personne** sans rouvrir de fiche. Les
deux écrans n'affichaient qu'un titre et un code interne.
"""
from datetime import date, timedelta

import pytest
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.catalog.models import Author, BibliographicRecord, Item, ItemStatus
from apps.loans.models import LoanStatus
from apps.loans.services import create_loan, return_item
from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db

EXTERNAL = "BCF132770013"


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.login(username="lib", password="pw")
    return user


@pytest.fixture
def item():
    record = BibliographicRecord.objects.create(title="Pop :")
    record.authors.add(Author.objects.create(full_name="Silvia Borando"))
    return Item.objects.create(record=record, external_code=EXTERNAL)


@pytest.fixture
def member():
    category = MemberCategory.objects.create(code="AD", name="Adultes")
    return Member.objects.create(
        first_name="Amélie",
        last_name="Dupont",
        category=category,
        birth_date=date(1990, 6, 15),
    )


# ── Âge de l'usager ────────────────────────────────────────────────────────


def test_age_counts_completed_years(member):
    """Un anniversaire pas encore passé ne compte pas : sinon un usager né en
    décembre paraîtrait un an plus vieux pendant onze mois."""
    today = date.today()
    member.birth_date = today.replace(year=today.year - 30) + timedelta(days=1)
    assert member.age == 29
    member.birth_date = today.replace(year=today.year - 30)
    assert member.age == 30


def test_age_is_none_without_birth_date(member):
    member.birth_date = None
    assert member.age is None


# ── Panier de prêt ─────────────────────────────────────────────────────────


def _scan_for_lend(client, member, code):
    client.post(reverse("loans:lend"), {"action": "set_member", "card": member.card_number})
    return client.post(reverse("loans:lend"), {"action": "add_item", "ean": code},
                       follow=True)


@pytest.mark.parametrize("scanned", ["ean13", "external"])
def test_lend_basket_shows_title_author_and_both_codes(client, librarian, item,
                                                       member, scanned):
    """Quel que soit le code-barres scanné, le panier affiche les deux codes :
    on ne sait pas lequel le bibliothécaire a sous les yeux."""
    code = item.ean13 if scanned == "ean13" else EXTERNAL
    resp = _scan_for_lend(client, member, code)
    body = resp.content.decode()
    assert "Pop :" in body
    assert "Silvia Borando" in body
    assert item.ean13 in body
    assert EXTERNAL in body


def test_lend_basket_without_external_code(client, librarian, member):
    """Un exemplaire sans code externe n'affiche pas de pastille vide."""
    record = BibliographicRecord.objects.create(title="Sans code externe")
    plain = Item.objects.create(record=record)
    resp = _scan_for_lend(client, member, plain.ean13)
    body = resp.content.decode()
    assert plain.ean13 in body
    assert "Externe" not in body


# ── Journal de retour ──────────────────────────────────────────────────────


def _lend_then_return(client, item, member, librarian, code=None):
    create_loan(item, member, librarian)
    return client.post(
        reverse("loans:return_items"),
        {"action": "add_item", "ean": code or EXTERNAL},
        follow=True,
    )


def test_return_shows_book_member_codes_and_confirmation(client, librarian, item, member):
    resp = _lend_then_return(client, item, member, librarian)
    body = resp.content.decode()
    assert "Pop :" in body                     # titre
    assert "Silvia Borando" in body            # auteur
    assert "Dupont" in body and "Amélie" in body  # nom et prénom
    assert item.ean13 in body                  # n° Ofelia
    assert EXTERNAL in body                    # n° externe
    assert "Retour effectué" in body           # message explicite
    assert str(member.age) in body             # âge


def test_return_log_entry_carries_every_field(client, librarian, item, member):
    _lend_then_return(client, item, member, librarian)
    entry = client.session["return_log"][0]
    assert entry["title"] == "Pop :"
    assert entry["authors"] == "Silvia Borando"
    assert entry["ean13"] == item.ean13
    assert entry["external_code"] == EXTERNAL
    assert entry["member_last_name"] == "Dupont"
    assert entry["member_first_name"] == "Amélie"
    assert entry["member_pk"] == member.pk
    assert entry["member_age"] == member.age
    assert entry["kind"] == "returned"


def test_return_result_carries_the_settled_loan(item, member, librarian):
    """C'est ce qui permet de nommer la personne : sans le prêt, la vue n'a
    aucun moyen de la retrouver une fois le retour enregistré."""
    loan = create_loan(item, member, librarian)
    result = return_item(item, librarian)
    assert result.loan is not None and result.loan.pk == loan.pk
    assert result.loan.member == member


def test_lost_book_return_still_names_the_borrower(item, member, librarian):
    """Réintégration d'un livre perdu : le prêt est soldé par un update() de
    masse, il faut donc l'avoir lu avant — sinon plus personne à nommer."""
    loan = create_loan(item, member, librarian)
    loan.status = LoanStatus.LOST
    loan.save(update_fields=["status"])
    item.status = ItemStatus.LOST
    item.save(update_fields=["status"])

    result = return_item(item, librarian)
    assert result.kind == "reintegrated"
    assert result.loan is not None and result.loan.member == member


def test_return_without_active_loan_has_no_member(client, librarian, item):
    """Un livre rendu sans prêt en cours : pas de nom à afficher, et le journal
    doit le dire au lieu d'annoncer un retour effectué."""
    resp = client.post(
        reverse("loans:return_items"),
        {"action": "add_item", "ean": EXTERNAL},
        follow=True,
    )
    body = resp.content.decode()
    entry = client.session["return_log"][0]
    assert entry["kind"] == "no_loan"
    assert entry["member"] == ""
    assert "Rendu par" not in body
    assert "Aucun prêt actif" in body


def test_member_without_photo_or_birth_date_renders(client, librarian, item, member):
    """« Si ces infos sont présentes » : leur absence ne doit pas casser la page."""
    member.birth_date = None
    member.save(update_fields=["birth_date"])
    resp = _lend_then_return(client, item, member, librarian)
    assert resp.status_code == 200
    assert "Dupont" in resp.content.decode()
    assert client.session["return_log"][0]["member_age"] is None
    assert client.session["return_log"][0]["member_photo"] == ""


def test_old_session_entries_still_render(client, librarian):
    """Le journal vit en session : une entrée écrite avant FEAT-080 n'a pas les
    nouvelles clés et doit s'afficher quand même."""
    session = client.session
    session["return_log"] = [{
        "title": "Ancienne entrée", "internal_id": "OFL-20260101-0001",
        "kind": "returned", "overdue": False, "reservation": "",
    }]
    session.save()
    resp = client.get(reverse("loans:return_items"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Ancienne entrée" in body
    assert "OFL-20260101-0001" in body


def test_templates_have_no_broken_comment(client, librarian, item, member):
    """Un commentaire {# #} à cheval sur deux lignes n'en est pas un (le lexer
    Django n'active pas DOTALL) : il s'afficherait en clair dans la page."""
    for resp in (client.get(reverse("loans:lend")),
                 client.get(reverse("loans:return_items"))):
        body = resp.content.decode()
        assert "FEAT-080" not in body
        assert "{#" not in body
