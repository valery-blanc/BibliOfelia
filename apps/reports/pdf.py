"""Génération PDF pour le rapport annuel d'activité. SPEC §6.6.

Utilise reportlab (déjà dans requirements.txt pour les étiquettes Task #12).
"""
from __future__ import annotations

import io
from datetime import date

from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .services import AnnualReport


def render_annual_pdf(report: AnnualReport, library_name: str = "BibliOfelia") -> bytes:
    """Rend `report` en PDF A4 et renvoie les bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(library_name, styles["Title"]))
    story.append(Paragraph(
        _("Rapport annuel d'activité — %(year)s") % {"year": report.year},
        styles["Heading2"],
    ))
    story.append(Paragraph(
        _("Période : du %(s)s au %(e)s") % {
            "s": report.period_start.isoformat(),
            "e": report.period_end.isoformat(),
        },
        styles["Italic"],
    ))
    story.append(Spacer(1, 0.6 * cm))

    rows = [
        [_("Prêts total"), report.loans_total],
        [_("Prêts retournés"), report.loans_returned],
        [_("Prêts en retard"), report.loans_overdue],
        [_("Prêts perdus"), report.loans_lost],
        [_("Usagers actifs sur la période"), report.members_active],
        [_("Usagers inscrits (total)"), report.members_total],
        [_("Notices ajoutées"), report.records_added],
        [_("Exemplaires ajoutés"), report.items_added],
    ]
    tbl = Table(rows, colWidths=[10 * cm, 4 * cm])
    tbl.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.8 * cm))

    if report.top:
        story.append(Paragraph(_("Top 10 ouvrages empruntés"), styles["Heading3"]))
        top_rows = [[_("Titre"), _("Prêts")]]
        for entry in report.top:
            top_rows.append([entry["title"][:80], entry["count"]])
        top_tbl = Table(top_rows, colWidths=[12 * cm, 2 * cm])
        top_tbl.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("ALIGN", (1, 1), (1, -1), "RIGHT"),
        ]))
        story.append(top_tbl)

    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        _("Édité par BibliOfelia le %(d)s.") % {"d": date.today().isoformat()},
        styles["Italic"],
    ))
    doc.build(story)
    return buf.getvalue()
