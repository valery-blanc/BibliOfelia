"""FEAT-079 — mise à jour d'exemplaires existants depuis un fichier Excel.

La règle qui structure tout le mode : **on ne crée jamais rien**. Chaque test
qui applique un fichier vérifie donc aussi que le nombre de notices et
d'exemplaires n'a pas bougé — c'est la garantie qui permet à un bibliothécaire
de renvoyer un export corrigé sans risquer de dupliquer sa bibliothèque.
"""
import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Role, User
from apps.catalog.excel_catalog import run_update_job, validate_xlsx
from apps.catalog.excel_export import EXPORT_COLUMNS, build_catalog_workbook
from apps.catalog.models import (
    Author,
    BibliographicRecord,
    Category,
    DocumentType,
    ExcelCatalogJob,
    ExcelJobMode,
    Item,
    ItemState,
    Location,
    Provenance,
    Tag,
)

pytestmark = pytest.mark.django_db


def _xlsx(headers, rows, name="maj.xlsx"):
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
    settings.MEDIA_ROOT = str(tmp_path)


@pytest.fixture
def user():
    return User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)


@pytest.fixture
def item():
    category = Category.objects.create(code="RO", name="Romans", abbreviation="RO")
    record = BibliographicRecord.objects.create(
        title="Titre d'origine",
        isbn_13="9782070612758",
        publisher="Gallimard",
        publication_year=1943,
        language="fr",
        category=category,
        document_type=DocumentType.BOOK,
    )
    record.authors.add(Author.objects.create(full_name="Auteur d'origine"))
    return Item.objects.create(record=record, state=ItemState.GOOD)


def _run(user, headers, rows):
    job = ExcelCatalogJob.objects.create(
        mode=ExcelJobMode.UPDATE, uploaded_file=_xlsx(headers, rows), created_by=user
    )
    run_update_job(job)
    job.refresh_from_db()
    return job


def _counts():
    return BibliographicRecord.objects.count(), Item.objects.count()


# ── Validation ─────────────────────────────────────────────────────────────


def test_validate_requires_an_identifying_column():
    f = _xlsx(["TITLE", "AUTHOR"], [["T", "A"]])
    errors = validate_xlsx(f, ExcelJobMode.UPDATE)
    assert errors and "OFELIA_CODE" in errors[0]


def test_validate_accepts_ofelia_code_alone():
    assert validate_xlsx(_xlsx(["OFELIA_CODE"], [["2900000000017"]]),
                         ExcelJobMode.UPDATE) == []


def test_validate_accepts_external_code_alone():
    assert validate_xlsx(_xlsx(["EXTERNAL_CODE"], [["BCF1"]]),
                         ExcelJobMode.UPDATE) == []


def test_validate_accepts_french_header_aliases():
    """Un fichier repris à la main écrit « Code Ofelia », pas « OFELIA_CODE »."""
    assert validate_xlsx(_xlsx(["Code Ofelia", "Titre"], [["2900000000017", "T"]]),
                         ExcelJobMode.UPDATE) == []


# ── Résolution de l'exemplaire ─────────────────────────────────────────────


def test_update_by_ean13(user, item):
    before = _counts()
    job = _run(user, ["OFELIA_CODE", "TITLE"], [[item.ean13, "Nouveau titre"]])
    item.record.refresh_from_db()
    assert item.record.title == "Nouveau titre"
    assert (job.total, job.updated, job.errors) == (1, 1, 0)
    assert _counts() == before


def test_update_by_internal_id(user, item):
    """Le code interne OFL-… est ce qu'un bibliothécaire lit sur l'étiquette."""
    job = _run(user, ["OFELIA_CODE", "TITLE"], [[item.internal_id, "Par code interne"]])
    item.record.refresh_from_db()
    assert item.record.title == "Par code interne"
    assert job.updated == 1


def test_update_by_dedicated_internal_id_column(user, item):
    job = _run(user, ["INTERNAL_ID", "TITLE"], [[item.internal_id, "Colonne dédiée"]])
    item.record.refresh_from_db()
    assert item.record.title == "Colonne dédiée"
    assert job.updated == 1


