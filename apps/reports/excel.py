"""Export Excel d'un `ReportPage`. FEAT-093.

Un onglet « Résumé » avec les compteurs, puis un onglet par sous-rapport. Les
graphes sortent en graphique Excel **natif** posé au-dessus de ses données : un
membre du comité peut ainsi recopier le camembert dans une présentation sans
redessiner quoi que ce soit. Un tableau accompagné de son graphe les met tous
les deux sur la même feuille, comme à l'écran.

openpyxl est déjà une dépendance (import/export du catalogue, FEAT-050/078).
"""
from __future__ import annotations

import io
import re

from django.utils.translation import gettext as _

from .charts import PALETTE, grouped_pairs
from .pages import Chart, Table

_HEADER_FILL = "6B2138"  # bordeaux OFELIA
_TITLE_FILL = "F7F5F0"  # crème


def _sheet_name(raw: str, used: set[str]) -> str:
    """Excel refuse `[]:*?/\\`, tronque à 31 caractères et exige l'unicité."""
    name = re.sub(r"[\[\]:*?/\\]", " ", raw).strip()[:31] or _("Feuille")
    candidate, suffix = name, 2
    while candidate.lower() in used:
        candidate = f"{name[:28]}~{suffix}"
        suffix += 1
    used.add(candidate.lower())
    return candidate


def render_report_xlsx(page, block=None) -> bytes:
    """Rend `page` en classeur. `block` limite le fichier à un sous-rapport."""
    import openpyxl
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = openpyxl.Workbook()
    used: set[str] = set()
    bold = Font(bold=True)
    white_bold = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor=_HEADER_FILL)

    def style_header(ws, row: int, count: int) -> None:
        for col in range(1, count + 1):
            cell = ws.cell(row=row, column=col)
            cell.font = white_bold
            cell.fill = header_fill
            cell.alignment = Alignment(vertical="center", wrap_text=True)
        ws.freeze_panes = ws.cell(row=row + 1, column=1)

    blocks = page.blocks if block is None else [block]

    # ── Onglet Résumé ──
    ws = wb.active
    ws.title = _sheet_name(_("Résumé"), used)
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 20
    ws.column_dimensions["C"].width = 34

    ws.append([block.title if block is not None else page.title])
    ws["A1"].font = Font(bold=True, size=14)
    ws.append([page.title if block is not None else page.subtitle])
    if page.period:
        ws.append([_("Période"), page.period.label])
        ws.append([_("Du"), page.period.start, _("au")])
        ws.cell(row=ws.max_row, column=4, value=page.period.end)
    ws.append([])

    if block is None and page.kpis:
        kpi_header = ws.max_row + 1
        ws.append([_("Chiffre"), _("Valeur"), _("Précision")])
        style_header(ws, kpi_header, 3)
        for kpi in page.kpis:
            ws.append([kpi.label, kpi.value, kpi.hint])

    # ── Un onglet par sous-rapport, dans l'ordre de l'écran ──
    for item in blocks:
        if isinstance(item, Table):
            sheet = wb.create_sheet(_sheet_name(item.title, used))
            last_col = _write_table(sheet, item, bold, style_header, get_column_letter,
                                    Alignment, PatternFill)
            if item.chart is not None and not item.chart.is_empty:
                # Le graphe apparié va sur la même feuille, à droite du tableau :
                # à l'écran il est à côté, le fichier doit le refléter.
                _write_chart(sheet, item.chart, anchor_col=last_col + 2,
                             bold=bold, style_header=style_header,
                             get_column_letter=get_column_letter)
        elif isinstance(item, Chart):
            sheet = wb.create_sheet(_sheet_name(item.title, used))
            sheet.append([item.title])
            sheet["A1"].font = bold
            sheet["A1"].fill = PatternFill("solid", fgColor=_TITLE_FILL)
            sheet.append([])
            _write_chart(sheet, item, anchor_col=1, bold=bold,
                         style_header=style_header,
                         get_column_letter=get_column_letter, start_row=3)

    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _write_table(sheet, block, bold, style_header, get_column_letter,
                 Alignment, PatternFill) -> int:
    sheet.append([block.title])
    sheet["A1"].font = bold
    sheet["A1"].fill = PatternFill("solid", fgColor=_TITLE_FILL)
    sheet.append([])
    head_row = sheet.max_row + 1
    sheet.append([column.label for column in block.columns])
    style_header(sheet, head_row, len(block.columns))
    for row in block.rows:
        sheet.append(list(row))
    if block.total_row:
        sheet.append(list(block.total_row))
        for col in range(1, len(block.total_row) + 1):
            sheet.cell(row=sheet.max_row, column=col).font = bold

    for col, column in enumerate(block.columns, start=1):
        # Largeur : le plus long des cent premières valeurs, sinon l'en-tête.
        # Les lignes plus courtes que l'en-tête existent (une ligne de total
        # laisse des cases vides) : on les ignore plutôt que d'indexer hors
        # bornes.
        widths = [len(str(column.label))] + [
            len(str(row[col - 1])) for row in block.rows[:100] if len(row) >= col
        ]
        sheet.column_dimensions[get_column_letter(col)].width = min(
            max(max(widths) + 3, 12), 60
        )
        if column.align == "right":
            for row_idx in range(head_row + 1, sheet.max_row + 1):
                sheet.cell(row=row_idx, column=col).alignment = Alignment(
                    horizontal="right"
                )
    return len(block.columns)


