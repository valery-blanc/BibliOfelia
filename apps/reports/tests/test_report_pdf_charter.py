"""FEAT-093 — la charte OFELIA dans le PDF.

Polices du site embarquées, logo blanc en grand, titre en grand, calendrier à
côté de la période, et **en-têtes de tableau en blanc** — c'est le défaut que
Val a vu en premier : du noir sur bordeaux ne se lit pas.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from reportlab.lib import colors

from apps.reports import pdf as reports_pdf
from apps.reports.pages import Column, Period, ReportPage, Table

pytestmark = pytest.mark.django_db


def _page(**kwargs) -> ReportPage:
    defaults = {
        "slug": "test",
        "title": "Le fonds",
        "subtitle": "Sous-titre",
        "period": Period(
            date.today() - timedelta(days=30), date.today(), "12 derniers mois", "custom"
        ),
    }
    defaults.update(kwargs)
    return ReportPage(**defaults)


def test_the_site_fonts_are_available_and_registered():
    """Les TTF fabriqués par `scripts/build_pdf_fonts.py` sont versionnés : le
    PDF doit composer avec Bricolage Grotesque et DM Sans, pas avec Helvetica."""
    for filename in reports_pdf.FONT_FILES.values():
        assert (reports_pdf.FONT_DIR / filename).exists(), (
            f"{filename} manque — lancer `python scripts/build_pdf_fonts.py`"
        )
    assert reports_pdf._register_fonts() is True
    assert reports_pdf._fonts()["title"] == "Ofelia-Title"
    assert reports_pdf._fonts()["body"] == "Ofelia"


def test_the_fonts_carry_the_thin_space_used_as_thousands_separator():
    """`1 234` s'écrit avec une espace fine insécable (U+202F). Absente de la
    police, elle sortirait en carré noir sur chaque page de chiffres.

    On interroge reportlab plutôt que fontTools : c'est reportlab qui compose le
    PDF, et fontTools n'est pas installé sur la cible — il ne sert qu'à
    fabriquer les TTF, hors ligne.
    """
    from reportlab.pdfbase import pdfmetrics

    reports_pdf._register_fonts()
    for name in reports_pdf.FONT_FILES:
        face = pdfmetrics.getFont(name).face
        assert face.charToGlyph.get(0x202F), f"{name} n'a pas U+202F"


def test_table_headers_are_written_in_white():
    """Le style du `Paragraph` l'emporte sur le `TEXTCOLOR` de la table : sans
    style dédié, l'en-tête sortait en noir sur fond bordeaux."""
    styles = reports_pdf._styles()
    assert styles["head"].textColor == colors.white
    assert styles["head_narrow"].textColor == colors.white
    # Et le corps du tableau reste en encre foncée, sur fond clair.
    assert styles["cell"].textColor == reports_pdf.INK


def test_the_white_logo_is_the_one_used_on_the_burgundy_banner():
    from django.conf import settings

    assert (settings.BASE_DIR / "static" / "img" / "ofelia-logo-white.png").exists()
    assert reports_pdf._logo() is not None


def test_the_banner_is_tall_enough_for_the_logo_and_the_title():
    """Le bandeau se calcule à partir de son contenu. Au premier essai, une
    hauteur écrite à la main laissait le titre chevaucher le logo."""
    logo_bottom = reports_pdf.A4[1] - reports_pdf.BANNER_TOP - reports_pdf.LOGO_H
    title_top = reports_pdf.TITLE_BASELINE + reports_pdf.TITLE_SIZE * 0.78
    assert title_top <= logo_bottom, "le titre remonte sur le logo"

    banner_bottom = reports_pdf.A4[1] - reports_pdf.BANNER_H
    assert reports_pdf.TITLE_BASELINE > banner_bottom, "le titre déborde du bandeau"


def test_the_title_is_much_bigger_than_the_body():
    styles = reports_pdf._styles()
    assert reports_pdf.TITLE_SIZE >= 20
    assert reports_pdf.TITLE_SIZE > styles["h2"].fontSize > styles["cell"].fontSize


def test_a_report_renders_with_the_charter():
    page = _page(blocks=[
        Table(
            title="Un tableau",
            columns=[Column("Rayon"), Column("Livres", "right")],
            rows=[["Albums", "12"], ["Romans", "3"]],
        )
    ])
    content = reports_pdf.render_report_pdf(page)
    assert content[:4] == b"%PDF"
    # Les polices embarquées apparaissent dans les ressources du document.
    assert b"DMSans" in content
    assert b"BricolageGrotesque" in content


# ── Largeur des colonnes ───────────────────────────────────────────────────


def _widths(columns, rows, width=400.0, narrow=False):
    block = Table(title="t", columns=columns, rows=rows)
    return reports_pdf._column_widths(block, reports_pdf._styles(), width, narrow)


