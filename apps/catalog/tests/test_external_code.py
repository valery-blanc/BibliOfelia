"""FEAT-063 — code Ofelia externe : normalisation, résolution, saisie, import."""
from __future__ import annotations

import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.catalog.excel_catalog import run_import_job
from apps.catalog.lookup import (
    find_item,
    is_valid_external_code,
    normalize_external_code,
)
from apps.catalog.models import (
    BibliographicRecord,
    ExcelCatalogJob,
    ExcelJobMode,
    Item,
)

pytestmark = pytest.mark.django_db

VALID_ISBN = "9782070368228"


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture
def record():
    return BibliographicRecord.objects.create(title="Fondation")


@pytest.fixture
def item(record):
    return Item.objects.create(record=record, external_code="BCF13298781X")


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


# ── Normalisation et validation ────────────────────────────────────────────


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("BCF13298781X", "BCF13298781X"),
        ("bcf13298781x", "BCF13298781X"),
        ("BCF-1329 8781.X", "BCF13298781X"),
        ("  bcf 1329 8781 x  ", "BCF13298781X"),
        ("", ""),
    ],
)
def test_normalize_external_code(raw, expected):
    """Saisie clavier et lecture douchette doivent converger sur la même chaîne."""
    assert normalize_external_code(raw) == expected


@pytest.mark.parametrize(
    "code,valid",
    [
        ("BCF13298781X", True),
        ("12345", True),
        ("A" * 20, True),
        ("A" * 21, False),    # 20 caractères au maximum
        ("BCF/1329", False),  # la barre oblique n'est pas retirée par la normalisation
        ("", False),
    ],
)
def test_is_valid_external_code(code, valid):
    assert is_valid_external_code(code) is valid


# ── Unicité en base ────────────────────────────────────────────────────────


def test_external_code_must_be_unique(record, item):
    """Deux exemplaires avec le même code rendraient tout scan ambigu."""
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Item.objects.create(record=record, external_code="BCF13298781X")


def test_several_items_without_external_code_are_allowed(record):
    """L'unicité est partielle : le code reste facultatif."""
    Item.objects.create(record=record)
    Item.objects.create(record=record)
    assert Item.objects.filter(external_code="").count() == 2


# ── Résolution d'un code ───────────────────────────────────────────────────


def test_find_item_by_ofelia_code(item):
    assert find_item(item.ean13) == item


def test_find_item_by_external_code(item):
    assert find_item("bcf-1329 8781x") == item


def test_find_item_returns_none_for_unknown_code(item):
    assert find_item("ZZZZ9999") is None
    assert find_item("") is None


def test_find_item_ignores_free_text(item, django_assert_num_queries):
    """Du texte libre ne peut pas être un code : inutile d'interroger la base."""
    with django_assert_num_queries(0):
        assert find_item("les misérables de victor hugo") is None


def test_ofelia_code_wins_over_external_code(record, item):
    """Un code externe qui imite un code Ofelia ne détourne pas le scan."""
    other = Item.objects.create(record=record)
    other.external_code = item.ean13
    other.save(update_fields=["external_code"])
    assert find_item(item.ean13) == item


def test_find_item_by_internal_id(item):
    """BUG-044 : le code interne OFL-… doit résoudre comme à la MAJ Excel."""
    assert item.internal_id.startswith("OFL-")
    assert find_item(item.internal_id) == item
    assert find_item(item.internal_id.lower()) == item
    compact = item.internal_id.replace("-", "")
    assert find_item(compact) == item


# ── Saisie dans le formulaire d'exemplaire ─────────────────────────────────


def _item_post(**overrides):
    data = {
        "external_code": "",
        "state": "good",
        "acquisition_date": "2026-08-19",
        "acquisition_source": "unknown",
        "donor": "",
        "notes": "",
    }
    data.update(overrides)
    return data


def test_item_form_normalizes_code(client, librarian, item):
    resp = client.post(
        reverse("catalog:item_edit", args=[item.pk]),
        _item_post(external_code="abc-123 456"),
    )
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.external_code == "ABC123456"


def test_item_form_rejects_code_already_taken(client, librarian, record, item):
    other = Item.objects.create(record=record)
    resp = client.post(
        reverse("catalog:item_edit", args=[other.pk]),
        _item_post(external_code="BCF13298781X"),
    )
    assert resp.status_code == 200  # ré-affichage du formulaire en erreur
    other.refresh_from_db()
    assert other.external_code == ""
    assert "déjà porté" in resp.content.decode()


def test_item_form_rejects_invalid_code(client, librarian, item):
    resp = client.post(
        reverse("catalog:item_edit", args=[item.pk]),
        _item_post(external_code="A" * 25),
    )
    assert resp.status_code == 200
    item.refresh_from_db()
    assert item.external_code == "BCF13298781X"


