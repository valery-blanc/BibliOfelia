"""FEAT-065 (langues parlées), FEAT-070 (liste gérée) et FEAT-072 (famille)."""
from __future__ import annotations

from datetime import date

import pytest
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.members.languages import display, labels_for, spoken_language_choices
from apps.members.models import Member, MemberCategory, MemberFamilyMember

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def languages(db):
    """FEAT-070 : la liste des langues vit en base, il faut donc la semer."""
    from apps.catalog.models import Language
    from apps.core.management.commands.seed_defaults import LANGUAGES_SEED

    for code, fr, en, es, mg in LANGUAGES_SEED:
        Language.objects.get_or_create(
            code=code,
            defaults={"name": fr, "name_fr": fr, "name_en": en, "name_es": es, "name_mg": mg},
        )


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Ada", last_name="Lovelace", category=category
    )


def _post_data(category, **overrides):
    """Corps d'un POST du formulaire usager, formset des enfants compris."""
    data = {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "category": category.pk,
        "preferred_language": "",
        "spoken_languages_other": "",
        "registration_date": date.today().isoformat(),
        "family-TOTAL_FORMS": "1",
        "family-INITIAL_FORMS": "0",
        "family-MIN_NUM_FORMS": "0",
        "family-MAX_NUM_FORMS": "1000",
        "family-0-first_name": "",
        "family-0-gender": "",
        "family-0-kind": "child",
        "family-0-birth_year": "",
        "family-0-languages_other": "",
    }
    data.update(overrides)
    return data


# ── FEAT-065 : liste des langues ───────────────────────────────────────────


def test_language_list_has_the_22_requested_entries():
    """FEAT-070 : la liste vient désormais de la base, pas du code."""
    choices = spoken_language_choices()
    assert len(choices) == 22
    codes = [code for code, _label in choices]
    assert len(set(codes)) == 22, "les codes doivent être uniques"
    assert set(codes) >= {"fr", "en", "mg", "ta", "sq"}


def test_choices_are_sorted_alphabetically_by_label():
    """Tri par libellé traduit : c'est l'ordre attendu par le lecteur."""
    labels = [str(label) for _code, label in spoken_language_choices()]
    assert labels == sorted(labels, key=str.lower)


def test_labels_are_alphabetical_not_in_saved_order():
    """Deux fiches avec les mêmes langues s'affichent pareil."""
    assert labels_for(["mg", "fr"]) == ["Français", "Malgache"]


def test_unknown_language_code_is_kept_as_is():
    """On n'escamote pas une donnée qu'on ne sait pas nommer."""
    assert labels_for(["fr", "xx"]) == ["Français", "xx"]


def test_display_appends_the_free_text_field():
    assert display(["fr"], "wolof, peul") == "Français, wolof, peul"
    assert display([], "") == ""


# ── FEAT-065 : formulaire et fiche ─────────────────────────────────────────


def test_member_form_offers_every_language(client, librarian, category):
    body = client.get(reverse("members:create")).content.decode()
    assert "Langues parlées" in body
    assert 'value="sq"' in body   # Albanais
    assert 'value="fa-farsi"' in body  # Farsi, distinct de Persan (fa)


def test_create_member_with_spoken_languages(client, librarian, category):
    resp = client.post(
        reverse("members:create"),
        _post_data(
            category,
            spoken_languages=["fr", "ar"],
            spoken_languages_other="wolof, peul",
        ),
    )
    assert resp.status_code == 302
    member = Member.objects.get(last_name="Lovelace")
    assert member.spoken_languages == ["fr", "ar"]
    assert member.spoken_languages_other == "wolof, peul"
    # Ordre alphabétique des libellés (FEAT-070), puis le champ libre.
    assert member.spoken_languages_display == "Arabe, Français, wolof, peul"


def test_member_detail_shows_spoken_languages(client, librarian, member):
    member.spoken_languages = ["pt"]
    member.save(update_fields=["spoken_languages"])
    body = client.get(reverse("members:detail", args=[member.pk])).content.decode()
    assert "Portugais" in body


def test_member_without_languages_saves_empty_list(client, librarian, category):
    client.post(reverse("members:create"), _post_data(category))
    assert Member.objects.get(last_name="Lovelace").spoken_languages == []


# ── FEAT-072 : famille ─────────────────────────────────────────────────────


def test_parent_account_field_is_gone():
    assert not any(f.name == "parent_account" for f in Member._meta.get_fields())