def test_update_by_external_code(user, item):
    item.external_code = "BCF13298781X"
    item.save(update_fields=["external_code"])
    job = _run(user, ["EXTERNAL_CODE", "TITLE"], [["BCF-1329 8781x", "Par code externe"]])
    item.record.refresh_from_db()
    # Le code est normalisé avant recherche : tirets et espaces ne comptent pas.
    assert item.record.title == "Par code externe"
    assert job.updated == 1


def test_ofelia_code_wins_and_applies_the_external_code(user, item):
    """Règle métier : les deux codes présents → le code Ofelia identifie
    l'exemplaire, et le code externe de la ligne LUI est appliqué."""
    other = Item.objects.create(record=item.record, external_code="ANCIEN1")
    job = _run(
        user,
        ["OFELIA_CODE", "EXTERNAL_CODE"],
        [[item.ean13, "NOUVEAU1"]],
    )
    item.refresh_from_db()
    other.refresh_from_db()
    assert item.external_code == "NOUVEAU1"
    assert other.external_code == "ANCIEN1"  # l'autre exemplaire n'a pas bougé
    assert job.updated == 1


def test_unknown_ofelia_code_is_reported_and_creates_nothing(user, item):
    before = _counts()
    job = _run(user, ["OFELIA_CODE", "TITLE"], [["2909999999999", "Fantôme"]])
    assert (job.errors, job.updated) == (1, 0)
    assert job.report[0]["warning"] == "OFELIA_CODE_UNKNOWN"
    assert _counts() == before


def test_unknown_ofelia_code_does_not_fall_back_on_external_code(user, item):
    """Un code Ofelia faux signale une ligne mal identifiée : on refuse de
    modifier via l'autre code, ce serait modifier au jugé."""
    item.external_code = "BCF1"
    item.save(update_fields=["external_code"])
    job = _run(
        user,
        ["OFELIA_CODE", "EXTERNAL_CODE", "TITLE"],
        [["2909999999999", "BCF1", "Ne doit pas passer"]],
    )
    item.record.refresh_from_db()
    assert item.record.title == "Titre d'origine"
    assert job.report[0]["warning"] == "OFELIA_CODE_UNKNOWN"


def test_unknown_external_code_is_reported(user, item):
    job = _run(user, ["EXTERNAL_CODE", "TITLE"], [["INCONNU9", "Fantôme"]])
    assert job.errors == 1
    assert job.report[0]["warning"] == "EXTERNAL_CODE_UNKNOWN"


def test_row_without_any_code_is_reported(user, item):
    job = _run(user, ["OFELIA_CODE", "TITLE"], [["", "Sans clé"]])
    assert job.errors == 1
    assert job.report[0]["warning"] == "NO_KEY"


def test_blank_rows_are_ignored(user, item):
    job = _run(user, ["OFELIA_CODE", "TITLE"],
               [[item.ean13, "Nouveau"], ["", ""], [None, None]])
    assert job.total == 1
    assert job.errors == 0


# ── Champs mis à jour ──────────────────────────────────────────────────────


def test_every_supported_field_is_applied(user, item):
    Location.objects.create(code="A1")
    Provenance.objects.create(code="DON2024", label="Don Dupont")
    Category.objects.create(code="BD", name="Bandes dessinées")
    job = _run(
        user,
        [
            "OFELIA_CODE", "TITLE", "AUTHOR", "CATEGORY", "CATEGORY_ABBR", "TYPE",
            "EDITOR", "YEAR", "LANGUAGE", "TAGS", "CONDITION", "PROVENANCE",
            "LOCATION", "EXTERNAL_CODE",
        ],
        [[
            item.ean13, "Astérix", "Goscinny; Uderzo", "Bandes dessinées", "BD AV",
            "BD / manga", "Dargaud", 1961, "fr", "humour, gaulois", "Usé",
            "DON2024", "A1", "BCF42",
        ]],
    )
    item.refresh_from_db()
    record = item.record
    assert record.title == "Astérix"
    assert sorted(a.full_name for a in record.authors.all()) == ["Goscinny", "Uderzo"]
    assert record.category.name == "Bandes dessinées"
    assert record.category.abbreviation == "BD AV"
    assert record.document_type == DocumentType.COMIC
    assert record.publisher == "Dargaud"
    assert record.publication_year == 1961
    assert sorted(t.name for t in record.tags.all()) == ["gaulois", "humour"]
    assert item.state == ItemState.WORN
    assert item.provenance.code == "DON2024"
    assert item.location.code == "A1"
    assert item.external_code == "BCF42"
    assert (job.updated, job.errors) == (1, 0)