def test_bulk_create_refuses_code_on_several_copies(client, librarian, record):
    resp = client.post(
        reverse("catalog:item_create", args=[record.pk]),
        _item_post(copies=3, external_code="ABC123"),
    )
    assert resp.status_code == 200
    assert Item.objects.count() == 0


def test_bulk_create_accepts_code_on_single_copy(client, librarian, record):
    resp = client.post(
        reverse("catalog:item_create", args=[record.pk]),
        _item_post(copies=1, external_code="abc123"),
    )
    assert resp.status_code == 302
    assert Item.objects.get().external_code == "ABC123"


# ── Recherche ──────────────────────────────────────────────────────────────


def test_global_search_finds_record_by_external_code(client, librarian, item):
    resp = client.get(reverse("core:search"), {"q": "bcf-13298781x"})
    assert resp.status_code == 302
    assert resp.url == reverse("catalog:record_detail", args=[item.record_id])


def test_catalog_search_finds_record_by_external_code(client, librarian, item):
    resp = client.get(reverse("catalog:record_list"), {"q": "BCF13298781X"})
    assert list(resp.context["page_obj"]) == [item.record]


def test_catalog_search_unknown_item_code_returns_nothing(client, librarian, item):
    """Un code d'exemplaire inconnu ne doit pas retomber en plein texte."""
    resp = client.get(reverse("catalog:record_list"), {"q": "2900000000000"})
    assert list(resp.context["page_obj"]) == []


# ── Récolement ─────────────────────────────────────────────────────────────


def test_inventory_scan_accepts_external_code(item):
    """Le pointage est stocké sous le code Ofelia, quelle que soit l'étiquette lue."""
    from apps.inventory.models import InventorySession
    from apps.inventory.services import record_scan

    session = InventorySession.objects.create(label="Récolement")
    scan, created = record_scan(session, "bcf 1329 8781 x")
    assert created is True
    assert scan.item == item
    assert scan.ean13 == item.ean13


def test_inventory_scan_same_book_twice_counts_once(item):
    """Scanner l'étiquette Ofelia puis l'étiquette externe = un seul pointage."""
    from apps.inventory.models import InventorySession
    from apps.inventory.services import record_scan

    session = InventorySession.objects.create(label="Récolement")
    record_scan(session, item.ean13)
    _scan, created = record_scan(session, "BCF13298781X")
    assert created is False
    assert session.scans.count() == 1


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


def test_import_assigns_external_code(librarian):
    job = _import_job(librarian, ["ISBN", "EXTERNAL_CODE"], [[VALID_ISBN, "bcf-1329"]])
    run_import_job(job)
    assert Item.objects.get().external_code == "BCF1329"


def test_import_accepts_column_alias(librarian):
    job = _import_job(librarian, ["ISBN", "CODE EXTERNE"], [[VALID_ISBN, "XYZ42"]])
    run_import_job(job)
    assert Item.objects.get().external_code == "XYZ42"


def test_import_reports_duplicate_external_code(librarian):
    job = _import_job(
        librarian,
        ["ISBN", "EXTERNAL_CODE"],
        [[VALID_ISBN, "DUP1"], ["9782266283434", "dup 1"]],
    )
    run_import_job(job)
    job.refresh_from_db()
    warnings = [e.get("warning", "") for e in job.report]
    assert any("EXTERNAL_CODE_DUPLICATE" in w for w in warnings)
    # La 1re ligne garde le code, la 2e est importée sans code.
    assert Item.objects.filter(external_code="DUP1").count() == 1
    assert Item.objects.filter(external_code="").count() == 1


def test_import_reports_invalid_external_code(librarian):
    job = _import_job(librarian, ["ISBN", "EXTERNAL_CODE"], [[VALID_ISBN, "A" * 30]])
    run_import_job(job)
    job.refresh_from_db()
    warnings = [e.get("warning", "") for e in job.report]
    assert any("EXTERNAL_CODE_INVALID" in w for w in warnings)
    assert Item.objects.get().external_code == ""


def test_import_does_not_steal_a_code_already_used(librarian, item):
    """Un code déjà porté par un exemplaire du catalogue n'est pas réattribué."""
    job = _import_job(
        librarian, ["ISBN", "EXTERNAL_CODE"], [[VALID_ISBN, "BCF13298781X"]]
    )
    run_import_job(job)
    job.refresh_from_db()
    warnings = [e.get("warning", "") for e in job.report]
    assert any("EXTERNAL_CODE_DUPLICATE" in w for w in warnings)
    assert Item.objects.filter(external_code="BCF13298781X").count() == 1