def test_create_member_with_a_child(client, librarian, category):
    resp = client.post(
        reverse("members:create"),
        _post_data(
            category,
            **{
                "family-0-first_name": "Pierre",
                "family-0-gender": "m",
                "family-0-kind": "child",
                "family-0-birth_year": "2019",
                "family-0-languages": ["fr", "mg"],
                "family-0-languages_other": "créole",
            },
        ),
    )
    assert resp.status_code == 302
    child = MemberFamilyMember.objects.get()
    assert child.first_name == "Pierre"
    assert child.gender == "m"
    assert child.birth_year == 2019
    assert child.age == date.today().year - 2019
    assert child.languages == ["fr", "mg"]
    assert child.languages_display == "Français, Malgache, créole"


def test_several_family_members_on_one_member(client, librarian, category):
    resp = client.post(
        reverse("members:create"),
        _post_data(
            category,
            **{
                "family-TOTAL_FORMS": "2",
                "family-0-first_name": "Pierre",
                "family-0-kind": "child",
                "family-0-birth_year": "2019",
                "family-1-first_name": "Marie",
                "family-1-gender": "f",
                "family-1-kind": "child",
                "family-1-birth_year": "2016",
                "family-1-languages_other": "",
            },
        ),
    )
    assert resp.status_code == 302
    member = Member.objects.get(last_name="Lovelace")
    assert [c.first_name for c in member.family.all()] == ["Marie", "Pierre"]


def test_empty_family_row_is_ignored(client, librarian, category):
    """La ligne vide toujours présente ne doit pas bloquer l'enregistrement."""
    resp = client.post(reverse("members:create"), _post_data(category))
    assert resp.status_code == 302
    assert MemberFamilyMember.objects.count() == 0


def test_clearing_the_first_name_removes_the_child(client, librarian, member):
    """Le bouton « Retirer » vide la ligne : le serveur en déduit la suppression."""
    child = MemberFamilyMember.objects.create(member=member, first_name="Pierre", birth_year=2019)
    resp = client.post(
        reverse("members:edit", args=[member.pk]),
        {
            "first_name": member.first_name,
            "last_name": member.last_name,
            "category": member.category_id,
            "preferred_language": "",
            "spoken_languages_other": "",
            "registration_date": member.registration_date.isoformat(),
            "family-TOTAL_FORMS": "1",
            "family-INITIAL_FORMS": "1",
            "family-MIN_NUM_FORMS": "0",
            "family-MAX_NUM_FORMS": "1000",
            "family-0-id": child.pk,
            "family-0-first_name": "",
            "family-0-gender": "",
            "family-0-kind": "child",
        "family-0-birth_year": "",
            "family-0-languages_other": "",
        },
    )
    assert resp.status_code == 302
    assert not MemberFamilyMember.objects.filter(pk=child.pk).exists()


def test_member_detail_lists_the_family(client, librarian, member):
    MemberFamilyMember.objects.create(
        member=member, first_name="Pierre", birth_year=2019, languages=["fr"]
    )
    body = client.get(reverse("members:detail", args=[member.pk])).content.decode()
    assert "Pierre" in body
    assert "Français" in body


def test_family_is_deleted_with_the_member(member):
    MemberFamilyMember.objects.create(member=member, first_name="Pierre")
    member.delete()
    assert MemberFamilyMember.objects.count() == 0


def test_an_adult_family_member_has_no_age(client, librarian, category):
    """« Adulte » : pas d'année de naissance, donc pas d'âge calculé."""
    resp = client.post(
        reverse("members:create"),
        _post_data(
            category,
            **{
                "family-0-first_name": "Hery",
                "family-0-kind": "adult",
                "family-0-birth_year": "1980",
            },
        ),
    )
    assert resp.status_code == 302
    person = MemberFamilyMember.objects.get()
    assert person.is_adult is True
    assert person.birth_year is None
    assert person.age is None


def test_family_first_names_feed_the_card(client, librarian, member):
    """FEAT-072 : la carte imprimée liste les prénoms de la famille."""
    MemberFamilyMember.objects.create(member=member, first_name="Tiana")
    MemberFamilyMember.objects.create(member=member, first_name="Mamy")
    assert member.family_first_names == ["Mamy", "Tiana"]


def test_member_form_says_famille_not_enfants(client, librarian, category):
    body = client.get(reverse("members:create")).content.decode()
    assert "Famille" in body
    assert "Ajouter une personne" in body
