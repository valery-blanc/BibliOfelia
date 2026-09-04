"""Facture A4. FEAT-084.

Charte OFELIA réutilisée telle quelle : logo `static/img/ofelia-logo.png` et
bordeaux `#6B2138` de `static/css/ofelia.css`. Rien n'est réinventé ici.

reportlab est déjà une dépendance (étiquettes et rapport annuel) ; les polices
OFELIA sont des `.woff2`, que reportlab ne sait pas embarquer — on reste sur
Helvetica pour le texte, comme les étiquettes et les cartes.
"""
from __future__ import annotations

import io
import logging

from django.conf import settings
from django.utils.translation import gettext as _
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from .models import InvoiceStatus
from .money import format_amount

logger = logging.getLogger(__name__)

BURGUNDY = colors.HexColor("#6B2138")
INK = colors.HexColor("#3D3530")
INK_SOFT = colors.HexColor("#7A6E66")
CREAM = colors.HexColor("#F7F5F0")

MARGIN = 20 * mm


def _logo() -> ImageReader | None:
    try:
        path = settings.BASE_DIR / "static" / "img" / "ofelia-logo.png"
        return ImageReader(str(path)) if path.exists() else None
    except Exception as exc:  # pragma: no cover — dépend du système de fichiers
        logger.warning("Logo facture : %s", exc)
        return None


def _library() -> dict:
    from apps.core.models import Setting

    identity = Setting.get("library_identity", {}) or {}
    return {
        "name": Setting.get("library_name", identity.get("name", "BibliOfelia")),
        "address": identity.get("address", ""),
        "country": identity.get("country", ""),
        "email": identity.get("email", ""),
        "phone": identity.get("phone", ""),
    }


