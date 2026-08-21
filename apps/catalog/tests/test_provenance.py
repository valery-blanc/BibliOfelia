"""FEAT-064 — provenance des exemplaires + recherche par exemplaire."""
from __future__ import annotations

import io

import openpyxl
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.catalog.excel_catalog import run_import_job
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    ExcelCatalogJob,
    ExcelJobMode,
    Item,
    Provenance,
    RetiredItemCode,
    ScanItem,
    ScanKind,
    ScanSession,
)

pytestmark = pytest.mark.django_db

VALID_ISBN = "9782070368228"


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture
def superadmin(client):
    user = User.objects.create_user(username="boss", password="pw", role=Role.SUPERADMIN)
    client.force_login(user)
    return user


@pytest.fixture
def ofelia():
    return Provenance.objects.create(code="OFELIA", label="Acheté par Ofelia")


@pytest.fixture
def borrowed():
    return Provenance.objects.create(code="BM-GE", label="Prêt Bibliothèque de Genève")


@pytest.fixture
def record():
    return BibliographicRecord.objects.create(title="Fondation")


@pytest.fixture(autouse=True)
def _tmp_media(settings, tmp_path):
    settings.MEDIA_ROOT = str(tmp_path)


# ── Modèle ─────────────────────────────────────────────────────────────────


def test_provenance_str_is_the_full_name(ofelia):
    """Le nom complet se suffit : répéter le code devant allonge pour rien."""
    assert str(ofelia) == "Acheté par Ofelia"


def test_provenance_str_falls_back_to_the_code(ofelia):
    """Sans nom saisi, le code reste le seul repère lisible."""
    assert str(Provenance.objects.create(code="DON")) == "DON"


# ── Écran de gestion ───────────────────────────────────────────────────────


def test_provenance_list_shows_item_count(client, librarian, ofelia, record):
    Item.objects.create(record=record, provenance=ofelia)
    resp = client.get(reverse("catalog:provenance_list"))
    assert resp.status_code == 200
    assert resp.context["provenances"][0].items_count == 1


def test_provenance_create(client, librarian):
    resp = client.post(
        reverse("catalog:provenance_create"),
        {"code": "DON-DUPONT", "label": "Don famille Dupont", "notes": ""},
    )
    assert resp.status_code == 302
    assert Provenance.objects.get(code="DON-DUPONT").label == "Don famille Dupont"


def test_provenance_edit(client, librarian, ofelia):
    client.post(
        reverse("catalog:provenance_edit", args=[ofelia.pk]),
        {"code": "OFELIA", "label": "Fonds propre", "notes": ""},
    )
    ofelia.refresh_from_db()
    assert ofelia.label == "Fonds propre"


def test_provenance_delete_refused_while_items_use_it(client, librarian, ofelia, record):
    """Effacer une provenance en service perdrait l'origine des exemplaires."""
    Item.objects.create(record=record, provenance=ofelia)
    resp = client.post(reverse("catalog:provenance_delete", args=[ofelia.pk]))
    assert resp.status_code == 302
    assert Provenance.objects.filter(pk=ofelia.pk).exists()


def test_provenance_delete_allowed_when_unused(client, librarian, ofelia):
    resp = client.post(reverse("catalog:provenance_delete", args=[ofelia.pk]))
    assert resp.status_code == 302
    assert not Provenance.objects.filter(pk=ofelia.pk).exists()


def test_provenance_confirm_page_lists_blocking_items(client, librarian, ofelia, record):
    Item.objects.create(record=record, provenance=ofelia)
    resp = client.get(reverse("catalog:provenance_delete", args=[ofelia.pk]))
    assert resp.status_code == 200
    assert resp.context["items_count"] == 1


# ── Affectation en masse au catalogage ─────────────────────────────────────


def test_scan_session_default_provenance_applies_to_copies(librarian, borrowed):
    """Les exemplaires d'un lot héritent de la provenance du lot."""
    from apps.api.services import finalize_scan_session

    session = ScanSession.objects.create(
        label="Dépôt Genève", created_by=librarian, default_provenance=borrowed
    )
    ScanItem.objects.create(
        session=session,
        local_id="a",
        scan_kind=ScanKind.EAN13,
        scanned_value=VALID_ISBN,
        copy_count=2,
        scanned_at=timezone.now(),
    )
    finalize_scan_session(session)
    assert Item.objects.count() == 2
    assert all(it.provenance_id == borrowed.pk for it in Item.objects.all())


