"""Tests FEAT-042 — seed_defaults applique les 4 langues + backfill idempotent."""
from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.catalog.models import Category

pytestmark = pytest.mark.django_db


def test_seed_populates_all_languages():
    call_command("seed_defaults")
    enf = Category.objects.get(code="ENF")
    assert enf.name_fr == "Enfance"
    assert enf.name_en == "Childhood"
    assert enf.name_es == "Infancia"
    assert enf.name_mg == "Fahazazana"


def test_seed_backfills_missing_translations_on_existing():
    Category.objects.create(code="ENF", name="Enfance", name_fr="Enfance")
    call_command("seed_defaults")
    enf = Category.objects.get(code="ENF")
    assert enf.name_en == "Childhood"
    assert enf.name_es == "Infancia"
    assert enf.name_mg == "Fahazazana"


def test_seed_preserves_existing_manual_translations():
    Category.objects.create(
        code="ENF",
        name="Enfance",
        name_fr="Enfance",
        name_en="MyCustomEN",
    )
    call_command("seed_defaults")
    enf = Category.objects.get(code="ENF")
    assert enf.name_en == "MyCustomEN"
    assert enf.name_es == "Infancia"
