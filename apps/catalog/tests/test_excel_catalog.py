"""FEAT-050 — catalogage Excel (vérification + import)."""
import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Role, User
from apps.catalog import excel_catalog
from apps.catalog.excel_catalog import (
    run_import_job,
    run_verify_job,
    validate_xlsx,
)
from apps.catalog.models import (
    Category,
    ExcelCatalogJob,
    ExcelJobMode,
    Item,
    Location,
    ScanItem,
    ScanSession,
)

pytestmark = pytest.mark.django_db

VALID_ISBN = "9782070368228"


def _xlsx(headers, rows, name="inventaire.xlsx"):
    """Construit un SimpleUploadedFile .xlsx en mémoire."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(list(headers))
    for row in rows:
        ws.append(list(row))
    buf = io.BytesIO()
    wb.save(buf)
    return SimpleUploadedFile(
        name,
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    """Isole les uploads/result_file dans un dossier temporaire."""
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def user():
    return User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)


# ── Validation ─────────────────────────────────────────────────────────────


def test_validate_xlsx_rejects_xls():
    f = SimpleUploadedFile("old.xls", b"garbage", content_type="application/vnd.ms-excel")
    errors = validate_xlsx(f, ExcelJobMode.VERIFY)
    assert errors and "xlsx" in errors[0].lower()


def test_validate_xlsx_rejects_oversized(monkeypatch):
    monkeypatch.setattr(excel_catalog, "MAX_FILE_BYTES", 10)
    f = _xlsx(["ID", "TITLE", "AUTHOR", "ISBN"], [["1", "T", "A", VALID_ISBN]])
    errors = validate_xlsx(f, ExcelJobMode.VERIFY)
    assert any("Mo" in e for e in errors)


def test_validate_xlsx_requires_columns_verify():
    f = _xlsx(["ID", "AUTHOR", "ISBN"], [["1", "A", VALID_ISBN]])  # TITLE manquant
    errors = validate_xlsx(f, ExcelJobMode.VERIFY)
    assert any("TITLE" in e for e in errors)


def test_validate_xlsx_requires_columns_import():
    f = _xlsx(["ID", "TITLE"], [["1", "T"]])  # ISBN manquant
    errors = validate_xlsx(f, ExcelJobMode.IMPORT)
    assert any("ISBN" in e for e in errors)


def test_validate_xlsx_accents_tolerated():
    # En-têtes accentués / casse mixte → normalisés.
    f = _xlsx(["Id", "Titre", "Author", "Isbn"], [["1", "T", "A", VALID_ISBN]])
    errors = validate_xlsx(f, ExcelJobMode.IMPORT)
    assert errors == []  # ISBN présent (insensible casse)


# ── Mode VERIFY ────────────────────────────────────────────────────────────


def _make_verify_job(user, headers, rows):
    f = _xlsx(headers, rows)
    return ExcelCatalogJob.objects.create(
        mode=ExcelJobMode.VERIFY, uploaded_file=f, created_by=user
    )


def _read_result(job):
    wb = openpyxl.load_workbook(job.result_file.path)
    ws = wb.active
    headers = [c.value for c in ws[1]]
    data = [[c.value for c in row] for row in ws.iter_rows(min_row=2)]
    return headers, data


def test_verify_job_pass1_only(user, monkeypatch):
    monkeypatch.setattr(
        excel_catalog,
        "_pass1_by_isbn",
        lambda isbn: ({"title": "Vrai Titre", "authors_text": "Vrai Auteur", "source": "bnf"}, False),
    )
    monkeypatch.setattr(excel_catalog, "_search_all", lambda title, author: ([], False))
    job = _make_verify_job(user, ["ID", "TITLE", "AUTHOR", "ISBN"],
                           [["1", "Saisi", "Saisi", VALID_ISBN]])
    run_verify_job(job)
    assert job.matched_by_isbn == 1
    assert job.not_found == 0
    headers, data = _read_result(job)
    assert "TITLE_FOUND_BY_ISBN" in headers
    col = headers.index("TITLE_FOUND_BY_ISBN")
    assert data[0][col] == "Vrai Titre"


def test_verify_job_pass2_runs_even_with_isbn(user, monkeypatch):
    """La passe 2 (titre+auteur) tourne même quand l'ISBN a résolu la ligne :
    permet de recouper un ISBN saisi à la main."""
    monkeypatch.setattr(
        excel_catalog,
        "_pass1_by_isbn",
        lambda isbn: ({"title": "Le Petit Prince", "authors_text": "Saint-Exupéry", "source": "bnf"}, False),
    )
    monkeypatch.setattr(
        excel_catalog,
        "_search_all",
        lambda title, author: ([
            {"title": "Le Petit Prince", "authors_text": "Antoine de Saint-Exupéry",
             "isbn_13": "9782070408504", "isbn_10": ""},
        ], False),
    )
    # ISBN saisi (VALID_ISBN) ≠ ISBN trouvé par titre+auteur → recoupement.
    job = _make_verify_job(user, ["ID", "TITLE", "AUTHOR", "ISBN"],
                           [["1", "Le Petit Prince", "Saint-Exupéry", VALID_ISBN]])
    run_verify_job(job)
    assert job.matched_by_isbn == 1
    assert job.matched_by_ta == 1  # passe 2 a aussi tourné
    headers, data = _read_result(job)
    col = headers.index("ISBN_FOUND_BY_TA")
    assert data[0][col] == "9782070408504"


def test_verify_job_pass2_fuzzy_match(user, monkeypatch):
    monkeypatch.setattr(excel_catalog, "_pass1_by_isbn", lambda isbn: (None, False))
    monkeypatch.setattr(
        excel_catalog,
        "_search_all",
        lambda title, author: ([
            {"title": "Le Petit Prince", "authors_text": "Antoine de Saint-Exupéry",
             "isbn_13": VALID_ISBN, "isbn_10": ""},
        ], False),
    )
    # Ligne sans ISBN, titre avec faute de frappe → doit matcher (score > 60).
    job = _make_verify_job(user, ["ID", "TITLE", "AUTHOR", "ISBN"],
                           [["1", "Le Petit Pince", "Saint Exupery", ""]])
    run_verify_job(job)
    assert job.matched_by_ta == 1
    assert job.not_found == 0
    headers, data = _read_result(job)
    col = headers.index("ISBN_FOUND_BY_TA")
    assert data[0][col] == VALID_ISBN


def test_verify_job_pass2_low_score_skipped(user, monkeypatch):
    monkeypatch.setattr(excel_catalog, "_pass1_by_isbn", lambda isbn: (None, False))
    monkeypatch.setattr(
        excel_catalog,
        "_search_all",
        lambda title, author: ([
            {"title": "Un livre totalement différent zzz", "authors_text": "Quelqu'un d'autre",
             "isbn_13": "9780000000000", "isbn_10": ""},
        ], False),
    )
    job = _make_verify_job(user, ["ID", "TITLE", "AUTHOR", "ISBN"],
                           [["1", "Mon titre unique abc", "Moi", ""]])
    run_verify_job(job)
    assert job.matched_by_ta == 0
    assert job.not_found == 1
    headers, data = _read_result(job)
    col = headers.index("ISBN_FOUND_BY_TA")
    assert not data[0][col]  # rien écrit


# ── Mode IMPORT ────────────────────────────────────────────────────────────


def _make_import_job(user, headers, rows):
    f = _xlsx(headers, rows)
    return ExcelCatalogJob.objects.create(
        mode=ExcelJobMode.IMPORT, uploaded_file=f, created_by=user
    )


def test_import_job_creates_scan_session_and_items(user):
    job = _make_import_job(user, ["ISBN"], [[VALID_ISBN], ["9782266283434"]])
    run_import_job(job)
    job.refresh_from_db()
    assert job.scan_session is not None
    assert ScanItem.objects.filter(session=job.scan_session).count() == 2
    # finalize_scan_session a matérialisé les notices + exemplaires.
    assert Item.objects.count() == 2


def test_import_job_resolves_location_and_category(user):
    Location.objects.create(code="A1")
    cat = Category.objects.create(code="ROM", name="Roman")
    job = _make_import_job(user, ["ISBN", "LOCATION", "CATEGORY"],
                           [[VALID_ISBN, "A1", "Roman"]])
    run_import_job(job)
    item = ScanItem.objects.get(session=job.scan_session)
    assert item.location_code == "A1"
    assert item.category_id == cat.pk


def test_import_job_skips_invalid_isbn(user):
    job = _make_import_job(user, ["ISBN"], [["not-an-isbn"], [VALID_ISBN]])
    run_import_job(job)
    job.refresh_from_db()
    assert job.errors == 1
    assert ScanItem.objects.filter(session=job.scan_session).count() == 1
    assert any(e.get("warning") == "ISBN_INVALID" for e in job.report)


def test_import_job_unknown_location_warns(user):
    job = _make_import_job(user, ["ISBN", "LOCATION"], [[VALID_ISBN, "ZZ9"]])
    run_import_job(job)
    job.refresh_from_db()
    item = ScanItem.objects.get(session=job.scan_session)
    assert item.location_code == ""  # emplacement inconnu ignoré
    assert any("LOCATION_UNKNOWN" in e.get("warning", "") for e in job.report)


def test_index_page_renders(client, user):
    client.force_login(user)
    from django.urls import reverse

    resp = client.get(reverse("catalog:excel_catalog_index"))
    assert resp.status_code == 200
    assert b"Catalogage Excel" in resp.content


def test_detail_page_renders(client, user):
    client.force_login(user)
    from django.urls import reverse

    job = ExcelCatalogJob.objects.create(mode=ExcelJobMode.VERIFY, created_by=user)
    resp = client.get(reverse("catalog:excel_catalog_detail", args=[job.pk]))
    assert resp.status_code == 200


def test_detail_other_user_redirects(client):
    other = User.objects.create_user(username="other", password="pw", role=Role.LIBRARIAN)
    owner = User.objects.create_user(username="owner", password="pw", role=Role.LIBRARIAN)
    job = ExcelCatalogJob.objects.create(mode=ExcelJobMode.VERIFY, created_by=owner)
    client.force_login(other)
    from django.urls import reverse

    resp = client.get(reverse("catalog:excel_catalog_detail", args=[job.pk]))
    assert resp.status_code == 302  # pas le propriétaire → renvoyé à l'index


def test_import_job_idempotent_on_local_id(user):
    job = _make_import_job(user, ["ISBN"], [[VALID_ISBN]])
    run_import_job(job)
    job.refresh_from_db()
    count_after_first = ScanItem.objects.filter(session=job.scan_session).count()
    # Ré-exécution sur la même session (même job) → pas de doublon.
    run_import_job(job)
    assert ScanItem.objects.filter(session=job.scan_session).count() == count_after_first