def render_invoice_pdf(invoice) -> bytes:
    """Rend `invoice` en A4 et renvoie les octets du PDF."""
    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    library = _library()

    # ── Bandeau ──
    pdf.setFillColor(BURGUNDY)
    pdf.rect(0, height - 32 * mm, width, 32 * mm, stroke=0, fill=1)
    logo = _logo()
    text_x = MARGIN
    if logo is not None:
        try:
            pdf.drawImage(
                logo, MARGIN, height - 26 * mm, width=18 * mm, height=18 * mm,
                preserveAspectRatio=True, anchor="sw", mask="auto",
            )
            text_x = MARGIN + 23 * mm
        except Exception as exc:  # pragma: no cover
            logger.warning("Logo facture non dessiné : %s", exc)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(text_x, height - 16 * mm, library["name"])
    pdf.setFont("Helvetica", 9)
    line_y = height - 21 * mm
    for line in _address_lines(library):
        pdf.drawString(text_x, line_y, line)
        line_y -= 4 * mm

    # ── Titre + destinataire ──
    y = height - 48 * mm
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 20)
    pdf.drawString(MARGIN, y, _("Facture %(num)s") % {"num": invoice.number})

    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(INK_SOFT)
    pdf.drawRightString(
        width - MARGIN, y + 6 * mm,
        _("Émise le %(d)s") % {"d": _date(invoice.issue_date)},
    )
    pdf.drawRightString(
        width - MARGIN, y + 1 * mm,
        _("Échéance : %(d)s") % {"d": _date(invoice.due_date)},
    )

    y -= 14 * mm
    pdf.setFillColor(INK_SOFT)
    pdf.setFont("Helvetica", 8.5)
    pdf.drawString(MARGIN, y, _("DESTINATAIRE"))
    y -= 5 * mm
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(MARGIN, y, invoice.member.full_name)
    pdf.setFont("Helvetica", 10)
    for line in invoice.member.address_lines:
        y -= 4.6 * mm
        pdf.drawString(MARGIN, y, line)
    y -= 4.6 * mm
    pdf.setFillColor(INK_SOFT)
    pdf.setFont("Helvetica", 9)
    pdf.drawString(MARGIN, y, _("N° de carte : %(n)s") % {"n": invoice.member.card_number})

    # ── Tableau des lignes ──
    y -= 14 * mm
    table_top = y
    pdf.setFillColor(CREAM)
    pdf.rect(MARGIN, y - 7 * mm, width - 2 * MARGIN, 7 * mm, stroke=0, fill=1)
    pdf.setFillColor(INK_SOFT)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(MARGIN + 3 * mm, y - 5 * mm, _("Désignation"))
    pdf.drawRightString(width - MARGIN - 55 * mm, y - 5 * mm, _("Qté"))
    pdf.drawRightString(width - MARGIN - 30 * mm, y - 5 * mm, _("P.U."))
    pdf.drawRightString(width - MARGIN - 3 * mm, y - 5 * mm, _("Total"))
    y -= 7 * mm

    pdf.setFont("Helvetica", 10)
    for line in invoice.lines.all():
        y -= 7 * mm
        if y < 45 * mm:
            pdf.showPage()
            y = height - MARGIN
        pdf.setFillColor(INK)
        label = f"{line.get_kind_display()} — {line.label}"
        pdf.drawString(MARGIN + 3 * mm, y, _truncate(pdf, label, width - 2 * MARGIN - 65 * mm))
        pdf.drawRightString(width - MARGIN - 55 * mm, y, str(line.quantity))
        pdf.drawRightString(width - MARGIN - 30 * mm, y, format_amount(line.amount, False))
        pdf.drawRightString(width - MARGIN - 3 * mm, y, format_amount(line.line_total, False))
        pdf.setStrokeColor(colors.HexColor("#E6E0D8"))
        pdf.setLineWidth(0.4)
        pdf.line(MARGIN, y - 2.5 * mm, width - MARGIN, y - 2.5 * mm)

    pdf.setStrokeColor(colors.HexColor("#E6E0D8"))
    pdf.rect(MARGIN, y - 2.5 * mm, width - 2 * MARGIN, table_top - y + 2.5 * mm,
             stroke=1, fill=0)

    # ── Totaux ──
    y -= 12 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(INK)
    pdf.drawRightString(width - MARGIN - 30 * mm, y, _("Total"))
    pdf.drawRightString(width - MARGIN - 3 * mm, y, format_amount(invoice.total_amount))
    if invoice.amount_paid:
        y -= 6 * mm
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(INK_SOFT)
        pdf.drawRightString(width - MARGIN - 30 * mm, y, _("Déjà réglé"))
        pdf.drawRightString(width - MARGIN - 3 * mm, y, format_amount(invoice.amount_paid))
    y -= 7 * mm
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(BURGUNDY)
    if invoice.status == InvoiceStatus.PAID:
        pdf.drawRightString(width - MARGIN - 3 * mm, y, _("Réglée — merci."))
    elif invoice.status == InvoiceStatus.CANCELLED:
        pdf.drawRightString(width - MARGIN - 3 * mm, y, _("Facture annulée"))
    else:
        pdf.drawRightString(width - MARGIN - 30 * mm, y, _("Reste à payer"))
        pdf.drawRightString(width - MARGIN - 3 * mm, y, format_amount(invoice.balance))

    if invoice.note:
        y -= 12 * mm
        pdf.setFont("Helvetica-Oblique", 9)
        pdf.setFillColor(INK_SOFT)
        pdf.drawString(MARGIN, y, _truncate(pdf, invoice.note, width - 2 * MARGIN))

    # ── Pied ──
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(INK_SOFT)
    pdf.drawCentredString(
        width / 2, 14 * mm,
        _("%(lib)s — document généré par BibliOfelia") % {"lib": library["name"]},
    )
    pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _address_lines(library: dict) -> list[str]:
    lines = [
        line.strip()
        for line in (library["address"] or "").splitlines()
        if line.strip()
    ]
    if library["country"]:
        lines.append(library["country"])
    contact = " · ".join(p for p in (library["phone"], library["email"]) if p)
    if contact:
        lines.append(contact)
    return lines[:4]


def _truncate(pdf, text: str, max_width: float, font: str = "Helvetica",
              size: float = 10) -> str:
    """Coupe `text` pour tenir dans `max_width` — une désignation trop longue
    déborderait sur la colonne des montants."""
    if pdf.stringWidth(text, font, size) <= max_width:
        return text
    while text and pdf.stringWidth(text + "…", font, size) > max_width:
        text = text[:-1]
    return text + "…"


def _date(value) -> str:
    from django.utils.formats import date_format

    return date_format(value, "SHORT_DATE_FORMAT", use_l10n=True)
