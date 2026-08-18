"""FEAT-062 — impression sur ruban continu Brother QL-810W (62 mm noir/rouge).

La QL-810W est branchée en USB sur le poste du bibliothécaire : le serveur ne
peut que produire un PDF à la géométrie exacte du ruban, c'est le navigateur du
poste qui parle au pilote. Ces tests verrouillent donc la géométrie (une
étiquette par page, page = largeur du ruban) plutôt qu'un envoi réseau.
"""
from __future__ import annotations

import re

import pytest
from reportlab.lib import colors
from reportlab.lib.units import mm

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item, Location
from apps.core.models import Setting
from apps.members.models import Member, MemberCategory
from apps.printing.services import (
    RED,
    ROLL_FONT,
    ROLL_TEXT_PT,
    _accent,
    _fit_to_width,
    _roll_settings,
    _static_logo_grayscale,
    _text_width,
    _wrap_to_width,
    render_item_labels_roll_pdf,
    render_member_cards_roll_pdf,
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
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Alice", last_name="Wonderland", category=category,
        preferred_language="fr",
    )


@pytest.fixture
def items():
    loc = Location.objects.create(code="A1")
    out = []
    for title in ("Le Comte de Monte-Cristo intégral", "Atlas"):
        rec = BibliographicRecord.objects.create(title=title)
        out.append(Item.objects.create(record=rec, location=loc))
    return out


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


# -- Réglages ----------------------------------------------------------
def test_roll_defaults_on_a_fresh_instance():
    """Aucun Setting posé → ruban 62 mm bicolore, étiquette 35 mm, carte 89 mm."""
    assert Setting.objects.filter(key="roll_printer_format").count() == 0
    assert _roll_settings() == {
        "enabled": True,
        "tape_width_mm": 62,
        "label_length_mm": 35,
        "card_length_mm": 89,
        "two_color": True,
        "show_logo": True,
    }


def test_accent_is_pure_red_only_when_two_color():
    """Le pilote Brother ne déclenche la 2e couleur que sur du rouge pur.

    L'accent ne sert plus qu'aux cartes membres : les étiquettes sont
    entièrement monochromes depuis les retours de Val (2026-08-18).
    """
    assert _accent(True) == RED == colors.Color(1, 0, 0)
    assert _accent(False) == colors.black


# -- Mise en page du texte --------------------------------------------
def test_wrap_to_width_uses_the_whole_label_width():
    """Le titre remplit la largeur au lieu de casser sur un quota de caractères."""
    width = 58 * mm
    lines = _wrap_to_width(
        "Il illlustre lili ilili lit ili lilit illi litil ilil litili ili",
        ROLL_FONT, ROLL_TEXT_PT, width, 2,
    )
    assert lines
    for line in lines:
        assert _text_width(line, ROLL_FONT, ROLL_TEXT_PT) <= width
    # Des caractères étroits : l'ancien budget de 38 signes gaspillait la place.
    assert len(lines[0]) > 38


def test_wrap_to_width_marks_a_truncated_title():
    lines = _wrap_to_width("mot " * 60, ROLL_FONT, ROLL_TEXT_PT, 58 * mm, 2)
    assert len(lines) == 2
    assert lines[-1].endswith("…")


def test_fit_to_width_shortens_a_long_library_name():
    width = 20 * mm
    out = _fit_to_width("Bibliothèque du Grand-Saconnex", ROLL_FONT, ROLL_TEXT_PT, width)
    assert out.endswith("…")
    assert _text_width(out, ROLL_FONT, ROLL_TEXT_PT) <= width


def test_fit_to_width_leaves_a_short_text_alone():
    assert _fit_to_width("A1", ROLL_FONT, ROLL_TEXT_PT, 58 * mm) == "A1"


def test_logo_is_converted_to_grayscale():
    """Le logo Ofelia part en niveaux de gris : l'étiqueteuse est monochrome."""
    reader = _static_logo_grayscale("ofelia-logo.png")
    assert reader is not None
    data = reader.getRGBData()
    assert data and len(data) % 3 == 0
    assert all(data[i] == data[i + 1] == data[i + 2] for i in range(0, len(data), 3))


