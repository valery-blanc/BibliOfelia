"""FEAT-068 — étiquettes de tranche : la cote de catégorie, en gros, centrée."""
from __future__ import annotations

import re

import pytest
from django.urls import reverse
from reportlab.lib.units import mm

from apps.accounts.models import Role, User
from apps.catalog.models import BibliographicRecord, Category, Item
from apps.core.models import Setting
from apps.printing.services import (
    ROLL_FONT,
    SPINE_MAX_PT,
    SPINE_MIN_PT,
    _text_width,
    _wrap_words,
    render_spine_labels_roll_pdf,
    spine_label_text,
    spine_layout,
)

pytestmark = pytest.mark.django_db

_MEDIABOX_RE = re.compile(rb"/MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)")
_COUNT_RE = re.compile(rb"/Count\s+(\d+)")


def _page_size_mm(pdf: bytes) -> tuple[float, float]:
    match = _MEDIABOX_RE.search(pdf)
    assert match, "MediaBox introuvable dans le PDF"
    return round(float(match.group(1)) / mm, 1), round(float(match.group(2)) / mm, 1)


def _page_count(pdf: bytes) -> int:
    counts = [int(m) for m in _COUNT_RE.findall(pdf)]
    assert counts, "/Count introuvable dans le PDF"
    return max(counts)


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture
def category():
    return Category.objects.create(
        code="ADU-ROM-ADO",
        name="Romans fiction pour adolescents",
        abbreviation="RO FI ADO",
    )


@pytest.fixture
def item(category):
    record = BibliographicRecord.objects.create(title="Fondation", category=category)
    return Item.objects.create(record=record)


# ── Ce qui s'imprime ───────────────────────────────────────────────────────


def test_spine_text_is_the_category_abbreviation(item):
    assert spine_label_text(item) == "RO FI ADO"


def test_spine_text_empty_without_category():
    record = BibliographicRecord.objects.create(title="Sans catégorie")
    assert spine_label_text(Item.objects.create(record=record)) == ""


def test_spine_text_empty_when_category_has_no_abbreviation():
    cat = Category.objects.create(code="X", name="Sans cote")
    record = BibliographicRecord.objects.create(title="Fondation", category=cat)
    assert spine_label_text(Item.objects.create(record=record)) == ""


# ── Géométrie ──────────────────────────────────────────────────────────────


def test_page_matches_the_book_label_geometry(item):
    """Même ruban, même coupe que les étiquettes de livres (FEAT-062)."""
    pdf = render_spine_labels_roll_pdf([item])
    assert _page_size_mm(pdf) == (62.0, 35.0)


def test_one_page_per_item(item, category):
    record = BibliographicRecord.objects.create(title="Dune", category=category)
    second = Item.objects.create(record=record)
    assert _page_count(render_spine_labels_roll_pdf([item, second])) == 2


def test_items_without_abbreviation_are_skipped(item):
    """Rien à imprimer pour eux : ils ne doivent pas sortir une page blanche."""
    blank_record = BibliographicRecord.objects.create(title="Sans catégorie")
    blank = Item.objects.create(record=blank_record)
    assert _page_count(render_spine_labels_roll_pdf([item, blank])) == 1


def test_geometry_follows_the_roll_setting(item):
    Setting.objects.update_or_create(
        pk="roll_printer_format",
        defaults={"value": {"tape_width_mm": 29, "label_length_mm": 40}},
    )
    assert _page_size_mm(render_spine_labels_roll_pdf([item])) == (29.0, 40.0)


def test_empty_selection_still_produces_a_valid_pdf():
    pdf = render_spine_labels_roll_pdf([])
    assert pdf.startswith(b"%PDF")
    assert _page_count(pdf) == 1


# ── Mise à l'échelle du texte ──────────────────────────────────────────────


def test_wrap_never_splits_a_word():
    lines = _wrap_words(["RO", "FI", "ADO"], ROLL_FONT, 60, 100)
    assert all(" " not in line or line.count(" ") >= 1 for line in lines)
    assert "".join(lines).replace(" ", "") == "ROFIADO"


def test_wrap_fills_the_width_before_breaking():
    """Avec de la place, la cote tient sur une ligne."""
    assert _wrap_words(["RO", "FI", "ADO"], ROLL_FONT, 10, 500) == ["RO FI ADO"]


# Zone utile d'une étiquette 62 × 35 mm, retraits compris (cf. _draw_roll_spine_label).
INNER_W = (62 - 2 * 2.0) * mm
INNER_H = (35 - 2 * 3.0) * mm


def test_wraps_on_two_lines_like_the_requested_mockup():
    """« RO FI ADO » doit sortir « RO FI » / « ADO », comme demandé."""
    _size, lines = spine_layout("RO FI ADO", INNER_W, INNER_H)
    assert lines == ["RO FI", "ADO"]


def test_short_abbreviation_is_printed_bigger_than_a_long_one():
    """Une cote courte doit remplir l'étiquette, pas rester timide au centre."""
    short_pt, short_lines = spine_layout("PER", INNER_W, INNER_H)
    long_pt, _ = spine_layout("RO FI ADO", INNER_W, INNER_H)
    assert short_lines == ["PER"]
    assert short_pt > long_pt
    assert SPINE_MIN_PT <= long_pt <= SPINE_MAX_PT


def test_layout_never_overflows_the_label():
    for text in ("PER", "RO FI ADO", "BANDES DESSINEES JEUNESSE", "ABCDEFGHIJKLMNOPQRST"):
        size, lines = spine_layout(text, INNER_W, INNER_H)
        assert size >= SPINE_MIN_PT, text
        widest = max(_text_width(line, ROLL_FONT, size) for line in lines)
        assert widest <= INNER_W + 0.5, text
        block_h = (len(lines) - 1) * size * 1.12 + size * 0.72
        assert block_h <= INNER_H + 0.5, text


def test_a_single_word_too_wide_is_shrunk_not_split():
    size, lines = spine_layout("ABCDEFGHIJKLMNOPQRST", INNER_W, INNER_H)
    assert lines == ["ABCDEFGHIJKLMNOPQRST"]
    assert _text_width(lines[0], ROLL_FONT, size) <= INNER_W


# ── Vue et écran de sélection ──────────────────────────────────────────────


def test_view_returns_a_pdf(client, librarian, item):
    resp = client.get(reverse("printing:spine_labels_roll_pdf"), {"ids": [item.pk]})
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


def test_view_warns_when_no_selection(client, librarian):
    resp = client.get(reverse("printing:spine_labels_roll_pdf"))
    assert resp.status_code == 302


def test_view_warns_when_nothing_has_an_abbreviation(client, librarian):
    """Mieux vaut le dire que sortir un PDF vide."""
    record = BibliographicRecord.objects.create(title="Sans catégorie")
    blank = Item.objects.create(record=record)
    resp = client.get(reverse("printing:spine_labels_roll_pdf"), {"ids": [blank.pk]})
    assert resp.status_code == 302
    assert resp.url == reverse("printing:labels")


def test_picker_offers_the_button(client, librarian, item):
    body = client.get(reverse("printing:labels")).content.decode()
    assert reverse("printing:spine_labels_roll_pdf") in body
    assert "Étiquettes de tranche" in body


def test_button_hidden_when_roll_printing_is_disabled(client, librarian, item):
    Setting.objects.update_or_create(
        pk="roll_printer_format", defaults={"value": {"enabled": False}}
    )
    body = client.get(reverse("printing:labels")).content.decode()
    assert reverse("printing:spine_labels_roll_pdf") not in body
