"""Tests FEAT-042 — seed_defaults applique les 4 langues aux MemberCategory."""
from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.members.models import MemberCategory

pytestmark = pytest.mark.django_db


def test_seed_populates_all_languages():
    call_command("seed_defaults")
    adulte = MemberCategory.objects.get(code="ADULTE")
    assert adulte.name_fr == "Adulte"
    assert adulte.name_en == "Adult"
    assert adulte.name_es == "Adulto"
    assert adulte.name_mg == "Olon-dehibe"


def test_seed_backfills_missing_translations():
    MemberCategory.objects.create(
        code="ADULTE",
        name="Adulte",
        name_fr="Adulte",
        max_concurrent_loans=5,
        default_loan_duration_days=21,
    )
    call_command("seed_defaults")
    adulte = MemberCategory.objects.get(code="ADULTE")
    assert adulte.name_en == "Adult"
    assert adulte.name_es == "Adulto"
    assert adulte.name_mg == "Olon-dehibe"