# -- Étiquettes --------------------------------------------------------
def test_item_labels_roll_uses_tape_geometry(items):
    assert _page_size_mm(render_item_labels_roll_pdf(items)) == (62.0, 35.0)


def test_item_labels_roll_emits_one_page_per_label(items):
    """Une étiquette = une page = une coupe.

    La QL est réglée pour couper tous les 35 mm : regrouper des étiquettes sur
    une page plus longue (essai du 2026-08-18 pour forcer l'orientation
    portrait du dialogue) donnait une page que l'imprimante ne pouvait pas
    honorer.
    """
    assert _page_count(render_item_labels_roll_pdf(items)) == len(items)


def test_item_labels_roll_follows_settings(items):
    Setting.set("roll_printer_format", {"tape_width_mm": 50, "label_length_mm": 40})
    assert _page_size_mm(render_item_labels_roll_pdf(items)) == (50.0, 40.0)


def test_item_labels_roll_without_location(items):
    """Un exemplaire sans emplacement ne casse pas le pied de l'étiquette."""
    items[0].location = None
    items[0].save()
    assert _page_count(render_item_labels_roll_pdf(items[:1])) == 1


def test_member_cards_roll_page_is_taller_than_wide(member):
    width, height = _page_size_mm(render_member_cards_roll_pdf([member]))
    assert height > width


# -- Cartes membres ----------------------------------------------------
def test_member_cards_roll_uses_tape_geometry(member):
    pdf = render_member_cards_roll_pdf([member])
    assert _page_size_mm(pdf) == (62.0, 89.0)


def test_member_cards_roll_emits_one_page_per_member(member, category):
    other = Member.objects.create(first_name="Bob", last_name="Marley", category=category)
    assert _page_count(render_member_cards_roll_pdf([member, other])) == 2


def test_member_cards_roll_shrinks_to_fit_a_narrow_tape(member):
    """Ruban 29 mm : la carte est réduite, pas débordée — le PDF sort quand même."""
    Setting.set("roll_printer_format", {"tape_width_mm": 29, "card_length_mm": 60})
    pdf = render_member_cards_roll_pdf([member])
    assert _page_size_mm(pdf) == (29.0, 60.0)


# -- Vues --------------------------------------------------------------
def test_labels_roll_pdf_view_returns_pdf(client, librarian, items):
    client.force_login(librarian)
    resp = client.get("/fr/printing/labels-roll.pdf", {"ids": [i.pk for i in items]})
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert _page_count(resp.content) == len(items)


def test_cards_roll_pdf_view_returns_pdf(client, librarian, member):
    client.force_login(librarian)
    resp = client.get("/fr/printing/cards-roll.pdf", {"ids": [member.pk]})
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"


def test_roll_pdf_view_without_selection_redirects(client, librarian):
    client.force_login(librarian)
    resp = client.get("/fr/printing/labels-roll.pdf")
    assert resp.status_code == 302


def test_intermediate_print_page_is_gone(client, librarian):
    """Val ne veut pas d'écran de plus avant le dialogue d'impression."""
    client.force_login(librarian)
    assert client.get("/fr/printing/roll/labels/print/").status_code == 404


def test_picker_button_opens_the_pdf_directly(client, librarian, items):
    body = _picker_body(client, librarian)
    assert "labels-roll.pdf" in body
    assert 'formtarget="_blank"' in body


def test_pickers_hide_the_roll_button_when_disabled(client, librarian, items):
    assert "labels-roll.pdf" in _picker_body(client, librarian)
    Setting.set("roll_printer_format", {"enabled": False})
    assert "labels-roll.pdf" not in _picker_body(client, librarian)


def _picker_body(client, librarian) -> str:
    client.force_login(librarian)
    return client.get("/fr/printing/labels/").content.decode()
