"""Histogrammes, camemberts et courbes tracés par le serveur, en SVG. FEAT-093.

Pas de JavaScript et pas de bibliothèque de graphes : la Box travaille hors
ligne, un CDN est interdit (`CLAUDE.md`), et embarquer Chart.js (250 Ko) pour
trois formes de graphe coûterait plus cher que ces fonctions de tracé. Le SVG a
l'avantage décisif de s'imprimer net et de rester lisible sur un écran modeste.

Les couleurs sont celles de la charte OFELIA (`static/css/ofelia.css`), reprises
en dur ici parce que reportlab et openpyxl ne savent pas lire une variable CSS —
et que les trois sorties doivent montrer les mêmes couleurs.
"""
from __future__ import annotations

import math
from html import escape

from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

# Charte OFELIA, dans l'ordre de passage. Voir `static/css/ofelia.css`.
PALETTE = [
    "#6B2138",  # bordeaux
    "#ED7538",  # orange
    "#3D8C5A",  # forêt
    "#F3B84C",  # ambre
    "#5A9ED4",  # ciel
    "#D1C360",  # olive
    "#F4BABA",  # rose
    "#4E1829",  # bordeaux sombre
]
INK = "#3D3530"
INK_SOFT = "#5C5550"
LINE = "#D4CEC8"

# Au-delà, un camembert devient la roue illisible du logiciel de ludothèque :
# la queue est regroupée sous « Autres ».
MAX_SLICES = 8


def color_at(index: int) -> str:
    return PALETTE[index % len(PALETTE)]


def _fmt(value: float) -> str:
    """`12`, `12,5` — jamais `12.0`, jamais de notation scientifique."""
    if value == int(value):
        return str(int(value))
    return f"{value:.1f}".replace(".", ",")


def grouped_pairs(chart) -> list[tuple[str, float]]:
    """Les parts d'un camembert, la queue regroupée sous « Autres »."""
    pairs = [(label, value) for label, value in chart.pairs() if value > 0]
    pairs.sort(key=lambda item: item[1], reverse=True)
    if len(pairs) <= MAX_SLICES:
        return pairs
    head = pairs[: MAX_SLICES - 1]
    tail = sum(value for _label, value in pairs[MAX_SLICES - 1:])
    return head + [(_("Autres"), tail)]


def slice_label(label: str, value: float, total: float) -> str:
    """« Adultes Documentaire 35 (34 %) » — ce qui s'écrit sur une tranche."""
    share = round(value / total * 100) if total else 0
    return f"{label} {_fmt(value)} ({share} %)"


# ── Histogramme ────────────────────────────────────────────────────────────


def bar_series(chart) -> list:
    """Les séries d'un histogramme, qu'il en porte une ou plusieurs.

    Un histogramme simple est le cas particulier d'un histogramme groupé à une
    série : le tracé n'a ainsi qu'un seul chemin de code, et une série ajoutée
    à un graphe existant ne demande rien d'autre.
    """
    from .pages import Series

    if chart.series:
        return [s for s in chart.series if s.values]
    return [Series(chart.unit or chart.title, list(chart.values))]