def test_scan_session_form_offers_provenance(client, librarian, borrowed):
    resp = client.get(reverse("catalog:scan_session_create"))
    assert "default_provenance" in resp.context["form"].fields
    resp = client.post(
        reverse("catalog:scan_session_create"),
        {
            "label": "Dépôt",
            "default_category": "",
            "default_location": "",
            "default_provenance": borrowed.pk,
        },
    )
    assert resp.status_code == 302
    assert ScanSession.objects.get(label="Dépôt").default_provenance_id == borrowed.pk


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


def test_import_resolves_provenance_by_code(librarian, borrowed):
    job = _import_job(librarian, ["ISBN", "PROVENANCE"], [[VALID_ISBN, "BM-GE"]])
    run_import_job(job)
    assert Item.objects.get().provenance_id == borrowed.pk


def test_import_resolves_provenance_by_label(librarian, borrowed):
    job = _import_job(
        librarian, ["ISBN", "PROVENANCE"], [[VALID_ISBN, "Prêt Bibliothèque de Genève"]]
    )
    run_import_job(job)
    assert Item.objects.get().provenance_id == borrowed.pk


def test_import_reports_unknown_provenance(librarian):
    job = _import_job(librarian, ["ISBN", "PROVENANCE"], [[VALID_ISBN, "INCONNUE"]])
    run_import_job(job)
    job.refresh_from_db()
    warnings = [e.get("warning", "") for e in job.report]
    assert any("PROVENANCE_UNKNOWN" in w for w in warnings)
    assert Item.objects.get().provenance_id is None


# ── Recherche par exemplaire ───────────────────────────────────────────────


def test_items_mode_returns_one_row_per_copy(client, librarian, record):
    for _ in range(3):
        Item.objects.create(record=record)
    resp = client.get(reverse("catalog:record_list"), {"mode": "items"})
    assert resp.context["items_mode"] is True
    assert len(resp.context["page_obj"].object_list) == 3
    assert resp.context["total"] == 3


def test_record_mode_still_returns_one_row_per_record(client, librarian, record):
    for _ in range(3):
        Item.objects.create(record=record)
    resp = client.get(reverse("catalog:record_list"))
    assert resp.context["items_mode"] is False
    assert list(resp.context["page_obj"]) == [record]


def test_items_mode_table_swaps_copy_count_for_item_columns(client, librarian, record):
    Item.objects.create(record=record, external_code="BCF1", provenance=None)
    body = client.get(reverse("catalog:record_list"), {"mode": "items"}).content.decode()
    assert "Code Ofelia externe" in body
    assert "BCF1" in body
    # La colonne « Ex. » (nombre d'exemplaires) n'a plus de sens ligne à ligne.
    assert ">Ex.<" not in body


def test_items_mode_filters_on_provenance(client, librarian, record, ofelia, borrowed):
    """Le cas qui motive la feature : deux exemplaires du même titre, deux origines."""
    Item.objects.create(record=record, provenance=ofelia)
    lent = Item.objects.create(record=record, provenance=borrowed)
    resp = client.get(
        reverse("catalog:record_list"), {"mode": "items", "provenance": borrowed.pk}
    )
    assert list(resp.context["page_obj"]) == [lent]


def test_record_mode_provenance_filter_keeps_records_with_one_matching_copy(
    client, librarian, record, ofelia, borrowed
):
    Item.objects.create(record=record, provenance=ofelia)
    Item.objects.create(record=record, provenance=borrowed)
    other = BibliographicRecord.objects.create(title="Dune")
    Item.objects.create(record=other, provenance=ofelia)
    resp = client.get(reverse("catalog:record_list"), {"provenance": borrowed.pk})
    assert list(resp.context["page_obj"]) == [record]


def test_items_mode_keeps_other_filters(client, librarian, ofelia):
    cat = Category.objects.create(code="ROM", name="Roman")
    kept = BibliographicRecord.objects.create(title="Fondation", category=cat)
    other = BibliographicRecord.objects.create(title="Dune")
    keeper = Item.objects.create(record=kept)
    Item.objects.create(record=other)
    resp = client.get(
        reverse("catalog:record_list"), {"mode": "items", "category": cat.pk}
    )
    assert list(resp.context["page_obj"]) == [keeper]


