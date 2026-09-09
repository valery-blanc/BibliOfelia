"""Export PDF d'un `ReportPage`. FEAT-093.

Un seul moteur pour les dix écrans : ce qui est à l'écran est dans le PDF, dans
le même ordre, avec les mêmes couleurs. C'est le document qu'on tend à un
donateur.

**La charte OFELIA au complet**, pas seulement ses couleurs : le PDF compose
avec les polices du site — Bricolage Grotesque pour les titres, DM Sans pour le
texte — converties en TTF par `scripts/build_pdf_fonts.py`, reportlab ne
sachant pas lire le woff2. Si les TTF manquent, on retombe sur Helvetica sans
casser la génération : un rapport moins joli vaut mieux qu'un rapport absent.
"""
from __future__ import annotations

import io
import logging
from datetime import date

from django.conf import settings
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageTemplate,
    Paragraph,
    Spacer,
    Table as PdfTable,
    TableStyle,
)

from .charts import PALETTE, grouped_pairs, slice_label
from .pages import Chart, Table

logger = logging.getLogger(__name__)

BURGUNDY = colors.HexColor("#6B2138")
INK = colors.HexColor("#3D3530")
INK_SOFT = colors.HexColor("#5C5550")
CREAM = colors.HexColor("#F7F5F0")
LINE = colors.HexColor("#D4CEC8")

MARGIN = 18 * mm
CONTENT_W = A4[0] - 2 * MARGIN

# Le logo blanc fourni par Val : « OFELIA » en lettres blanches à côté du
# pictogramme. Format large — 2560 × 688, soit un rapport de 3,72.
LOGO_RATIO = 2560 / 688
LOGO_W = 70 * mm
LOGO_H = LOGO_W / LOGO_RATIO

# Le bandeau se calcule à partir de ce qu'il contient, il n'est pas posé au
# jugé : marge haute, logo, interligne, hauteur du titre, marge basse. Une
# constante écrite à la main se désaccorde du premier changement de taille —
# c'est ainsi que le titre est venu chevaucher le logo au premier essai.
TITLE_SIZE = 24
BANNER_TOP = 8 * mm
BANNER_GAP = 7 * mm
BANNER_BOTTOM = 8 * mm
BANNER_H = BANNER_TOP + LOGO_H + BANNER_GAP + TITLE_SIZE + BANNER_BOTTOM
TITLE_BASELINE = A4[1] - BANNER_TOP - LOGO_H - BANNER_GAP - TITLE_SIZE * 0.78

# Au-delà, un tableau apparié passe en pleine largeur avec son graphe au-dessus :
# côte à côte, ses colonnes deviendraient illisibles.
SIDE_BY_SIDE_MAX_COLUMNS = 4


# ── Polices de la charte ───────────────────────────────────────────────────

FONT_DIR = settings.BASE_DIR / "static" / "fonts" / "pdf"
FONT_FILES = {
    "Ofelia": "DMSans-Regular.ttf",
    "Ofelia-Bold": "DMSans-Bold.ttf",
    "Ofelia-Title": "BricolageGrotesque-Bold.ttf",
}
_FONTS_READY: bool | None = None


def _register_fonts() -> bool:
    """Enregistre les polices OFELIA auprès de reportlab. Vrai si disponibles.

    Le résultat est mémorisé : l'enregistrement est global à reportlab, le
    refaire à chaque rapport relirait trois fichiers pour rien.
    """
    global _FONTS_READY
    if _FONTS_READY is not None:
        return _FONTS_READY

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    try:
        for name, filename in FONT_FILES.items():
            path = FONT_DIR / filename
            if not path.exists():
                raise FileNotFoundError(path)
            pdfmetrics.registerFont(TTFont(name, str(path)))
        pdfmetrics.registerFontFamily(
            "Ofelia", normal="Ofelia", bold="Ofelia-Bold",
            italic="Ofelia", boldItalic="Ofelia-Bold",
        )
        _FONTS_READY = True
    except Exception as exc:  # pragma: no cover — dépend des fichiers installés
        logger.warning(
            "Polices OFELIA indisponibles (%s) : le PDF sort en Helvetica. "
            "Lancer `python scripts/build_pdf_fonts.py`.", exc,
        )
        _FONTS_READY = False
    return _FONTS_READY