def bar_svg(chart, compact: bool = False) -> str:
    """Histogramme vertical, à une ou plusieurs séries.

    Avec plusieurs séries, les barres sont **groupées par catégorie** — les
    livres d'un rayon à côté de ses prêts — et une légende les nomme en tête.
    Empilées, elles auraient additionné des livres et des prêts, deux grandeurs
    qui ne s'additionnent pas.
    """
    width, height = (520, 250) if compact else (820, 280)
    series = bar_series(chart)
    labels = list(chart.labels)
    if not series or not labels:
        return ""

    grouped = len(series) > 1
    legend_h = 22 if grouped else 0
    pad_left, pad_right, pad_top, pad_bottom = 8, 8, 26 + legend_h, 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    top = max((max(s.values) for s in series if s.values), default=0) or 1
    slot = plot_w / len(labels)
    # Les barres d'un même groupe se serrent, avec un filet entre elles.
    group_w = min(slot * 0.72, 68 * len(series))
    bar_w = group_w / len(series)

    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" '
        f'role="img" preserveAspectRatio="xMidYMid meet" '
        f'aria-label="{escape(chart.title)}">'
    ]

    if grouped:
        x = pad_left
        for index, entry in enumerate(series):
            parts.append(
                f'<rect x="{x:.1f}" y="6" width="11" height="11" rx="3" '
                f'fill="{color_at(index)}"/>'
            )
            parts.append(
                f'<text x="{x + 16:.1f}" y="16" font-size="12" fill="{INK}">'
                f"{escape(entry.label)}</text>"
            )
            x += 26 + _text_width(entry.label, 12)

    # Ligne de base : sans elle les barres flottent.
    baseline = pad_top + plot_h
    parts.append(
        f'<line x1="{pad_left}" y1="{baseline:.1f}" x2="{width - pad_right}" '
        f'y2="{baseline:.1f}" stroke="{LINE}" stroke-width="1"/>'
    )

    value_size = 11 if grouped else 13
    for index, label in enumerate(labels):
        group_x = pad_left + slot * index + (slot - group_w) / 2
        for rank, entry in enumerate(series):
            value = entry.values[index] if index < len(entry.values) else 0
            bar_h = (value / top) * plot_h if top else 0
            x = group_x + bar_w * rank
            y = baseline - bar_h
            parts.append(
                f'<rect x="{x + 1:.1f}" y="{y:.1f}" width="{max(bar_w - 2, 1):.1f}" '
                f'height="{max(bar_h, 0):.1f}" rx="3" fill="{color_at(rank)}"/>'
            )
            if value:
                parts.append(
                    f'<text x="{x + bar_w / 2:.1f}" y="{y - 6:.1f}" '
                    f'text-anchor="middle" font-size="{value_size}" font-weight="600" '
                    f'fill="{INK}">{escape(_fmt(value))}</text>'
                )
        parts.append(
            f'<text x="{group_x + group_w / 2:.1f}" y="{baseline + 18:.1f}" '
            f'text-anchor="middle" font-size="12" fill="{INK_SOFT}">'
            f"{escape(_short(label, slot))}</text>"
        )

    parts.append("</svg>")
    return mark_safe("".join(parts))


def _short(label: str, slot: float) -> str:
    """Coupe un libellé trop long pour sa colonne, plutôt que de le chevaucher."""
    budget = max(int(slot / 7), 3)
    if len(label) <= budget:
        return label
    return label[: budget - 1] + "…"


# ── Camembert ──────────────────────────────────────────────────────────────


def pie_svg(chart, compact: bool = False) -> str:
    """Anneau dont chaque part porte son étiquette, **posée à l'extérieur**.

    Toutes les étiquettes sortent du disque et rejoignent leur part par un
    trait, exactement comme le PDF. Écrire dans la tranche ne marchait pas : un
    texte blanc posé sur une part claire, ou débordant sur le fond blanc de la
    page, devenait invisible (retour de Val). À l'extérieur, le texte est
    toujours en encre foncée sur fond blanc, quelle que soit la couleur de la
    part.
    """
    pairs = grouped_pairs(chart)
    if not pairs:
        return ""
    total = sum(value for _label, value in pairs)
    if not total:
        return ""

    # Géométrie : au large ou en demi-page. Les valeurs sont choisies pour que
    # le texte fasse à peu près la même taille à l'écran dans les deux cas —
    # un SVG s'étire à son conteneur, un dessin trop grand y devient minuscule.
    radius, font, clip, step = (86, 11, 24, 17) if compact else (
        108, 12.5, 40, LABEL_STEP
    )
    # La marge latérale se **mesure** sur les étiquettes réellement écrites, au
    # lieu d'être posée au jugé : une valeur fixe finit toujours par être trop
    # courte pour un libellé un peu long, et le texte déborde du cadre.
    longest = max(
        (_text_width(_clip(slice_label(label, value, total), clip), font)
         for label, value in pairs),
        default=0,
    )
    side = max(140, LEADER_REACH + longest + 8)
    width = radius * 2 + side * 2
    # Assez haut pour empiler toutes les étiquettes d'un même côté sans
    # chevauchement, même quand elles se pressent toutes sur une moitié.
    height = max(radius * 2 + 40, step * (len(pairs) + 1) + 30)
    cx, cy = width / 2, height / 2
    inner = radius * 0.52

    parts = [
        f'<svg class="chart-svg chart-svg--pie" viewBox="0 0 {width} {height:.0f}" '
        f'role="img" preserveAspectRatio="xMidYMid meet" '
        f'aria-label="{escape(chart.title)}">'
    ]

    angle = -math.pi / 2
    outside: list[tuple[float, str, str]] = []  # (angle médian, texte, couleur)
    for index, (label, value) in enumerate(pairs):
        sweep = 2 * math.pi * (value / total)
        color = color_at(index)
        parts.append(_slice_path(cx, cy, radius, inner, angle, sweep, color))
        outside.append((angle + sweep / 2, slice_label(label, value, total), color))
        angle += sweep

    parts.extend(_outside_labels(cx, cy, radius, outside, font, clip, step))
    parts.append("</svg>")
    return mark_safe("".join(parts))


