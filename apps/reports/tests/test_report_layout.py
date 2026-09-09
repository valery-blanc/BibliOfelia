"""FEAT-093 — la mise en page des écrans, après le second essai de Val.

Trois choses vérifiées ici, chacune correspondant à un défaut constaté :

- la feuille de style des rapports est dans **`ofelia.css`**, la seule que
  `base.html` charge — dans `bibliofelia.css` elle n'atteignait aucun écran ;
- les graphes appariés à un tableau sont tracés en version **compacte**, sinon
  leur texte devient minuscule sur une demi-page ;
- une courbe restée à zéro est **quand même tracée**, sans quoi la légende
  annonce trois séries pour un dessin qui n'en montre qu'une.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from django.conf import settings

from apps.reports import charts
from apps.reports.pages import Chart, Series

CSS_DIR = Path(settings.BASE_DIR) / "static" / "css"

# Les classes que les gabarits de rapport posent sur le HTML.
REPORT_CLASSES = [
    "chip-btn", "report-toc", "report-action", "report-card",
    "block-pair--split", "block-exports", "chart-card",
]


def test_the_report_stylesheet_is_the_one_the_pages_load():
    """`base.html` ne charge que `ofelia.css`.

    Tout le bloc des rapports était parti dans `bibliofelia.css`, feuille que
    seuls les deux gabarits du wizard d'installation référencent : les boutons,
    le sommaire et la mise en page côte à côte existaient dans le HTML mais
    n'étaient habillés par rien.
    """
    base = (Path(settings.BASE_DIR) / "templates" / "base.html").read_text(
        encoding="utf-8"
    )
    loaded = set(re.findall(r"css/([\w.-]+\.css)", base))
    assert "ofelia.css" in loaded

    ofelia = (CSS_DIR / "ofelia.css").read_text(encoding="utf-8")
    for name in REPORT_CLASSES:
        assert f".{name}" in ofelia, f"« {name} » n'est habillé par aucune règle"


def test_no_report_class_is_left_in_the_unloaded_stylesheet():
    unloaded = (CSS_DIR / "bibliofelia.css").read_text(encoding="utf-8")
    for name in REPORT_CLASSES:
        assert f".{name}" not in unloaded


@pytest.mark.parametrize("kind", ["bar", "pie", "line"])
def test_a_compact_chart_is_narrower_than_the_full_width_one(kind):
    """Un SVG s'étire à son conteneur : le dessin de demi-page doit être plus
    petit, pour que son texte reste de la même taille à l'écran."""
    chart = Chart(
        title="t", kind=kind,
        labels=["janvier 2026", "février 2026", "mars 2026"],
        values=[3, 5, 2],
        series=[Series("Nouveaux", [3, 5, 2])],
    )
    wide = charts.render(chart)
    compact = charts.render(chart, compact=True)
    assert _viewbox_width(compact) < _viewbox_width(wide)


def _viewbox_width(svg: str) -> float:
    match = re.search(r'viewBox="0 0 ([\d.]+) ', svg)
    assert match, "le SVG n'a pas de viewBox"
    return float(match.group(1))


def test_a_pie_label_fits_inside_the_drawing():
    """« Adolescent (14-17 ans) 20 (91 %) » sortait du cadre et se voyait
    tronquer par le bord de la carte."""
    chart = Chart(
        title="t", kind="pie",
        labels=["Adolescent (14-17 ans)", "Adulte"], values=[20, 2],
    )
    svg = charts.pie_svg(chart)
    width = _viewbox_width(svg)
    texts = re.findall(r'<text x="([\d.]+)"[^>]*text-anchor="(\w+)"[^>]*>([^<]+)<', svg)
    assert texts
    for x, anchor, label in texts:
        # Largeur approchée du texte, au corps utilisé pour les étiquettes.
        span = len(label) * 6.6
        right = float(x) + (span if anchor == "start" else 0)
        left = float(x) - (span if anchor == "end" else 0)
        assert left >= -1, f"« {label} » déborde à gauche"
        assert right <= width + 1, f"« {label} » déborde à droite"
    assert "…" not in "".join(t[2] for t in texts), "l'étiquette a été tronquée"


def test_a_flat_series_is_still_drawn():
    """Une courbe restée à zéro dit « on n'a perdu personne » : c'est une
    information, et la légende l'annonce."""
    chart = Chart(
        title="t", kind="line", labels=["jan", "fév", "mar"],
        series=[
            Series("Nouveaux", [0, 22, 0]),
            Series("Réinscriptions", [0, 0, 0]),
            Series("Usagers perdus", [0, 0, 0]),
        ],
    )
    svg = charts.line_svg(chart)
    assert svg.count("<polyline") == 3
    for label in ("Nouveaux", "Réinscriptions", "Usagers perdus"):
        assert label in svg


def test_the_paired_chart_is_rendered_compact_by_the_template_filter():
    from apps.reports.templatetags.report_tags import chart_svg

    chart = Chart(title="t", kind="pie", labels=["A", "B"], values=[3, 1])
    assert _viewbox_width(chart_svg(chart, "compact")) < _viewbox_width(chart_svg(chart))


def test_the_pie_margin_follows_the_longest_label():
    """La marge latérale se mesure sur les étiquettes, elle n'est pas figée.

    Une valeur fixe finit toujours par être trop courte pour un libellé un peu
    long, et le texte déborde du cadre — c'est ce qui est arrivé au camembert
    des rayons.
    """
    short = Chart(title="t", kind="pie", labels=["A", "B"], values=[3, 1])
    long = Chart(
        title="t", kind="pie",
        labels=["Adultes Documentaire jeunesse", "Bandes dessinées adultes"],
        values=[3, 1],
    )
    assert _viewbox_width(charts.pie_svg(long)) > _viewbox_width(charts.pie_svg(short))


@pytest.mark.parametrize("compact,font", [(False, 12.5), (True, 11)])
def test_no_pie_label_ever_leaves_the_frame(compact, font):
    """Sur des libellés volontairement longs, dans les deux géométries.

    Le corps diffère selon la géométrie : mesurer au mauvais corps ferait
    passer — ou échouer — le test sans rien dire du dessin.
    """
    chart = Chart(
        title="t", kind="pie",
        labels=[
            "Adultes Documentaire sciences", "Jeunesse albums illustrés",
            "Bandes dessinées et mangas", "Périodiques",
        ],
        values=[894, 48, 11, 3],
    )
    svg = charts.pie_svg(chart, compact=compact)
    width = _viewbox_width(svg)
    for x, anchor, label in re.findall(
        r'<text x="([\d.-]+)"[^>]*text-anchor="(\w+)"[^>]*>([^<]+)<', svg
    ):
        span = charts._text_width(label, font)
        right = float(x) + (span if anchor == "start" else 0)
        left = float(x) - (span if anchor == "end" else 0)
        assert left >= -1, f"« {label} » déborde à gauche"
        assert right <= width + 1, f"« {label} » déborde à droite"


def test_a_wide_table_gets_the_full_size_chart_not_the_compact_one():
    """Un tableau de plus de quatre colonnes prend toute la largeur : son graphe
    aussi. Le dessin compact y serait étiré et ses libellés grossis."""
    page = (Path(settings.BASE_DIR) / "templates" / "reports" / "page.html").read_text(
        encoding="utf-8"
    )
    # Le gabarit choisit la géométrie sur le nombre de colonnes du tableau.
    assert 'block.columns|length > 4' in page
    assert 'chart_svg }}' in page  # pleine largeur
    assert 'chart_svg:"compact"' in page  # demi-page