def _fonts() -> dict[str, str]:
    """Les trois noms de police à utiliser, charte ou repli Helvetica."""
    if _register_fonts():
        return {"body": "Ofelia", "bold": "Ofelia-Bold", "title": "Ofelia-Title"}
    return {"body": "Helvetica", "bold": "Helvetica-Bold", "title": "Helvetica-Bold"}


def _logo() -> ImageReader | None:
    """Le logo blanc, pour le bandeau bordeaux. Repli sur le logo couleur."""
    for name in ("ofelia-logo-white.png", "ofelia-logo.png"):
        try:
            path = settings.BASE_DIR / "static" / "img" / name
            if path.exists():
                return ImageReader(str(path))
        except Exception as exc:  # pragma: no cover — dépend du système de fichiers
            logger.warning("Logo rapport : %s", exc)
    return None


def _library_name() -> str:
    from apps.core.models import Setting

    return Setting.get("library_name", "BibliOfelia")


def _styles() -> dict:
    base = getSampleStyleSheet()
    font = _fonts()
    return {
        "font": font,
        "sub": ParagraphStyle(
            "rSub", parent=base["Normal"], fontName=font["body"],
            fontSize=10, leading=13, textColor=INK_SOFT,
        ),
        "h2": ParagraphStyle(
            "rH2", parent=base["Heading2"], fontName=font["title"],
            fontSize=15, leading=18, textColor=BURGUNDY,
            spaceBefore=12, spaceAfter=6,
        ),
        "cell": ParagraphStyle(
            "rCell", parent=base["Normal"], fontName=font["body"],
            fontSize=8.5, leading=10.5, textColor=INK,
        ),
        # Les en-têtes de tableau sont posés sur un fond bordeaux : le texte y
        # est **blanc**. Le `TEXTCOLOR` de la table ne suffit pas — la couleur
        # portée par le style d'un `Paragraph` l'emporte, et l'en-tête sortait
        # en noir sur bordeaux, illisible.
        "head": ParagraphStyle(
            "rHead", parent=base["Normal"], fontName=font["bold"],
            fontSize=8.5, leading=10.5, textColor=colors.white,
        ),
        "head_narrow": ParagraphStyle(
            "rHeadNarrow", parent=base["Normal"], fontName=font["bold"],
            fontSize=7, leading=8.5, textColor=colors.white,
        ),
        "total": ParagraphStyle(
            "rTotal", parent=base["Normal"], fontName=font["bold"],
            fontSize=8.5, leading=10.5, textColor=INK,
        ),
        "note": ParagraphStyle(
            "rNote", parent=base["Normal"], fontName=font["body"],
            fontSize=8, leading=10, textColor=INK_SOFT,
        ),
    }