# Hauteur d'une ligne d'étiquette déportée.
LABEL_STEP = 19

# Le trait de rappel, du bord du disque au début du texte, en trois segments.
LEADER_ELBOW = 26      # bord du disque -> coude
LEADER_DOT_GAP = 8     # coude -> pastille de couleur
LEADER_TEXT_GAP = 13   # pastille -> première lettre
# Ce que le rappel occupe en tout. Les trois termes doivent y figurer : en
# oublier un donne une marge trop courte, et le texte déborde du cadre.
LEADER_REACH = LEADER_ELBOW + LEADER_DOT_GAP + LEADER_TEXT_GAP

# Largeur moyenne d'un caractère de DM Sans, en fraction du corps. Mesurée sur
# les libellés réels des rapports — chiffres, majuscules et espaces mêlés.
# Approximation assumée : il ne s'agit que de réserver la marge, pas de
# composer au point près.
CHAR_WIDTH_RATIO = 0.58


def _text_width(text: str, font_size: float) -> float:
    return len(text) * font_size * CHAR_WIDTH_RATIO


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _outside_labels(cx, cy, radius, entries, font, clip, step) -> list[str]:
    """Étiquettes déportées, reliées par un trait, empilées sans se chevaucher.

    Deux parts voisines ont des angles voisins : posées à leur angle exact,
    leurs étiquettes se superposeraient. On les range donc verticalement, de
    chaque côté du disque, dans l'ordre où elles apparaissent sur le cercle.
    """
    if not entries:
        return []
    out: list[str] = []
    right = [e for e in entries if math.cos(e[0]) >= 0]
    left = [e for e in entries if math.cos(e[0]) < 0]

    for group, is_right in ((right, True), (left, False)):
        if not group:
            continue
        group.sort(key=lambda e: math.sin(e[0]))
        start = cy - (len(group) - 1) * step / 2
        for position, (mid, text, color) in enumerate(group):
            label_y = start + position * step
            elbow_x = cx + (radius + LEADER_ELBOW) * (1 if is_right else -1)
            text_x = elbow_x + (LEADER_DOT_GAP if is_right else -LEADER_DOT_GAP)
            x1 = cx + radius * math.cos(mid)
            y1 = cy + radius * math.sin(mid)
            x2 = cx + (radius + 12) * math.cos(mid)
            y2 = cy + (radius + 12) * math.sin(mid)
            out.append(
                f'<polyline points="{x1:.1f},{y1:.1f} {x2:.1f},{y2:.1f} '
                f'{elbow_x:.1f},{label_y:.1f}" fill="none" stroke="{color}" '
                f'stroke-width="1.3"/>'
            )
            # Une pastille de la couleur de la part, devant le texte : le trait
            # seul se perd quand deux parts voisines ont des teintes proches.
            dot_x = text_x + (2 if is_right else -8)
            out.append(
                f'<rect x="{dot_x:.1f}" y="{label_y - 4:.1f}" width="7" height="7" '
                f'rx="2" fill="{color}"/>'
            )
            anchor = "start" if is_right else "end"
            offset = LEADER_TEXT_GAP if is_right else -LEADER_TEXT_GAP
            clipped = _clip(text, clip)
            out.append(
                f'<text x="{text_x + offset:.1f}" y="{label_y + 3:.1f}" '
                f'text-anchor="{anchor}" font-size="{font}" fill="{INK}">'
                f"{escape(clipped)}</text>"
            )
    return out


def _slice_path(cx, cy, radius, inner, start, sweep, color) -> str:
    """Une part d'anneau. Un tour complet se dessine en deux demi-parts.

    Un `path` d'arc dont le début et la fin coïncident ne trace rien : une
    catégorie unique à 100 % donnerait un camembert vide.
    """
    if sweep >= 2 * math.pi - 1e-9:
        half = math.pi
        return (
            _slice_path(cx, cy, radius, inner, start, half, color)
            + _slice_path(cx, cy, radius, inner, start + half, half, color)
        )
    end = start + sweep
    large = 1 if sweep > math.pi else 0
    x1, y1 = cx + radius * math.cos(start), cy + radius * math.sin(start)
    x2, y2 = cx + radius * math.cos(end), cy + radius * math.sin(end)
    x3, y3 = cx + inner * math.cos(end), cy + inner * math.sin(end)
    x4, y4 = cx + inner * math.cos(start), cy + inner * math.sin(start)
    d = (
        f"M {x1:.2f} {y1:.2f} A {radius:.2f} {radius:.2f} 0 {large} 1 {x2:.2f} {y2:.2f} "
        f"L {x3:.2f} {y3:.2f} A {inner:.2f} {inner:.2f} 0 {large} 0 {x4:.2f} {y4:.2f} Z"
    )
    return f'<path d="{d}" fill="{color}" stroke="#FFFFFF" stroke-width="1"/>'