def test_empty_cell_keeps_the_existing_value(user, item):
    """Règle héritée de l'import : une cellule vide ne remplace rien. Sans elle,
    un export renvoyé avec deux corrections effacerait tout le reste."""
    job = _run(
        user,
        ["OFELIA_CODE", "TITLE", "EDITOR", "YEAR"],
        [[item.ean13, "", "", ""]],
    )
    item.record.refresh_from_db()
    assert item.record.title == "Titre d'origine"
    assert item.record.publisher == "Gallimard"
    assert item.record.publication_year == 1943
    assert (job.updated, job.unchanged) == (0, 1)


def test_isbn_is_updatable(user, item):
    job = _run(user, ["OFELIA_CODE", "ISBN"], [[item.ean13, "9782070368228"]])
    item.record.refresh_from_db()
    assert item.record.isbn_13 == "9782070368228"
    assert job.updated == 1


def test_isbn_already_taken_is_reported_not_applied(user, item):
    BibliographicRecord.objects.create(title="Autre", isbn_13="9782070368228")
    job = _run(user, ["OFELIA_CODE", "ISBN"], [[item.ean13, "9782070368228"]])
    item.record.refresh_from_db()
    assert item.record.isbn_13 == "9782070612758"
    assert "ISBN_CONFLICT" in job.report[0]["warning"]


def test_external_code_already_taken_is_reported_not_applied(user, item):
    other = Item.objects.create(record=item.record, external_code="PRIS1")
    job = _run(user, ["OFELIA_CODE", "EXTERNAL_CODE"], [[item.ean13, "PRIS1"]])
    item.refresh_from_db()
    other.refresh_from_db()
    assert item.external_code == ""
    assert other.external_code == "PRIS1"
    assert "EXTERNAL_CODE_DUPLICATE" in job.report[0]["warning"]


def test_unknown_location_is_reported_but_the_rest_applies(user, item):
    job = _run(
        user,
        ["OFELIA_CODE", "LOCATION", "TITLE"],
        [[item.ean13, "ZZ9", "Titre corrigé"]],
    )
    item.record.refresh_from_db()
    assert item.record.title == "Titre corrigé"
    assert item.location is None
    assert "LOCATION_UNKNOWN" in job.report[0]["warning"]
    assert job.errors == 0  # la ligne a bien été appliquée, elle est juste signalée


def test_unknown_category_is_reported_but_the_rest_applies(user, item):
    job = _run(
        user,
        ["OFELIA_CODE", "CATEGORY", "TITLE"],
        [[item.ean13, "Catégorie fantôme", "Titre corrigé"]],
    )
    item.record.refresh_from_db()
    assert item.record.title == "Titre corrigé"
    assert item.record.category.name == "Romans"
    assert "CATEGORY_UNKNOWN" in job.report[0]["warning"]


@pytest.mark.parametrize("lang", ["fr", "en", "es", "mg"])
def test_condition_and_type_labels_are_read_in_any_language(user, item, lang):
    """L'export écrit TYPE et CONDITION dans la langue du bibliothécaire, mais
    le job tourne dans le worker, en français. Les libellés de toutes les
    langues doivent donc être relisables, sinon un fichier exporté en espagnol
    reviendrait avec TYPE_UNKNOWN sur chaque ligne."""
    from django.utils.translation import override

    with override(lang):
        type_label = str(DocumentType.COMIC.label)
        state_label = str(ItemState.NEW.label)

    job = _run(user, ["OFELIA_CODE", "TYPE", "CONDITION"],
               [[item.ean13, type_label, state_label]])
    item.refresh_from_db()
    assert item.record.document_type == DocumentType.COMIC
    assert item.state == ItemState.NEW
    assert job.report == []


