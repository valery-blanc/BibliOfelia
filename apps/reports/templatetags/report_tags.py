"""Filtres de rendu des blocs de rapport. FEAT-093."""
from __future__ import annotations

from django import template

from .. import charts
from ..pages import Chart, Table

register = template.Library()


@register.filter
def chart_svg(chart, layout: str = ""):
    """Le SVG du graphe. `layout="compact"` = posé à côté d'un tableau.

    Un SVG s'étire à la largeur de son conteneur : le même dessin sur une
    demi-page est réduit d'un tiers et son texte devient illisible. La version
    compacte a un disque plus petit et moins de marge, donc un texte
    proportionnellement plus grand.
    """
    return charts.render(chart, compact=(layout == "compact"))


@register.filter
def is_chart(block) -> bool:
    return isinstance(block, Chart)


@register.filter
def is_table(block) -> bool:
    return isinstance(block, Table)


@register.filter
def anchor(block) -> str:
    """Une ancre stable pour le sommaire, dérivée du titre du bloc."""
    import hashlib

    return "b" + hashlib.md5(block.title.encode("utf-8")).hexdigest()[:8]


@register.filter
def cells(row, columns):
    """Apparie les valeurs d'une ligne avec leurs colonnes, pour que
    l'alignement à droite des nombres se retrouve dans le HTML."""
    return [
        {"value": value, "align": columns[index].align if index < len(columns) else "left"}
        for index, value in enumerate(row)
    ]