# ── Courbes ────────────────────────────────────────────────────────────────


def line_svg(chart, compact: bool = False) -> str:
    """Plusieurs séries dans le temps, une couleur par série, légende en haut.

    Sert aux mouvements d'usagers (arrivées, réinscriptions, départs) : trois
    tableaux de chiffres côte à côte ne montrent pas qu'une courbe croise
    l'autre, un graphe si.
    """
    width, height = (520, 280) if compact else (820, 300)
    # **Toutes** les séries sont tracées, y compris celles restées à zéro : une
    # courbe plate sur l'axe dit « on n'a perdu personne », ce qui est une
    # information. Les écarter laissait une légende qui annonçait trois courbes
    # et un dessin qui n'en montrait qu'une (retour de Val).
    series = [s for s in chart.series if s.values]
    if not series or not chart.labels:
        return ""

    pad_left, pad_right, pad_top, pad_bottom = 42, 14, 34, 40
    plot_w = width - pad_left - pad_right
    plot_h = height - pad_top - pad_bottom
    top = max((max(s.values) for s in series if s.values), default=0) or 1
    count = len(chart.labels)
    step = plot_w / max(count - 1, 1)
    baseline = pad_top + plot_h

    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {width} {height}" role="img" '
        f'preserveAspectRatio="xMidYMid meet" aria-label="{escape(chart.title)}">'
    ]

    # Quatre lignes de repère et leur graduation : sans elles, on lit des
    # formes mais aucune valeur.
    for tick in range(5):
        value = top * tick / 4
        y = baseline - (value / top) * plot_h
        parts.append(
            f'<line x1="{pad_left}" y1="{y:.1f}" x2="{width - pad_right}" y2="{y:.1f}" '
            f'stroke="{LINE}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{pad_left - 6}" y="{y + 4:.1f}" text-anchor="end" font-size="11" '
            f'fill="{INK_SOFT}">{escape(_fmt(round(value)))}</text>'
        )

    for index, entry in enumerate(series):
        color = color_at(index)
        points = " ".join(
            f"{pad_left + step * i:.1f},{baseline - (v / top) * plot_h:.1f}"
            for i, v in enumerate(entry.values)
        )
        parts.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" '
            f'stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>'
        )
        for i, value in enumerate(entry.values):
            x = pad_left + step * i
            y = baseline - (value / top) * plot_h
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}"/>'
            )

    # Libellés d'abscisse : un sur deux dès qu'il y en a trop pour la largeur.
    every = max(1, math.ceil(count / max(int(plot_w / 62), 1)))
    for i, label in enumerate(chart.labels):
        if i % every:
            continue
        parts.append(
            f'<text x="{pad_left + step * i:.1f}" y="{baseline + 18:.1f}" '
            f'text-anchor="middle" font-size="11" fill="{INK_SOFT}">'
            f"{escape(_short(label, 62))}</text>"
        )

    x = pad_left
    for index, entry in enumerate(series):
        parts.append(
            f'<rect x="{x:.1f}" y="6" width="11" height="11" rx="3" '
            f'fill="{color_at(index)}"/>'
        )
        parts.append(
            f'<text x="{x + 16:.1f}" y="16" font-size="12" fill="{INK}">'
            f"{escape(entry.label)}</text>"
        )
        x += 26 + len(entry.label) * 7

    parts.append("</svg>")
    return mark_safe("".join(parts))


def render(chart, compact: bool = False) -> str:
    """Le SVG correspondant à `chart.kind`, vide si le graphe n'a rien à montrer.

    `compact` : le graphe est posé à côté d'un tableau, sur une demi-page.
    """
    if chart.is_empty:
        return ""
    if chart.kind == "pie":
        return pie_svg(chart, compact)
    if chart.kind == "line":
        return line_svg(chart, compact)
    return bar_svg(chart, compact)
