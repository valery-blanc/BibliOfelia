"""FEAT-081 — une ancienne carte d'usager doit être reconnue partout.

`replace_card` archive l'ancien numéro dans `replaces_card_number`, mais la
carte physique reste des jours dans la poche de l'usager. Seul l'écran de prêt
l'acceptait : le même code-barres ouvrait la fiche au prêt et ne rendait rien
depuis l'accueil ou la liste des usagers.
"""
import pytest
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.members.lookup import find_member, is_replaced_card
from apps.members.models import Member, MemberCategory
from apps.members.services import replace_card

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)  # django-axes refuse login() hors requête
    return user


@pytest.fixture
def member():
    category = MemberCategory.objects.create(code="AD", name="Adultes")
    return Member.objects.create(
        first_name="Valéry", last_name="Blanc", category=category
    )


@pytest.fixture
def replaced(member):
    """Renvoie (usager, ancien_numéro, nouveau_numéro)."""
    old = member.card_number
    new = replace_card(member)
    member.refresh_from_db()
    assert old != new
    return member, old, new


# ── Résolveur ──────────────────────────────────────────────────────────────


def test_find_member_by_current_card(member):
    assert find_member(member.card_number) == member


def test_find_member_by_replaced_card(replaced):
    member, old, _new = replaced
    assert find_member(old) == member


def test_find_member_normalises_separators(replaced):
    member, old, _new = replaced
    assert find_member(f" {old[:3]}-{old[3:]} ") == member


def test_find_member_unknown_or_empty(member):
    assert find_member("2919999999999") is None
    assert find_member("") is None
    assert find_member(None) is None


def test_current_card_wins_over_someone_elses_old_card(replaced):
    """Si un numéro est à la fois carte courante d'un usager et ancienne carte
    d'un autre, c'est le porteur actuel qui gagne."""
    holder, old, _new = replaced
    category = MemberCategory.objects.first()
    other = Member.objects.create(
        first_name="Autre", last_name="Porteur", category=category
    )
    other.card_number = old
    other.save(update_fields=["card_number"])
    assert find_member(old) == other


def test_is_replaced_card(replaced):
    member, old, new = replaced
    assert is_replaced_card(member, old) is True
    assert is_replaced_card(member, new) is False


# ── Les trois écrans répondent pareil ──────────────────────────────────────


def test_home_search_finds_member_by_replaced_card(client, librarian, replaced):
    member, old, _new = replaced
    resp = client.get(reverse("core:search"), {"q": old})
    assert resp.status_code == 302
    assert resp["Location"].endswith(reverse("members:detail", args=[member.pk]))


def test_home_search_warns_that_the_card_was_replaced(client, librarian, replaced):
    member, old, new = replaced
    resp = client.get(reverse("core:search"), {"q": old}, follow=True)
    body = resp.content.decode()
    assert "Carte remplacée" in body
    assert new in body


def test_home_search_says_nothing_for_the_current_card(client, librarian, replaced):
    member, _old, new = replaced
    resp = client.get(reverse("core:search"), {"q": new}, follow=True)
    assert "Carte remplacée" not in resp.content.decode()


def test_member_list_finds_replaced_card(client, librarian, replaced):
    member, old, _new = replaced
    resp = client.get(reverse("members:list"), {"q": old})
    assert resp.status_code == 200
    assert member in list(resp.context["page_obj"].object_list)


def test_lend_accepts_replaced_card_and_warns(client, librarian, replaced):
    member, old, new = replaced
    resp = client.post(
        reverse("loans:lend"), {"action": "set_member", "card": old}, follow=True
    )
    assert resp.context["member"] == member
    body = resp.content.decode()
    assert "Carte remplacée" in body
    assert new in body


def test_lend_still_rejects_an_unknown_card(client, librarian, member):
    resp = client.post(
        reverse("loans:lend"), {"action": "set_member", "card": "2919999999999"},
        follow=True,
    )
    assert resp.context["member"] is None
    assert "Aucun usager pour cette carte" in resp.content.decode()


# ── Remplacement : prévenir qu'il faut réimprimer ──────────────────────────


def test_replace_card_tells_the_librarian_to_reprint(client, librarian, member):
    old = member.card_number
    resp = client.post(reverse("members:replace_card", args=[member.pk]), follow=True)
    body = resp.content.decode()
    assert "Nouvelle carte émise" in body
    # Le point qui manquait : rien ne disait que la carte en circulation
    # portait encore l'ancien numéro.
    assert old in body
    assert "imprimez la nouvelle carte" in body
