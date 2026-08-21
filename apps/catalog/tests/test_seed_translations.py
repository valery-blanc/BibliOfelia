"""Tests FEAT-042 — seed_defaults applique les 4 langues + backfill idempotent."""
from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.catalog.models import Category

pytestmark = pytest.mark.django_db


def test_seed_populates_all_languages():
    call_command("seed_defaults")
    cat = Category.objects.get(code="AD FIC")
    assert cat.name_fr == "Adultes Fiction"
    assert cat.name_en == "Adults Fiction"
    assert cat.name_es == "Adultos Ficción"
    assert cat.name_mg == "Olon-dehibe Tantara foronina"


def test_seed_backfills_missing_translations_on_existing():
    Category.objects.create(code="AD FIC", name="Adultes Fiction", name_fr="Adultes Fiction")
    call_command("seed_defaults")
    cat = Category.objects.get(code="AD FIC")
    assert cat.name_en == "Adults Fiction"
    assert cat.name_es == "Adultos Ficción"
    assert cat.name_mg == "Olon-dehibe Tantara foronina"


def test_seed_preserves_existing_manual_translations():
    Category.objects.create(
        code="AD FIC",
        name="Adultes Fiction",
        name_fr="Adultes Fiction",
        name_en="MyCustomEN",
    )
    call_command("seed_defaults")
    cat = Category.objects.get(code="AD FIC")
    assert cat.name_en == "MyCustomEN"
    assert cat.name_es == "Adultos Ficción"
