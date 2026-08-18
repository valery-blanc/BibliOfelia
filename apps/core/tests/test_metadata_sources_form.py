"""FEAT-059 — sources d'enrichissement actives par défaut."""
from __future__ import annotations

import pytest

from apps.core.forms import MetadataSourcesForm
from apps.core.models import Setting

pytestmark = pytest.mark.django_db


def test_all_sources_active_on_a_fresh_instance():
    """Aucun réglage posé (instance neuve) → les 6 sources sont proposées.

    Google Books était exclu par défaut : sur sanjuan / grand-saconnex la page
    d'enrichissement n'affichait donc que 3 cases (OpenLibrary, BnF, BNE).
    """
    assert Setting.objects.filter(key=MetadataSourcesForm.KEY).count() == 0
    assert MetadataSourcesForm.active_sources() == MetadataSourcesForm.SOURCE_ORDER


def test_active_sources_respects_explicit_opt_out():
    Setting.set(MetadataSourcesForm.KEY, {"bne": False, "k10plus": False})
    active = MetadataSourcesForm.active_sources()
    assert "bne" not in active and "k10plus" not in active
    assert "openlibrary" in active and "google_books" in active


def test_save_persists_every_source_flag():
    form = MetadataSourcesForm(
        data={
            "google_books_api_key": " KEY ",
            "openlibrary_enabled": "on",
            "bnf_enabled": "on",
            "swisscovery_enabled": "on",
        }
    )
    assert form.is_valid(), form.errors
    form.save()
    assert Setting.get(MetadataSourcesForm.KEY_API_KEY) == "KEY"
    assert Setting.get(MetadataSourcesForm.KEY) == {
        "openlibrary": True,
        "google_books": False,
        "bnf": True,
        "bne": False,
        "swisscovery": True,
        "k10plus": False,
    }


def test_enrichment_page_shows_readable_labels(client):
    """La page d'enrichissement propose une case par source, libellé lisible."""
    from django.urls import reverse

    from apps.accounts.models import Role, User
    from apps.catalog.sources import SOURCE_LABELS

    client.force_login(
        User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    )
    html = client.get(reverse("core:enrichment_index")).content.decode()
    for source in MetadataSourcesForm.SOURCE_ORDER:
        assert f'value="{source}"' in html
        assert SOURCE_LABELS[source] in html
    assert ">bnf<" not in html  # plus de slug brut affiché


def test_every_active_source_has_a_label():
    from apps.catalog.sources import SOURCE_LABELS, SOURCES

    for source in MetadataSourcesForm.SOURCE_ORDER:
        assert source in SOURCES
        assert source in SOURCE_LABELS