def _write_chart(sheet, chart, anchor_col, bold, style_header,
                 get_column_letter, start_row: int | None = None) -> None:
    """Écrit les données du graphe puis le graphe Excel natif au-dessus."""
    from openpyxl.chart import BarChart, LineChart, PieChart, Reference
    from openpyxl.chart.series import DataPoint

    first_row = start_row if start_row is not None else 1
    label_col = anchor_col

    # Courbes et histogramme groupé s'écrivent de la même façon : une colonne
    # de libellés, puis une colonne par série. Seul le type de graphique Excel
    # posé au-dessus diffère.
    if chart.series:
        series = [s for s in chart.series if s.values]
        if not series or not chart.labels:
            return
        sheet.cell(row=first_row, column=label_col, value=_("Libellé"))
        for offset, entry in enumerate(series, start=1):
            sheet.cell(row=first_row, column=label_col + offset, value=entry.label)
        style_header(sheet, first_row, label_col + len(series))
        for index, label in enumerate(chart.labels, start=1):
            sheet.cell(row=first_row + index, column=label_col, value=label)
            for offset, entry in enumerate(series, start=1):
                value = entry.values[index - 1] if index - 1 < len(entry.values) else 0
                sheet.cell(row=first_row + index, column=label_col + offset, value=value)
        last = first_row + len(chart.labels)
        graph = BarChart() if chart.kind == "bar" else LineChart()
        graph.title = chart.title
        data = Reference(sheet, min_col=label_col + 1, max_col=label_col + len(series),
                         min_row=first_row, max_row=last)
        graph.add_data(data, titles_from_data=True)
        graph.set_categories(
            Reference(sheet, min_col=label_col, min_row=first_row + 1, max_row=last)
        )
        for index in range(len(series)):
            color = PALETTE[index % len(PALETTE)].lstrip("#")
            if chart.kind == "bar":
                # Barres groupées par catégorie, jamais empilées : additionner
                # des livres et des prêts ne veut rien dire.
                graph.type = "col"
                graph.grouping = "clustered"
                graph.overlap = -10
                graph.series[index].graphicalProperties.solidFill = color
            else:
                graph.series[index].graphicalProperties.line.solidFill = color
                graph.series[index].graphicalProperties.line.width = 22000
                graph.series[index].smooth = False
        graph.height, graph.width = 9, 18
        sheet.add_chart(graph, f"{get_column_letter(label_col)}{last + 3}")
        sheet.column_dimensions[get_column_letter(label_col)].width = 20
        return

    pairs = grouped_pairs(chart) if chart.kind == "pie" else chart.pairs()
    if not pairs:
        return
    sheet.cell(row=first_row, column=label_col, value=_("Libellé"))
    sheet.cell(row=first_row, column=label_col + 1, value=chart.unit or _("Valeur"))
    style_header(sheet, first_row, label_col + 1)
    for index, (label, value) in enumerate(pairs, start=1):
        sheet.cell(row=first_row + index, column=label_col, value=label)
        sheet.cell(row=first_row + index, column=label_col + 1, value=value)
    last = first_row + len(pairs)

    graph = PieChart() if chart.kind == "pie" else BarChart()
    graph.title = chart.title
    graph.add_data(
        Reference(sheet, min_col=label_col + 1, min_row=first_row, max_row=last),
        titles_from_data=True,
    )
    graph.set_categories(
        Reference(sheet, min_col=label_col, min_row=first_row + 1, max_row=last)
    )
    graph.height, graph.width = 9, 18
    if chart.kind == "pie":
        # Sans couleur explicite, Excel repart sur sa palette bleue : le
        # camembert du fichier ne ressemblerait plus à celui de l'écran ni à
        # celui du PDF.
        graph.dataLabels = _pie_labels()
        series = graph.series[0]
        for point_index in range(len(pairs)):
            point = DataPoint(idx=point_index)
            point.graphicalProperties.solidFill = PALETTE[
                point_index % len(PALETTE)
            ].lstrip("#")
            series.data_points.append(point)
    else:
        graph.legend = None
        graph.series[0].graphicalProperties.solidFill = PALETTE[0].lstrip("#")
    sheet.add_chart(graph, f"{get_column_letter(label_col)}{last + 3}")
    sheet.column_dimensions[get_column_letter(label_col)].width = 26


def _pie_labels():
    """Nom, valeur et pourcentage **sur les parts** — comme à l'écran et au PDF."""
    from openpyxl.chart.label import DataLabelList

    labels = DataLabelList()
    labels.showCatName = True
    labels.showVal = True
    labels.showPercent = True
    labels.showSerName = False
    labels.showLegendKey = False
    return labels