def test_items_mode_search_by_text(client, librarian, record):
    """La recherche plein texte reste indexée sur les notices."""
    keeper = Item.objects.create(record=record)
    other = BibliographicRecord.objects.create(title="Dune")
    Item.objects.create(record=other)
    resp = client.get(
        reverse("catalog:record_list"), {"mode": "items", "q": "Fondation"}
    )
    assert list(resp.context["page_obj"]) == [keeper]


# ── Actions de masse sur les exemplaires ───────────────────────────────────


def test_bulk_assign_provenance(client, librarian, record, borrowed):
    items = [Item.objects.create(record=record) for _ in range(3)]
    resp = client.post(
        reverse("catalog:item_bulk_assign"),
        {"ids": [it.pk for it in items[:2]], "provenance": borrowed.pk},
    )
    assert resp.status_code == 302
    assert Item.objects.filter(provenance=borrowed).count() == 2


def test_bulk_assign_provenance_can_clear_it(client, librarian, record, borrowed):
    item = Item.objects.create(record=record, provenance=borrowed)
    client.post(
        reverse("catalog:item_bulk_assign"),
        {"ids": [item.pk], "provenance": ""},
    )
    item.refresh_from_db()
    assert item.provenance_id is None


def test_bulk_assign_provenance_ignores_unselected_items(client, librarian, record, borrowed):
    """FEAT-069 : plus de page de confirmation, l'affectation est directe."""
    target = Item.objects.create(record=record)
    other = Item.objects.create(record=record)
    client.post(
        reverse("catalog:item_bulk_assign"),
        {"ids": [target.pk], "provenance": borrowed.pk},
    )
    target.refresh_from_db()
    other.refresh_from_db()
    assert target.provenance_id == borrowed.pk
    assert other.provenance_id is None


def test_bulk_delete_items_keeps_the_record(client, superadmin, record, borrowed):
    """Rendre un fonds prêté : on supprime des exemplaires, pas des notices."""
    kept = Item.objects.create(record=record)
    lent = [Item.objects.create(record=record, provenance=borrowed) for _ in range(2)]
    resp = client.post(
        reverse("catalog:item_bulk_delete"), {"ids": [it.pk for it in lent]}
    )
    assert resp.status_code == 302
    assert list(Item.objects.all()) == [kept]
    assert BibliographicRecord.objects.filter(pk=record.pk).exists()


def test_bulk_delete_items_tombstones_the_codes(client, superadmin, record, borrowed):
    """FEAT-043 : une étiquette déjà collée ne doit jamais être réattribuée."""
    item = Item.objects.create(record=record, provenance=borrowed)
    internal_id = item.internal_id
    client.post(reverse("catalog:item_bulk_delete"), {"ids": [item.pk]})
    tomb = RetiredItemCode.objects.get(internal_id=internal_id)
    assert tomb.reason == RetiredItemCode.REASON_BULK_DELETE
    assert tomb.retired_by_id == superadmin.pk


def test_bulk_delete_items_closes_open_loans(client, superadmin, record, borrowed):
    """Loan.item est en PROTECT : sans clôture préalable, la suppression casse."""
    from apps.loans.models import Loan
    from apps.loans.services import create_loan
    from apps.members.models import Member, MemberCategory

    cat = MemberCategory.objects.create(code="AD", name="Adulte")
    member = Member.objects.create(first_name="Ada", last_name="Lovelace", category=cat)
    item = Item.objects.create(record=record, provenance=borrowed)
    create_loan(item, member, superadmin)
    client.post(reverse("catalog:item_bulk_delete"), {"ids": [item.pk]})
    assert not Item.objects.filter(pk=item.pk).exists()
    assert not Loan.objects.filter(item_id=item.pk).exists()


def test_bulk_delete_items_refused_for_librarian(client, librarian, record):
    item = Item.objects.create(record=record)
    resp = client.post(reverse("catalog:item_bulk_delete"), {"ids": [item.pk]})
    assert resp.status_code in (302, 403)
    assert Item.objects.filter(pk=item.pk).exists()
