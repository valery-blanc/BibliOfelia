"""FEAT-096 — export Excel de la liste catalogue filtrée."""
from __future__ import annotations

import io

import openpyxl
import pytest
from django.http import QueryDict
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role
from apps.catalog.list_export import (
    build_list_workbook,
    item_headers,
    list_export_filename,
    record_headers,
)
from apps.catalog.models import (
    Author,
    BibliographicRecord,
    Category,
    Item,
    Location,
    Provenance,
)

pytestmark = pytest.mark.django_db


def _read(content: bytes):
    wb = openpyxl.load_workbook(io.BytesIO(content))
    ws = wb.active
    headers = [c.value for c in ws[1]]
    rows = [[c.value for c in row] for row in ws.iter_rows(min_row=2)]
    return headers, rows


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="bib", password="x", role=Role.LIBRARIAN
    )


@pytest.fixture
def readonly(django_user_model):
    return django_user_model.objects.create_user(
        username="lecteur", password="x", role=Role.READONLY
    )


@pytest.fixture
def fonds():
    category = Category.objects.create(code="RO", name="Romans")
    a1 = Location.objects.create(code="A1")
    b2 = Location.objects.create(code="B2")
    provenance = Provenance.objects.create(code="BM-GE", label="Prêt Genève")
    prince = BibliographicRecord.objects.create(title="Le Petit Prince", category=category)
    prince.authors.add(Author.objects.create(full_name="Saint-Exupéry"))
    germinal = BibliographicRecord.objects.create(title="Germinal")
    germinal.authors.add(Author.objects.create(full_name="Émile Zola"))
    first = Item.objects.create(
        record=prince, location=a1, provenance=provenance, external_code="EXT-1"
    )
    second = Item.objects.create(record=prince, location=b2)
    other = Item.objects.create(record=germinal, location=a1)
    return {
        "prince": prince,
        "germinal": germinal,
        "a1": a1,
        "b2": b2,
        "first": first,
        "second": second,
        "other": other,
    }


def test_record_headers_are_the_visible_columns_plus_location():
    assert record_headers() == [
        "Titre",
        "Auteur(s)",
        "Classification",
        "Ex.",
        "Emplacement",
    ]


def test_item_headers_are_the_visible_columns_plus_location():
    assert item_headers() == [
        "Titre",
        "Auteur(s)",
        "Classification",
        "Code Ofelia",
        "Code Ofelia externe",
        "Provenance",
        "Emplacement",
    ]


def test_records_export_one_row_per_notice_with_joined_locations(fonds):
    headers, rows = _read(build_list_workbook(QueryDict("")))
    assert headers == record_headers()
    assert len(rows) == 2
    by_title = {row[0]: row for row in rows}
    prince = by_title["Le Petit Prince"]
    assert prince[1] == "Saint-Exupéry"
    assert prince[2] == "Romans"
    assert prince[3] == 2
    assert prince[4] == "A1, B2"
    germinal = by_title["Germinal"]
    assert germinal[2] in (None, "")
    assert germinal[3] == 1
    assert germinal[4] == "A1"


def test_items_export_one_row_per_copy_with_its_location(fonds):
    headers, rows = _read(build_list_workbook(QueryDict("mode=items")))
    assert headers == item_headers()
    assert len(rows) == 3
    by_code = {row[3]: row for row in rows}
    first = by_code[fonds["first"].ean13]
    assert first[0] == "Le Petit Prince"
    assert first[4] == "EXT-1"
    assert first[5] == "Prêt Genève"
    assert first[6] == "A1"
    second = by_code[fonds["second"].ean13]
    assert second[4] in (None, "")
    assert second[5] in (None, "")
    assert second[6] == "B2"


def test_filters_and_pagination_are_respected(fonds):
    """Le fichier ignore `page` : toute la recherche sort, pas 25 lignes."""
    for i in range(30):
        BibliographicRecord.objects.create(title=f"Autre {i:02d}")
    params = QueryDict(f"category={fonds['prince'].category_id}&page=2")
    _headers, rows = _read(build_list_workbook(params))
    assert [row[0] for row in rows] == ["Le Petit Prince"]


def test_location_filter_reduces_the_export(fonds):
    params = QueryDict(mutable=True)
    params.setlist("location", [str(fonds["b2"].pk)])
    _headers, rows = _read(build_list_workbook(params))
    assert [row[0] for row in rows] == ["Le Petit Prince"]
    params["mode"] = "items"
    _headers, rows = _read(build_list_workbook(params))
    assert len(rows) == 1
    assert rows[0][6] == "B2"


def test_filename_depends_on_mode():
    today = timezone.localdate().isoformat()
    assert list_export_filename(QueryDict("")) == f"catalogue-notices-{today}.xlsx"
    assert (
        list_export_filename(QueryDict("mode=items"))
        == f"catalogue-exemplaires-{today}.xlsx"
    )


def test_export_view_returns_xlsx_and_keeps_filters(client, librarian, fonds):
    client.force_login(librarian)
    resp = client.get(
        reverse("catalog:catalog_list_export"),
        {"mode": "items", "location": fonds["b2"].pk},
    )
    assert resp.status_code == 200
    assert "spreadsheetml" in resp["Content-Type"]
    assert "attachment" in resp["Content-Disposition"]
    assert "catalogue-exemplaires-" in resp["Content-Disposition"]
    headers, rows = _read(resp.content)
    assert headers == item_headers()
    assert len(rows) == 1
    assert rows[0][0] == "Le Petit Prince"
    assert rows[0][6] == "B2"


def test_readonly_can_export(client, readonly, fonds):
    client.force_login(readonly)
    resp = client.get(reverse("catalog:catalog_list_export"))
    assert resp.status_code == 200
    _headers, rows = _read(resp.content)
    assert len(rows) == 2


def test_catalog_page_offers_the_button_with_current_filters(client, librarian, fonds):
    client.force_login(librarian)
    resp = client.get(
        reverse("catalog:record_list"),
        {"mode": "items", "location": fonds["b2"].pk},
    )
    body = resp.content.decode()
    assert "Export Excel" in body
    assert reverse("catalog:catalog_list_export") in body
    assert "mode=items" in body
    assert str(fonds["b2"].pk) in body


def test_button_hidden_when_the_list_is_empty(client, librarian):
    client.force_login(librarian)
    body = client.get(reverse("catalog:record_list")).content.decode()
    assert "Export Excel" not in body