def render_report_pdf(page, block=None) -> bytes:
    """Rend `page` en A4 portrait. `block` limite le PDF à un sous-rapport."""
    buf = io.BytesIO()
    styles = _styles()
    font = styles["font"]
    library = _library_name()
    heading = block.title if block is not None else page.title

    def banner(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BURGUNDY)
        canvas.rect(0, A4[1] - BANNER_H, A4[0], BANNER_H, stroke=0, fill=1)

        # ── Le logo, en grand, en haut à gauche ──
        logo_top = A4[1] - BANNER_TOP
        logo = _logo()
        if logo is not None:
            try:
                canvas.drawImage(
                    logo, MARGIN, logo_top - LOGO_H, width=LOGO_W, height=LOGO_H,
                    preserveAspectRatio=True, anchor="nw", mask="auto",
                )
            except Exception as exc:  # pragma: no cover
                logger.warning("Logo rapport non dessiné : %s", exc)
                logo = None
        if logo is None:
            canvas.setFillColor(colors.white)
            canvas.setFont(font["title"], 26)
            canvas.drawString(MARGIN, logo_top - LOGO_H * 0.75, "OFELIA")

        # Le nom de la bibliothèque à droite, aligné sur le logo : le logo dit
        # l'association, pas l'établissement.
        canvas.setFillColor(colors.white)
        canvas.setFont(font["body"], 11)
        canvas.drawRightString(A4[0] - MARGIN, logo_top - LOGO_H * 0.55, library)

        # ── Le titre du rapport, en grand, sous le logo ──
        canvas.setFont(font["title"], TITLE_SIZE)
        canvas.drawString(MARGIN, TITLE_BASELINE, heading)

        # ── La période, précédée d'un calendrier, sur la ligne du titre ──
        if page.period:
            label = page.period.label
            size = 11
            canvas.setFont(font["body"], size)
            width = canvas.stringWidth(label, font["body"], size)
            right = A4[0] - MARGIN
            icon = 4.6 * mm
            _calendar_icon(canvas, right - width - icon - 2.5 * mm,
                           TITLE_BASELINE - 0.6 * mm, icon)
            canvas.setFillColor(colors.white)
            canvas.drawRightString(right, TITLE_BASELINE, label)

        # ── Pied de page ──
        canvas.setFillColor(INK_SOFT)
        canvas.setFont(font["body"], 7.5)
        canvas.drawString(
            MARGIN, 10 * mm,
            _("Édité par BibliOfelia le %(d)s.") % {"d": date.today().strftime("%d/%m/%Y")},
        )
        canvas.drawRightString(A4[0] - MARGIN, 10 * mm, _("Page %(n)s") % {"n": doc.page})
        canvas.restoreState()

    doc = BaseDocTemplate(
        buf, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=BANNER_H + 8 * mm, bottomMargin=16 * mm, title=heading,
    )
    frame = Frame(
        MARGIN, 16 * mm, CONTENT_W, A4[1] - BANNER_H - 24 * mm, id="body",
        leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="report", frames=[frame], onPage=banner)])

    story = []
    if block is None:
        if page.subtitle:
            story.append(Paragraph(page.subtitle, styles["sub"]))
            story.append(Spacer(1, 4 * mm))
        if page.note:
            story.append(Paragraph(page.note, styles["note"]))
            story.append(Spacer(1, 3 * mm))
        if page.kpis:
            story.append(_kpi_grid(page.kpis, styles))
            story.append(Spacer(1, 6 * mm))
        blocks = page.blocks
    else:
        # Un sous-rapport exporté seul : son titre est déjà dans le bandeau,
        # inutile de le répéter en tête de page.
        story.append(Paragraph(page.title, styles["sub"]))
        story.append(Spacer(1, 4 * mm))
        blocks = [block]

    for item in blocks:
        if isinstance(item, Table):
            story.extend(_table_flowables(item, styles))
        elif isinstance(item, Chart):
            story.extend(_chart_flowables(item, styles, CONTENT_W))

    doc.build(story)
    return buf.getvalue()


def _calendar_icon(canvas, x, y, size) -> None:
    """Un petit calendrier tracé au trait — même dessin que l'icône de l'écran.

    Dessiné plutôt qu'importé : les icônes du site sont des SVG, que reportlab
    ne sait pas poser directement, et cinq traits coûtent moins qu'un
    convertisseur.
    """
    canvas.saveState()
    canvas.setStrokeColor(colors.white)
    canvas.setFillColor(colors.white)
    canvas.setLineWidth(0.9)
    canvas.roundRect(x, y, size, size * 0.88, size * 0.12, stroke=1, fill=0)
    # La ligne d'en-tête du calendrier, et les deux anneaux au-dessus.
    top = y + size * 0.88
    canvas.line(x, top - size * 0.26, x + size, top - size * 0.26)
    for offset in (0.28, 0.72):
        canvas.line(x + size * offset, top, x + size * offset, top + size * 0.16)
    canvas.restoreState()


