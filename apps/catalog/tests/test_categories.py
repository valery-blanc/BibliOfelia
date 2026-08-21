"""FEAT-067 — catégorie abrégée (cote) + écran de gestion des catégories."""
from __future__ import annotations

import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.catalog.excel_catalog import run_import_job
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    ExcelCatalogJob,
    ExcelJobMode,
)

pytestmark = pytest.mark.django_db

VALID_ISBN = "9782070368228"


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture
def category():
    return Category.objects.create(
        code="ADU-ROM-ADO", name="Romans fiction pour adolescents",
        abbreviation="RO FI ADO",
    )


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


# ── Écran de gestion ───────────────────────────────────────────────────────


def test_category_list_shows_abbreviation_and_counts(client, librarian, category):
    BibliographicRecord.objects.create(title="Fondation", category=category)
    resp = client.get(reverse("catalog:category_list"))
    assert resp.status_code == 200
    assert resp.context["categories"][0].records_count == 1
    assert "RO FI ADO" in resp.content.decode()


def test_category_create_with_abbreviation(client, librarian):
    resp = client.post(
        reverse("catalog:category_create"),
        {
            "code": "ADU-POL",
            "name": "Romans policiers",
            "abbreviation": "RO POL",
            "parent": "",
            "default_loan_duration_days": "",
        },
    )
    assert resp.status_code == 302
    assert Category.objects.get(code="ADU-POL").abbreviation == "RO POL"


def test_category_edit_abbreviation(client, librarian, category):
    client.post(
        reverse("catalog:category_edit", args=[category.pk]),
        {
            "code": category.code,
            "name": category.name,
            "abbreviation": "ROM ADO",
            "parent": "",
            "default_loan_duration_days": "",
        },
    )
    category.refresh_from_db()
    assert category.abbreviation == "ROM ADO"


def test_category_cannot_be_its_own_parent(client, librarian, category):
    form_page = client.get(reverse("catalog:category_edit", args=[category.pk]))
    parents = form_page.context["form"].fields["parent"].queryset
    assert category not in parents


def test_category_delete_keeps_records(client, librarian, category):
    """Supprimer une catégorie ne supprime aucun livre (SET_NULL)."""
    record = BibliographicRecord.objects.create(title="Fondation", category=category)
    resp = client.post(reverse("catalog:category_delete", args=[category.pk]))
    assert resp.status_code == 302
    record.refresh_from_db()
    assert record.category_id is None
    assert BibliographicRecord.objects.filter(pk=record.pk).exists()


def test_category_delete_page_announces_impact(client, librarian, category):
    BibliographicRecord.objects.create(title="Fondation", category=category)
    resp = client.get(reverse("catalog:category_delete", args=[category.pk]))
    assert resp.context["records_count"] == 1


def test_categories_are_reachable_from_advanced(client, librarian):
    body = client.get(reverse("core:advanced")).content.decode()
    assert reverse("catalog:category_list") in body


# ── Seed ───────────────────────────────────────────────────────────────────


def test_seed_sets_default_abbreviations():
    call_command("seed_defaults")
    assert Category.objects.get(code="EN ALB").abbreviation == "EN ALB"
    assert Category.objects.get(code="AD FIC").abbreviation == "AD FIC"


def test_seed_backfills_empty_abbreviation_on_existing():
    Category.objects.create(code="EN ALB", name="Enfants Album")
    call_command("seed_defaults")
    assert Category.objects.get(code="EN ALB").abbreviation == "EN ALB"


def test_seed_never_overwrites_a_hand_written_abbreviation():
    """Une cote ajustée par la bibliothèque doit survivre au redémarrage."""
    Category.objects.create(code="EN ALB", name="Enfants Album", abbreviation="ALB")
    call_command("seed_defaults")
    assert Category.objects.get(code="EN ALB").abbreviation == "ALB"


# ── Import Excel ───────────────────────────────────────────────────────────


def _import_job(user, headers, rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(list(headers))
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    upload = SimpleUploadedFile(
        "import.xlsx",
        buf.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    return ExcelCatalogJob.objects.create(
        mode=ExcelJobMode.IMPORT, uploaded_file=upload, created_by=user
    )


def test_import_sets_abbreviation_on_the_resolved_category(librarian):
    cat = Category.objects.create(code="ROM", name="Romans")
    job = _import_job(
        librarian,
        ["ISBN", "CATEGORY", "CATEGORY_ABBR"],
        [[VALID_ISBN, "Romans", "RO FI ADO"]],
    )
    run_import_job(job)
    cat.refresh_from_db()
    assert cat.abbreviation == "RO FI ADO"


def test_import_accepts_abbreviation_alias(librarian):
    cat = Category.objects.create(code="ROM", name="Romans")
    job = _import_job(
        librarian, ["ISBN", "CATEGORY", "ABREVIATION"], [[VALID_ISBN, "Romans", "RO"]]
    )
    run_import_job(job)
    cat.refresh_from_db()
    assert cat.abbreviation == "RO"


def test_import_reports_abbreviation_without_category(librarian):
    """Une cote sans catégorie n'a pas de cible : on le dit au lieu de la perdre."""
    job = _import_job(
        librarian, ["ISBN", "CATEGORY_ABBR"], [[VALID_ISBN, "RO FI ADO"]]
    )
    run_import_job(job)
    job.refresh_from_db()
    warnings = [e.get("warning", "") for e in job.report]
    assert any("CATEGORY_ABBR_ORPHAN" in w for w in warnings)


# ── Fiche notice ───────────────────────────────────────────────────────────


def test_record_detail_shows_the_abbreviation(client, librarian, category):
    record = BibliographicRecord.objects.create(title="Fondation", category=category)
    body = client.get(
        reverse("catalog:record_detail", args=[record.pk])
    ).content.decode()
    assert "RO FI ADO" in body
