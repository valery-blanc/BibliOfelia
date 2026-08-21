"""FEAT-071 — catégories officielles Ofelia et reprise des anciennes."""
from __future__ import annotations

import pytest
from django.core.management import call_command

from apps.catalog.models import BibliographicRecord, Category

pytestmark = pytest.mark.django_db


def _seed():
    call_command("seed_defaults")


# ── Le seed ────────────────────────────────────────────────────────────────


def test_seed_creates_the_20_official_categories():
    _seed()
    assert Category.objects.count() == 20
    assert set(Category.objects.values_list("code", flat=True)) == {
        f"{age} {kind}"
        for age in ("AD", "JE", "ADO", "EN", "PE")
        for kind in ("FIC", "DOC", "ALB", "BD")
    }


def test_code_and_abbreviation_are_the_same():
    """La cote imprimée sur la tranche est le code : une seule vérité."""
    _seed()
    assert all(c.code == c.abbreviation for c in Category.objects.all())


def test_teen_fiction_is_ado_fic_not_ado_doc():
    """La liste fournie portait la coquille `ADO DOC` pour « Adolescents Fiction »."""
    _seed()
    assert Category.objects.get(code="ADO FIC").name == "Adolescents Fiction"
    assert Category.objects.get(code="ADO DOC").name == "Adolescents Documentaire"


def test_names_are_translated():
    _seed()
    cat = Category.objects.get(code="PE ALB")
    assert cat.name_fr == "Petite enfance Album"
    assert cat.name_en == "Early childhood Picture books"
    assert cat.name_es == "Primera infancia Álbum"
    assert cat.name_mg == "Zaza madinika Boky misy sary"


def test_categories_have_no_parent():
    """Une tranche d'âge n'est pas un rayon : plus de hiérarchie."""
    _seed()
    assert not Category.objects.filter(parent__isnull=False).exists()


# ── Reprise : préfixe de langue ────────────────────────────────────────────


def test_language_prefix_is_stripped_and_merged():
    """Cas grand-saconnex : « FR AD FIC » rejoint « AD FIC »."""
    old = Category.objects.create(
        code="FR AD FIC", name="Français Adultes Fiction"
    )
    record = BibliographicRecord.objects.create(title="Fondation", category=old)
    call_command("migrate_categories")

    record.refresh_from_db()
    assert record.category.code == "AD FIC"
    assert not Category.objects.filter(code="FR AD FIC").exists()


def test_every_prefixed_category_is_merged():
    codes = ["FR AD BD", "FR AD DOC", "FR EN ALB", "FR JE FIC"]
    for code in codes:
        cat = Category.objects.create(code=code, name=code)
        BibliographicRecord.objects.create(title=code, category=cat)
    call_command("migrate_categories")

    assert not Category.objects.filter(code__startswith="FR ").exists()
    assert Category.objects.count() == 20
    assert BibliographicRecord.objects.filter(category__isnull=True).count() == 0


def test_a_prefix_on_an_unknown_code_is_left_alone():
    """On ne décapite pas une catégorie qu'on ne saurait pas reclasser."""
    Category.objects.create(code="FR MAISON", name="Français Maison")
    call_command("migrate_categories")
    assert Category.objects.filter(code="FR MAISON").exists()


# ── Reprise : anciennes catégories du seed ─────────────────────────────────


def test_legacy_seed_categories_are_remapped():
    novels = Category.objects.create(code="ADU-ROM", name="Romans")
    sciences = Category.objects.create(code="DOC-SCI", name="Sciences")
    a = BibliographicRecord.objects.create(title="Fondation", category=novels)
    b = BibliographicRecord.objects.create(title="Cosmos", category=sciences)
    call_command("migrate_categories")

    a.refresh_from_db()
    b.refresh_from_db()
    assert a.category.code == "AD FIC"
    assert b.category.code == "AD DOC"
    assert not Category.objects.filter(code__in=["ADU-ROM", "DOC-SCI"]).exists()


def test_empty_umbrella_categories_are_removed():
    Category.objects.create(code="ENF", name="Enfance")
    Category.objects.create(code="ADU", name="Adultes")
    call_command("migrate_categories")
    assert not Category.objects.filter(code__in=["ENF", "ADU"]).exists()


def test_an_unknown_category_survives():
    """Le fonds local d'une bibliothèque n'est jamais supprimé en silence."""
    local = Category.objects.create(code="LOCAL", name="Fonds local")
    record = BibliographicRecord.objects.create(title="Chronique", category=local)
    call_command("migrate_categories")

    record.refresh_from_db()
    assert record.category == local
    assert Category.objects.filter(code="LOCAL").exists()


# ── Garanties de la commande ───────────────────────────────────────────────


def test_dry_run_changes_nothing():
    old = Category.objects.create(code="FR AD FIC", name="Français Adultes Fiction")
    call_command("migrate_categories", "--dry-run")
    assert Category.objects.filter(pk=old.pk).exists()
    assert Category.objects.count() == 1


def test_command_is_idempotent():
    Category.objects.create(code="FR AD FIC", name="Français Adultes Fiction")
    call_command("migrate_categories")
    call_command("migrate_categories")
    assert Category.objects.count() == 20


def test_command_creates_the_targets_on_an_empty_base():
    call_command("migrate_categories")
    assert Category.objects.count() == 20


def test_records_never_lose_their_category_when_remapped():
    for code in ("FR AD FIC", "ADU-ROM", "DOC-REL"):
        cat = Category.objects.create(code=code, name=code)
        BibliographicRecord.objects.create(title=code, category=cat)
    call_command("migrate_categories")
    assert BibliographicRecord.objects.filter(category__isnull=True).count() == 0