def _kpi_grid(kpis, styles, per_row: int = 4):
    """Les compteurs en cartouches crème, quatre par ligne."""
    font = styles["font"]
    label_style = ParagraphStyle(
        "kpiLabel", parent=styles["note"], fontSize=7.5, alignment=1, leading=9
    )
    value_style = ParagraphStyle(
        "kpiValue", parent=styles["cell"], fontName=font["title"],
        fontSize=16, alignment=1, leading=18,
    )
    hint_style = ParagraphStyle(
        "kpiHint", parent=styles["note"], fontSize=6.5, alignment=1, leading=8
    )

    rows, cells = [], []
    for kpi in kpis:
        stack = [Paragraph(str(kpi.value), value_style), Paragraph(kpi.label, label_style)]
        if kpi.hint:
            stack.append(Paragraph(kpi.hint, hint_style))
        cells.append(PdfTable([[flow] for flow in stack], colWidths=[CONTENT_W / per_row - 4]))
        if len(cells) == per_row:
            rows.append(cells)
            cells = []
    if cells:
        cells += [""] * (per_row - len(cells))
        rows.append(cells)

    grid = PdfTable(rows, colWidths=[CONTENT_W / per_row] * per_row)
    grid.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), CREAM),
        ("BOX", (0, 0), (-1, -1), 0.4, LINE),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return grid


def _table_flowables(block, styles) -> list:
    """Le tableau, et son graphe apparié posé à sa droite quand il tient."""
    out = [Paragraph(block.title, styles["h2"])]
    if not block.rows:
        out.append(Paragraph(block.empty_text or _("Rien à afficher."), styles["note"]))
        return out + [Spacer(1, 4 * mm)]

    paired = block.chart is not None and not block.chart.is_empty
    side_by_side = paired and len(block.columns) <= SIDE_BY_SIDE_MAX_COLUMNS

    if side_by_side:
        half = CONTENT_W / 2
        table = _plain_table(block, styles, half - 4 * mm, narrow=True)
        drawing = _chart_drawing(block.chart, half - 4 * mm, styles)
        pair = PdfTable([[table, drawing]], colWidths=[half, half])
        pair.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        out.append(pair)
    else:
        out.append(_plain_table(block, styles, CONTENT_W))
        if paired:
            out.append(Spacer(1, 3 * mm))
            out.append(_chart_drawing(block.chart, CONTENT_W, styles))

    if block.note:
        out.append(Spacer(1, 1.5 * mm))
        out.append(Paragraph(block.note, styles["note"]))
    out.append(Spacer(1, 5 * mm))
    return out


# Marge intérieure d'une cellule, gauche + droite : reportlab pose 6 points de
# chaque côté par défaut, et le tableau plus bas ne les redéfinit pas.
CELL_PADDING = 12
# Plafond de la largeur *souhaitée* d'une colonne, quand la place manque : un
# titre de livre de cent caractères affamerait sinon toutes les autres. Quand
# le tableau tient au large, le surplus se répartit au prorata et une colonne
# peut dépasser ce plafond — personne n'est lésé, l'espace est libre.
MAX_COLUMN_SHARE = 0.5
# Au-delà, mesurer chaque ligne coûte plus que le gain de précision — les
# premières suffisent à dire la largeur du contenu.
MEASURED_ROWS = 80