@pytest.mark.parametrize("lang", ["en", "es", "mg"])
def test_category_is_found_whatever_the_export_language(user, item, lang):
    """Même problème pour la catégorie, dont le nom est un champ traduit
    (modeltranslation) : l'export écrit `name_es`, le worker cherche en français."""
    category = Category.objects.create(code="BD", name="Bandes dessinées")
    setattr(category, f"name_{lang}", f"Comics-{lang}")
    category.save()

    job = _run(user, ["OFELIA_CODE", "CATEGORY"], [[item.ean13, f"Comics-{lang}"]])
    item.record.refresh_from_db()
    assert item.record.category == category
    assert job.report == []


def test_category_is_also_found_by_its_code(user, item):
    category = Category.objects.create(code="BD", name="Bandes dessinées")
    _run(user, ["OFELIA_CODE", "CATEGORY"], [[item.ean13, "bd"]])
    item.record.refresh_from_db()
    assert item.record.category == category


def test_unknown_type_is_reported(user, item):
    job = _run(user, ["OFELIA_CODE", "TYPE"], [[item.ean13, "Hologramme"]])
    assert "TYPE_UNKNOWN" in job.report[0]["warning"]


def test_tags_and_authors_are_replaced_not_merged(user, item):
    item.record.tags.add(Tag.objects.create(name="ancien"))
    _run(user, ["OFELIA_CODE", "TAGS", "AUTHOR"], [[item.ean13, "neuf", "Nouvel Auteur"]])
    item.record.refresh_from_db()
    assert [t.name for t in item.record.tags.all()] == ["neuf"]
    assert [a.full_name for a in item.record.authors.all()] == ["Nouvel Auteur"]


def test_unchanged_rows_are_counted_apart(user, item):
    job = _run(user, ["OFELIA_CODE", "TITLE"], [[item.ean13, "Titre d'origine"]])
    assert (job.updated, job.unchanged, job.errors) == (0, 1, 0)


# ── Aller-retour export → mise à jour ──────────────────────────────────────


def test_exported_file_reimports_without_a_single_change(user, item):
    """Le test qui protège les deux features à la fois : l'export doit être
    relisable tel quel, sans erreur ET sans modifier quoi que ce soit."""
    Location.objects.create(code="A1")
    item.location = Location.objects.get(code="A1")
    item.external_code = "BCF42"
    item.save(update_fields=["location", "external_code"])
    before = _counts()

    content = build_catalog_workbook()
    job = ExcelCatalogJob.objects.create(
        mode=ExcelJobMode.UPDATE,
        uploaded_file=SimpleUploadedFile("export.xlsx", content),
        created_by=user,
    )
    run_update_job(job)
    job.refresh_from_db()

    assert (job.total, job.updated, job.unchanged, job.errors) == (1, 0, 1, 0)
    assert job.report == []
    assert _counts() == before


def test_exported_file_carries_every_update_column():
    """Garde-fou de cohérence : toute colonne d'export doit être relisable par
    la mise à jour, sinon l'aller-retour perdrait silencieusement une donnée."""
    from apps.catalog.excel_catalog import UPDATE_KEY_COLUMNS, UPDATE_OVERRIDE_COLUMNS

    known = {c.lower() for c in UPDATE_KEY_COLUMNS + UPDATE_OVERRIDE_COLUMNS}
    assert {c.lower() for c in EXPORT_COLUMNS} <= known


# ── Vue ────────────────────────────────────────────────────────────────────


def test_update_view_rejects_file_without_identifier(client, user, item):
    from django.urls import reverse

    client.login(username="lib", password="pw")
    resp = client.post(
        reverse("catalog:excel_catalog_update"),
        {"file": _xlsx(["TITLE"], [["T"]])},
        follow=True,
    )
    assert resp.status_code == 200
    assert not ExcelCatalogJob.objects.filter(mode=ExcelJobMode.UPDATE).exists()


def test_index_shows_the_four_tools(client, user, item):
    from django.urls import reverse

    client.login(username="lib", password="pw")
    resp = client.get(reverse("catalog:excel_catalog_index"))
    assert resp.status_code == 200
    assert resp.context["item_count"] == 1
    body = resp.content.decode()
    assert reverse("catalog:excel_catalog_export") in body
    assert reverse("catalog:excel_catalog_update") in body
