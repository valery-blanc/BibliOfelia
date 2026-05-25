"""Tests FEAT-038 + FEAT-039 — refonte impression cartes membres + étiquettes livres."""
from __future__ import annotations

import pytest

from apps.catalog.models import BibliographicRecord, Item, Location
from apps.core.models import Setting
from apps.members.models import Member, MemberCategory
from apps.printing.services import (
    _card_settings,
    _item_label_settings,
    _wrap_title,
    render_item_labels_pdf,
    render_member_cards_pdf,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Alice", last_name="Wonderland", category=category,
        preferred_language="fr",
    )


@pytest.fixture
def item():
    rec = BibliographicRecord.objects.create(title="Le Comte de Monte-Cristo intégral")
    loc = Location.objects.create(code="A1")
    return Item.objects.create(record=rec, location=loc)


# -- _wrap_title -------------------------------------------------------

def test_wrap_title_one_line_fits():
    assert _wrap_title("Court titre", max_chars=50, max_lines=2) == ["Court titre"]


def test_wrap_title_two_lines():
    lines = _wrap_title(
        "Le Comte de Monte-Cristo édition intégrale 1844",
        max_chars=50, max_lines=2,
    )
    assert len(lines) == 2
    # Aucune coupure au milieu d'un mot
    for ln in lines:
        for word in ln.split():
            assert " " not in word


def test_wrap_title_truncates_when_too_long():
    lines = _wrap_title(
        "Une suite très très longue de mots qui dépassent franchement la limite imposée par défaut",
        max_chars=30, max_lines=2,
    )
    assert len(lines) <= 2
    assert lines[-1].endswith("…")


def test_wrap_title_empty():
    assert _wrap_title("", max_chars=50, max_lines=2) == []


# -- settings ----------------------------------------------------------

def test_card_settings_defaults():
    fmt = _card_settings()
    assert fmt["per_a4"] == 8
    assert fmt["show_logo"] is True
    assert fmt["show_photo"] is True


def test_card_settings_legacy_migration():
    Setting.set("label_format", {"card_per_a4": 6})
    fmt = _card_settings()
    assert fmt["per_a4"] == 6


def test_card_settings_explicit_overrides_legacy():
    Setting.set("label_format", {"card_per_a4": 6})
    Setting.set("card_format", {"per_a4": 10, "show_logo": False, "show_photo": True})
    fmt = _card_settings()
    assert fmt["per_a4"] == 10
    assert fmt["show_logo"] is False


def test_item_label_settings_defaults():
    fmt = _item_label_settings()
    assert fmt["width_mm"] == 70
    assert fmt["height_mm"] == 42
    assert fmt["title_max_chars"] == 50
    assert fmt["title_lines"] == 2
    assert fmt["author_lines"] == 2
    assert fmt["show_logo"] is True


def test_item_label_settings_legacy_migration():
    Setting.set("label_format", {
        "item_width_mm": 70, "item_height_mm": 36, "item_title_max_chars": 30,
    })
    fmt = _item_label_settings()
    assert fmt["width_mm"] == 70
    assert fmt["height_mm"] == 36
    assert fmt["title_max_chars"] == 30


# -- PDF rendering (smoke) --------------------------------------------

def test_render_member_cards_pdf(member):
    pdf = render_member_cards_pdf([member])
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_render_member_cards_pdf_without_photo(member):
    member.photo = None
    member.save()
    pdf = render_member_cards_pdf([member])
    assert pdf.startswith(b"%PDF")


def test_render_item_labels_pdf(item):
    pdf = render_item_labels_pdf([item])
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_render_item_labels_pdf_with_long_title():
    rec = BibliographicRecord.objects.create(
        title="Un titre extrêmement long qui dépasse de loin la limite de 50 caractères imposée",
    )
    item = Item.objects.create(record=rec)
    pdf = render_item_labels_pdf([item])
    assert pdf.startswith(b"%PDF")