def _column_widths(block, styles, total_width, narrow: bool) -> list[float]:
    """Largeur de chaque colonne, mesurée sur le texte qu'elle contient.

    Des proportions fixes ne marchent pas : la même règle qui laisse respirer un
    titre de livre coupe « Réinscriptions » en deux dans un tableau de quatre
    colonnes posé sur une demi-page. On mesure donc, pour chaque colonne, la
    largeur de son en-tête et de ses valeurs, puis on répartit.

    Deux largeurs par colonne : la **naturelle**, celle qui éviterait tout
    retour à la ligne, et la **minimale**, celle du plus long mot insécable.
    Quand tout ne tient pas, on rogne sur l'écart entre les deux — jamais en
    dessous du mot le plus long, qui se briserait en plein milieu.
    """
    from reportlab.pdfbase.pdfmetrics import stringWidth

    font = styles["font"]
    head_size = (styles["head_narrow"] if narrow else styles["head"]).fontSize
    cell_size = styles["cell"].fontSize
    cap = total_width * MAX_COLUMN_SHARE

    natural: list[float] = []
    minimum: list[float] = []
    for index, column in enumerate(block.columns):
        values = [str(row[index]) for row in block.rows[:MEASURED_ROWS] if len(row) > index]
        head_full = stringWidth(column.label, font["bold"], head_size)
        head_word = max(
            (stringWidth(word, font["bold"], head_size) for word in column.label.split()),
            default=0,
        )
        cell_full = max(
            (stringWidth(value, font["body"], cell_size) for value in values), default=0
        )
        cell_word = max(
            (
                stringWidth(word, font["body"], cell_size)
                for value in values
                for word in value.split()
            ),
            default=0,
        )
        natural.append(min(max(head_full, cell_full) + CELL_PADDING, cap))
        minimum.append(min(max(head_word, cell_word) + CELL_PADDING, cap))

    total_natural = sum(natural)
    if total_natural <= total_width:
        # Il reste de la place : on la distribue au prorata plutôt que de
        # laisser une bande blanche à droite du tableau.
        factor = total_width / total_natural if total_natural else 1
        return [width * factor for width in natural]

    slack = [max(n - m, 0) for n, m in zip(natural, minimum)]
    total_slack = sum(slack)
    excess = total_natural - total_width
    if total_slack:
        taken = min(excess, total_slack)
        widths = [n - s * taken / total_slack for n, s in zip(natural, slack)]
        excess -= taken
    else:
        widths = list(natural)

    if excess > 0:
        # Même réduits au mot le plus long, les colonnes débordent : on rétrécit
        # tout, en acceptant qu'un mot se coupe. Mieux vaut cela qu'un tableau
        # plus large que la page.
        factor = total_width / sum(widths)
        widths = [width * factor for width in widths]
    return widths


def _plain_table(block, styles, total_width, narrow: bool = False):
    """Le tableau seul. `narrow` = posé sur une demi-page, à côté de son graphe.

    À demi-largeur, un en-tête composé au même corps se coupe en plein mot
    (« Réinscri / ptions ») : on réduit le corps et on rend à la première
    colonne un peu de la place qu'elle prenait.
    """
    head_style = styles["head_narrow"] if narrow else styles["head"]
    head = [Paragraph(c.label, head_style) for c in block.columns]
    body = [
        [Paragraph(str(value), styles["cell"]) for value in row]
        for row in block.rows
    ]
    data = [head] + body
    if block.total_row:
        data.append([Paragraph(str(v), styles["total"]) for v in block.total_row])

    widths = _column_widths(block, styles, total_width, narrow)

    table = PdfTable(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), BURGUNDY),
        ("GRID", (0, 0), (-1, -1), 0.3, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREAM]),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    for index, column in enumerate(block.columns):
        if column.align == "right":
            style.append(("ALIGN", (index, 0), (index, -1), "RIGHT"))
    if block.total_row:
        style.append(("BACKGROUND", (0, -1), (-1, -1), CREAM))
    table.setStyle(TableStyle(style))
    return table