def test_column_widths_fill_the_available_space():
    widths = _widths(
        [Column("Mois"), Column("Nouveaux", "right")],
        [["septembre 2025", "0"], ["octobre 2025", "22"]],
    )
    assert sum(widths) == pytest.approx(400.0, abs=0.5)


def test_a_long_word_header_is_not_cut_in_half_when_there_is_room():
    """« Réinscriptions » tenait sur deux lignes dans un tableau à demi-page :
    la colonne doit être au moins aussi large que le mot."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    styles = reports_pdf._styles()
    columns = [
        Column("Mois"), Column("Nouveaux", "right"),
        Column("Réinscriptions", "right"), Column("Cartes perdues", "right"),
    ]
    rows = [["septembre 2025", "0", "0", "0"]] * 12
    widths = _widths(columns, rows, width=245.0, narrow=True)

    word = stringWidth("Réinscriptions", styles["font"]["bold"], styles["head_narrow"].fontSize)
    assert widths[2] >= word, "la colonne est plus étroite que son en-tête"


def test_a_very_long_title_does_not_starve_the_other_columns():
    """Un titre de cent caractères doit laisser vivre « Rayon » et « Prêts ».

    C'est le cas serré : le tableau ne tient pas, il faut rogner. Chaque colonne
    garde au moins la largeur de son plus long mot, faute de quoi le texte se
    briserait en plein milieu.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    styles = reports_pdf._styles()
    widths = _widths(
        [Column("Livre"), Column("Rayon"), Column("Prêts", "right")],
        [["Le " + "très " * 40 + "long titre", "Albums", "3"]],
        width=200.0,
    )
    assert sum(widths) == pytest.approx(200.0, abs=0.5)
    for index, word in enumerate(("Livre", "Albums", "Prêts")):
        needed = stringWidth(word, styles["font"]["body"], styles["cell"].fontSize)
        assert widths[index] >= needed, f"la colonne {index} écrase « {word} »"


def test_column_widths_survive_a_table_with_no_rows():
    widths = _widths([Column("Rayon"), Column("Livres", "right")], [])
    assert len(widths) == 2
    assert sum(widths) == pytest.approx(400.0, abs=0.5)


# ── Libellés d'axe ─────────────────────────────────────────────────────────


def test_long_month_labels_are_shortened_but_keep_their_year():
    """Douze fois « septembre 2025 » se chevauchent ; l'année, elle, distingue
    deux barres identiques d'une année sur l'autre et ne s'ampute pas."""
    labels = [
        "septembre 2025", "octobre 2025", "novembre 2025", "décembre 2025",
        "janvier 2026", "février 2026", "mars 2026", "avril 2026",
        "mai 2026", "juin 2026", "juillet 2026", "août 2026", "septembre 2026",
    ]
    out = reports_pdf._axis_labels(labels, 380.0)
    assert all("2025" in o or "2026" in o for o in out)
    assert max(len(o) for o in out) < max(len(label) for label in labels)


def test_short_labels_are_left_alone():
    labels = ["2024", "2025", "2026"]
    assert reports_pdf._axis_labels(labels, 380.0) == labels


def test_every_character_a_report_writes_exists_in_the_pdf_fonts():
    """Aucun caractère produit par les rapports ne doit manquer aux polices.

    reportlab ne sait pas retomber sur une autre police : un glyphe absent se
    dessine en carré noir. C'est arrivé à la flèche « → » du libellé de période
    de comparaison — les sous-ensembles Google Fonts couvrent la ponctuation
    générale, mais pas le bloc des flèches.

    On échantillonne ici ce que les rapports composent réellement : libellés de
    période, séparateurs de milliers, symboles et accents des quatre langues.
    """
    from datetime import date as _date

    from reportlab.pdfbase import pdfmetrics

    from apps.reports import format as fmt
    from apps.reports import periods

    reports_pdf._register_fonts()
    written = "".join([
        periods.short_label(_date(2024, 9, 10), _date(2025, 9, 9)),
        periods.custom_label(_date(2024, 9, 10), _date(2025, 9, 9)),
        fmt.number(1234567), fmt.percent(1, 3), fmt.ratio(1.5), fmt.days(12),
        fmt.blank(""), fmt.age_bracket(None),
        "« » — – … € $ £ ¥ % ’",
        "àâäçéèêëîïôöùûüÿœ ÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒ áíóúñ¿¡",
    ])

    for name in reports_pdf.FONT_FILES:
        face = pdfmetrics.getFont(name).face
        missing = sorted(
            {c for c in written if c != "\n" and not face.charToGlyph.get(ord(c))}
        )
        assert not missing, (
            f"{name} n'a pas " + " ".join(f"U+{ord(c):04X} {c!r}" for c in missing)
        )
