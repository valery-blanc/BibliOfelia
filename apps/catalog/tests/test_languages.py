"""FEAT-070 — liste de langues gérée (documents + usagers)."""
from __future__ import annotations

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import translation

from apps.accounts.models import Role, User
from apps.catalog.languages import (
    label_for,
    language_choices,
    normalize_language_code,
)
from apps.catalog.models import BibliographicRecord, Language

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture
def seeded():
    call_command("seed_defaults")


# ── Normalisation des codes ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("fr", "fr"),
        ("FR", "fr"),
        ("fre", "fr"),
        ("fre-fre", "fr"),   # BnF : langue du texte + langue de l'original
        ("fre-eng", "fr"),
        ("eng-fre", "en"),
        ("fre-jpn", "fr"),
        ("spa", "es"),
        ("ger", "de"),
        ("mlg", "mg"),
        ("fr_CA", "fr"),     # pas de variante régionale
        ("", ""),
        ("zzz", "zzz"),      # inconnu : conservé tel quel
    ],
)
def test_normalize_language_code(raw, expected):
    assert normalize_language_code(raw) == expected


# ── Le seed ────────────────────────────────────────────────────────────────


def test_seed_creates_the_22_languages(seeded):
    assert Language.objects.count() == 22
    assert Language.objects.get(code="ta").name == "Tamoul"


def test_seed_is_idempotent(seeded):
    call_command("seed_defaults")
    assert Language.objects.count() == 22


def test_seed_translates_every_language(seeded):
    fr = Language.objects.get(code="fr")
    assert (fr.name_fr, fr.name_en, fr.name_es, fr.name_mg) == (
        "Français", "French", "Francés", "Frantsay",
    )


def test_seed_preserves_a_hand_written_name(seeded):
    """Une langue renommée par la bibliothèque survit au redémarrage."""
    Language.objects.filter(code="sh").update(name_fr="Bosniaque")
    call_command("seed_defaults")
    assert Language.objects.get(code="sh").name_fr == "Bosniaque"


# ── Choix triés ────────────────────────────────────────────────────────────


def test_choices_are_alphabetical_in_french(seeded):
    with translation.override("fr"):
        labels = [str(label) for _c, label in language_choices(include_blank=False)]
    assert labels[0] == "Albanais"
    assert labels == sorted(labels, key=str.lower)


def test_choices_are_alphabetical_in_english_too(seeded):
    """L'ordre suit la langue de l'interface, il change donc d'une langue à l'autre."""
    with translation.override("en"):
        labels = [str(label) for _c, label in language_choices(include_blank=False)]
    assert labels[0] == "Albanian"
    assert labels == sorted(labels, key=str.lower)


def test_blank_option_is_offered_for_forms(seeded):
    choices = language_choices()
    assert choices[0][0] == ""
    assert len(choices) == 23


def test_label_for_falls_back_to_the_raw_code(seeded):
    assert label_for("fr") == "Français"
    assert label_for("zzz") == "zzz"
    assert label_for("") == ""


# ── Branchement dans le catalogue ──────────────────────────────────────────


def test_record_form_offers_the_managed_languages(client, librarian, seeded):
    body = client.get(reverse("catalog:record_create")).content.decode()
    assert 'value="de"' in body   # Allemand : impossible à saisir avant FEAT-070
    assert 'value="ta"' in body


def test_catalog_filter_lists_the_managed_languages(client, librarian, seeded):
    resp = client.get(reverse("catalog:record_list"))
    codes = [code for code, _label in resp.context["languages"]]
    assert "de" in codes and "ja" in codes


def test_catalog_filter_finds_a_german_record(client, librarian, seeded):
    keeper = BibliographicRecord.objects.create(title="Der Prozess", language="de")
    BibliographicRecord.objects.create(title="Fondation", language="fr")
    resp = client.get(reverse("catalog:record_list"), {"language": "de"})
    assert list(resp.context["page_obj"]) == [keeper]


# ── Écran de gestion ───────────────────────────────────────────────────────


def test_language_list_counts_records(client, librarian, seeded):
    BibliographicRecord.objects.create(title="Der Prozess", language="de")
    resp = client.get(reverse("catalog:language_list"))
    counts = {lang.code: lang.records_count for lang in resp.context["languages"]}
    assert counts["de"] == 1
    assert counts["fr"] == 0


def test_language_list_is_sorted_by_label(client, librarian, seeded):
    resp = client.get(reverse("catalog:language_list"))
    labels = [str(lang) for lang in resp.context["languages"]]
    assert labels == sorted(labels, key=str.lower)


def test_create_a_language(client, librarian):
    resp = client.post(
        reverse("catalog:language_create"), {"code": "NL", "name": "Néerlandais"}
    )
    assert resp.status_code == 302
    assert Language.objects.get(code="nl").name == "Néerlandais"  # code normalisé


def test_edit_a_language(client, librarian, seeded):
    lang = Language.objects.get(code="sh")
    client.post(
        reverse("catalog:language_edit", args=[lang.pk]),
        {"code": "sh", "name": "Bosniaque-croate-serbe"},
    )
    lang.refresh_from_db()
    assert lang.name == "Bosniaque-croate-serbe"


def test_delete_a_language_keeps_the_records(client, librarian, seeded):
    """Retirer une langue de la liste ne touche à aucune notice."""
    record = BibliographicRecord.objects.create(title="Der Prozess", language="de")
    lang = Language.objects.get(code="de")
    resp = client.post(reverse("catalog:language_delete", args=[lang.pk]))
    assert resp.status_code == 302
    record.refresh_from_db()
    assert record.language == "de"
    assert not Language.objects.filter(code="de").exists()


def test_delete_page_announces_the_records(client, librarian, seeded):
    BibliographicRecord.objects.create(title="Der Prozess", language="de")
    lang = Language.objects.get(code="de")
    resp = client.get(reverse("catalog:language_delete", args=[lang.pk]))
    assert resp.context["records_count"] == 1


def test_languages_are_reachable_from_advanced(client, librarian):
    body = client.get(reverse("core:advanced")).content.decode()
    assert reverse("catalog:language_list") in body


# ── Langue de correspondance de l'usager : inchangée ───────────────────────


def test_member_correspondence_language_stays_on_ui_languages(client, seeded):
    """BibliOfelia ne sait écrire qu'en 4 langues : ce menu ne bouge pas."""
    from apps.members.forms import MemberForm

    codes = [code for code, _label in MemberForm().fields["preferred_language"].widget.choices]
    assert set(codes) == {"", "fr", "en", "es", "mg"}