def _chart_flowables(block, styles, width) -> list:
    if block.is_empty:
        return [
            Paragraph(block.title, styles["h2"]),
            Paragraph(_("Rien à afficher."), styles["note"]),
            Spacer(1, 4 * mm),
        ]
    out = [KeepTogether([
        Paragraph(block.title, styles["h2"]),
        _chart_drawing(block, width, styles),
    ])]
    if block.note:
        out.append(Paragraph(block.note, styles["note"]))
    out.append(Spacer(1, 4 * mm))
    return out


def _chart_drawing(block, width, styles):
    """Le graphe redessiné avec `reportlab.graphics`, mêmes couleurs qu'à l'écran."""
    from reportlab.graphics.charts.barcharts import VerticalBarChart
    from reportlab.graphics.charts.legends import Legend
    from reportlab.graphics.charts.linecharts import HorizontalLineChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.shapes import Drawing

    palette = [colors.HexColor(c) for c in PALETTE]
    font = styles["font"]

    if block.kind == "pie":
        return _pie_drawing(block, width, palette, font, Drawing, Pie)
    if block.kind == "line":
        return _line_drawing(
            block, width, palette, font, Drawing, HorizontalLineChart, Legend
        )
    return _bar_drawing(block, width, palette, font, Drawing, VerticalBarChart)


def _pie_drawing(block, width, palette, font, Drawing, Pie):
    """Camembert dont **chaque part porte son étiquette**, comme à l'écran.

    reportlab pose les étiquettes autour du disque et écarte lui-même celles qui
    se chevaucheraient (`sideLabels`) : c'est exactement ce qu'il faut pour les
    petites parts, et cela évite d'écrire un placeur d'étiquettes de plus.
    """
    pairs = grouped_pairs(block)
    total = sum(value for _l, value in pairs) or 1
    height = max(74 * mm, 12 * mm + len(pairs) * 7 * mm)
    drawing = Drawing(width, height)
    pie = Pie()
    pie.width = pie.height = min(56 * mm, height - 16 * mm)
    pie.x = (width - pie.width) / 2
    pie.y = (height - pie.height) / 2
    pie.data = [value for _label, value in pairs]
    pie.labels = [slice_label(label, value, total) for label, value in pairs]
    pie.sideLabels = 1
    pie.sideLabelsOffset = 0.08
    pie.slices.fontName = font["body"]
    pie.slices.fontSize = 7
    pie.slices.labelRadius = 1.12
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1
    for index in range(len(pairs)):
        pie.slices[index].fillColor = palette[index % len(palette)]
    drawing.add(pie)
    return drawing


def _bar_drawing(block, width, palette, font, Drawing, VerticalBarChart):
    """Histogramme, à une ou plusieurs séries.

    Avec plusieurs séries, reportlab groupe les barres par catégorie et une
    légende les nomme — comme le SVG de l'écran.
    """
    from reportlab.graphics.charts.legends import Legend

    from .charts import bar_series

    series = bar_series(block)
    labels = list(block.labels)
    grouped = len(series) > 1
    height = (72 if grouped else 62) * mm
    drawing = Drawing(width, height)

    bars = VerticalBarChart()
    bars.x, bars.y = 8 * mm, 12 * mm
    bars.width = width - 14 * mm
    bars.height = height - (30 if grouped else 20) * mm
    bars.data = [list(entry.values) for entry in series]
    for index in range(len(series)):
        bars.bars[index].fillColor = palette[index % len(palette)]
    bars.bars.strokeColor = None
    bars.groupSpacing = 6
    bars.barSpacing = 0.5
    bars.valueAxis.valueMin = 0
    bars.valueAxis.labels.fontName = font["body"]
    bars.valueAxis.labels.fontSize = 7
    bars.categoryAxis.categoryNames = _axis_labels(labels, bars.width)
    bars.categoryAxis.labels.fontName = font["body"]
    bars.categoryAxis.labels.fontSize = 7
    bars.categoryAxis.labels.angle = 30 if len(labels) > 8 else 0
    bars.categoryAxis.labels.boxAnchor = "ne" if len(labels) > 8 else "n"
    bars.categoryAxis.labels.dy = -3
    bars.barLabels.fontName = font["bold"]
    bars.barLabels.fontSize = 6.5 if grouped else 7
    bars.barLabelFormat = "%d"
    bars.barLabels.nudge = 6
    drawing.add(bars)

    if grouped:
        legend = Legend()
        legend.x, legend.y = 8 * mm, height - 4 * mm
        legend.fontName, legend.fontSize = font["body"], 7
        legend.dx = legend.dy = 5
        legend.deltay = 9
        legend.columnMaximum = 1
        legend.alignment = "right"
        legend.colorNamePairs = [
            (palette[index % len(palette)], entry.label)
            for index, entry in enumerate(series)
        ]
        drawing.add(legend)
    return drawing


def _line_drawing(block, width, palette, font, Drawing, HorizontalLineChart, Legend):
    series = [s for s in block.series if s.values]
    height = 68 * mm
    drawing = Drawing(width, height)
    lines = HorizontalLineChart()
    lines.x, lines.y = 10 * mm, 18 * mm
    lines.width = width - 16 * mm
    lines.height = height - 30 * mm
    lines.data = [list(s.values) for s in series]
    lines.categoryAxis.categoryNames = _axis_labels(list(block.labels), lines.width)
    lines.categoryAxis.labels.fontName = font["body"]
    lines.categoryAxis.labels.fontSize = 6.5
    lines.categoryAxis.labels.angle = 30 if len(block.labels) > 8 else 0
    lines.categoryAxis.labels.boxAnchor = "ne" if len(block.labels) > 8 else "n"
    lines.valueAxis.valueMin = 0
    lines.valueAxis.labels.fontName = font["body"]
    lines.valueAxis.labels.fontSize = 6.5
    for index in range(len(series)):
        lines.lines[index].strokeColor = palette[index % len(palette)]
        lines.lines[index].strokeWidth = 1.6
        lines.lines[index].symbol = _dot(palette[index % len(palette)])
    drawing.add(lines)

    legend = Legend()
    legend.x, legend.y = 10 * mm, height - 4 * mm
    legend.fontName, legend.fontSize = font["body"], 7
    legend.dx = legend.dy = 5
    legend.deltay = 9
    legend.columnMaximum = 1
    legend.alignment = "right"
    legend.colorNamePairs = [
        (palette[index % len(palette)], entry.label)
        for index, entry in enumerate(series)
    ]
    drawing.add(legend)
    return drawing


def _dot(color):
    from reportlab.graphics.widgets.markers import makeMarker

    marker = makeMarker("FilledCircle")
    marker.strokeColor = color
    marker.fillColor = color
    marker.size = 3
    return marker


def _axis_labels(labels: list[str], width: float) -> list[str]:
    """Raccourcit les libellés d'abscisse trop longs pour leur colonne.

    reportlab n'écourte rien : « septembre 2025 » douze fois de suite se
    chevauche jusqu'à devenir une bouillie grise. Le SVG de l'écran applique la
    même règle (`charts._short`), et le mois se lit à ses trois premières
    lettres.
    """
    if not labels:
        return labels
    slot = width / len(labels)
    budget = max(int(slot / 3.6), 4)
    out = []
    for label in labels:
        if len(label) <= budget:
            out.append(label)
            continue
        head, _sep, year = label.rpartition(" ")
        # « septembre 2025 » → « sept. 2025 » : on ampute le mois, jamais
        # l'année, qui distingue deux barres identiques d'une année sur l'autre.
        if head and year.isdigit():
            keep = max(budget - len(year) - 2, 3)
            out.append(f"{head[:keep]}. {year}")
        else:
            out.append(label[: budget - 1] + "…")
    return out
