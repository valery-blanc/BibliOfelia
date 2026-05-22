"""Génération PDF des étiquettes exemplaires et cartes membres.

SPEC §6.7 :
- Étiquettes exemplaires : 50×25 mm par défaut (thermique) ; fallback PDF =
  planche A4 de 24 étiquettes 70×36 mm (3 colonnes × 8 lignes).
- Cartes membres : 8 par A4 (2 col × 4 lignes), format ~105×74 mm.

L'intégration CUPS (pycups) reste limitée à l'image Docker Linux (cf.
`requirements.txt` ; le package est installé conditionnellement dans le
Dockerfile). En dev Windows et en l'absence de CUPS, on génère le PDF.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

from django.conf import settings
from django.utils.translation import gettext as _

from barcode import EAN13
from barcode.writer import ImageWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Helpers EAN → image
# ----------------------------------------------------------------------
def _barcode_image(ean13: str) -> ImageReader:
    """Rend un code-barres EAN13 en PNG (bytes) et l'enveloppe dans ImageReader."""
    buf = io.BytesIO()
    EAN13(ean13[:12], writer=ImageWriter()).write(buf, options={
        "module_height": 8.0,
        "module_width": 0.25,
        "font_size": 8,
        "text_distance": 2,
        "quiet_zone": 2,
        "write_text": False,
    })
    buf.seek(0)
    return ImageReader(buf)


def _truncate(text: str, max_chars: int) -> str:
    text = text or ""
    return text if len(text) <= max_chars else text[: max_chars - 1] + "…"


def _format_settings() -> dict:
    """Lit `label_format` (Setting) avec valeurs par défaut."""
    from apps.core.models import Setting

    data = Setting.get("label_format", {}) or {}
    return {
        "item_width_mm": data.get("item_width_mm", 70),
        "item_height_mm": data.get("item_height_mm", 36),
        "item_title_max_chars": data.get("item_title_max_chars", 30),
        "card_per_a4": data.get("card_per_a4", 8),
    }


# ----------------------------------------------------------------------
# Planches d'étiquettes exemplaires
# ----------------------------------------------------------------------
def render_item_labels_pdf(items: Sequence) -> bytes:
    """Génère un PDF A4 de planches d'étiquettes pour `items`.

    Layout : 3 colonnes × 8 lignes = 24 étiquettes par page, 70×36 mm
    (marges 0). En cas de personnalisation `label_format`, on recalcule
    cols/rows pour tenir dans A4.
    """
    fmt = _format_settings()
    label_w = fmt["item_width_mm"] * mm
    label_h = fmt["item_height_mm"] * mm
    cols = max(1, int(A4[0] // label_w))
    rows = max(1, int(A4[1] // label_h))
    per_page = cols * rows

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    library_name = _library_name()

    for idx, item in enumerate(items):
        slot = idx % per_page
        col = slot % cols
        row = slot // cols
        x = col * label_w
        y = A4[1] - (row + 1) * label_h
        _draw_item_label(
            pdf, x, y, label_w, label_h, item, library_name,
            title_max=fmt["item_title_max_chars"],
        )
        if slot == per_page - 1 and idx != len(items) - 1:
            pdf.showPage()

    pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _draw_item_label(pdf, x, y, w, h, item, library_name: str, title_max: int) -> None:
    pdf.setLineWidth(0.2)
    pdf.setStrokeColor(colors.lightgrey)
    pdf.rect(x + 1, y + 1, w - 2, h - 2)
    # Titre
    title = _truncate(item.record.title, title_max)
    pdf.setFont("Helvetica-Bold", 8)
    pdf.drawString(x + 3 * mm, y + h - 5 * mm, title)
    # Auteurs (1 ligne max)
    pdf.setFont("Helvetica", 6.5)
    authors = ", ".join(a.full_name for a in item.record.authors.all()[:2])
    if authors:
        pdf.drawString(x + 3 * mm, y + h - 8 * mm, _truncate(authors, 50))
    # Code-barres
    try:
        img = _barcode_image(item.ean13)
        bw = w - 6 * mm
        bh = h * 0.45
        pdf.drawImage(img, x + 3 * mm, y + 6 * mm, width=bw, height=bh,
                      preserveAspectRatio=True, anchor="sw")
    except Exception as exc:
        logger.warning("Item %s : barcode KO : %s", item.pk, exc)
    # Ligne basse : EAN13 + location + internal_id
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(x + 3 * mm, y + 3 * mm, item.ean13)
    loc = item.location.code if item.location_id else ""
    if loc:
        pdf.drawRightString(x + w - 3 * mm, y + 3 * mm, loc)
    pdf.setFont("Helvetica-Oblique", 5.5)
    pdf.drawString(x + 3 * mm, y + 1 * mm, item.internal_id)
    pdf.drawRightString(x + w - 3 * mm, y + 1 * mm, library_name[:20])


# ----------------------------------------------------------------------
# Cartes membres
# ----------------------------------------------------------------------
def render_member_cards_pdf(members: Sequence) -> bytes:
    """Génère un PDF A4 de cartes membres.

    Layout 8/A4 par défaut (2 col × 4 lignes), chaque cellule 105×74 mm.
    """
    fmt = _format_settings()
    per_page = int(fmt["card_per_a4"])
    # Choix simple : 2 colonnes ; rows = per_page / 2 (4, 5, 4, etc.)
    cols = 2 if per_page >= 2 else 1
    rows = max(1, per_page // cols)
    card_w = A4[0] / cols
    card_h = A4[1] / rows
    library_name = _library_name()

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    for idx, member in enumerate(members):
        slot = idx % (cols * rows)
        col = slot % cols
        row = slot // cols
        x = col * card_w
        y = A4[1] - (row + 1) * card_h
        _draw_member_card(pdf, x, y, card_w, card_h, member, library_name)
        if slot == cols * rows - 1 and idx != len(members) - 1:
            pdf.showPage()
    pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _draw_member_card(pdf, x, y, w, h, member, library_name: str) -> None:
    pdf.setLineWidth(0.5)
    pdf.setStrokeColor(colors.grey)
    pdf.rect(x + 2 * mm, y + 2 * mm, w - 4 * mm, h - 4 * mm)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(x + 8 * mm, y + h - 12 * mm, library_name)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(x + 8 * mm, y + h - 17 * mm, _("Carte de membre"))
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(x + 8 * mm, y + h - 27 * mm,
                   f"{member.last_name} {member.first_name}")
    pdf.setFont("Helvetica", 8)
    if member.category_id:
        pdf.drawString(x + 8 * mm, y + h - 32 * mm,
                       _("Catégorie : %(c)s") % {"c": member.category.name})
    if member.expiration_date:
        pdf.drawString(x + 8 * mm, y + h - 37 * mm,
                       _("Valide jusqu'au %(d)s") % {"d": member.expiration_date.isoformat()})
    if member.preferred_language:
        pdf.drawRightString(x + w - 8 * mm, y + h - 12 * mm,
                            member.preferred_language.upper())
    # Code-barres
    try:
        img = _barcode_image(member.card_number)
        pdf.drawImage(img, x + 8 * mm, y + 8 * mm,
                      width=w - 16 * mm, height=18 * mm,
                      preserveAspectRatio=True, anchor="sw")
    except Exception as exc:
        logger.warning("Member %s : barcode KO : %s", member.pk, exc)
    pdf.setFont("Helvetica", 8)
    pdf.drawString(x + 8 * mm, y + 5 * mm, member.card_number)


# ----------------------------------------------------------------------
# Envoi CUPS (Linux uniquement, échec silencieux ailleurs)
# ----------------------------------------------------------------------
@dataclass
class PrintResult:
    sent: bool
    job_id: int | None = None
    error: str = ""


def submit_to_cups(pdf_bytes: bytes, job_title: str = "BibliOfelia") -> PrintResult:
    """Envoie un PDF à l'imprimante par défaut via CUPS.

    `pycups` n'est pas installé en dev Windows : on retourne `sent=False`.
    Côté Pi (Docker Linux), si CUPS_HOST est vide, le serveur local est utilisé.
    """
    try:
        import cups  # type: ignore[import-not-found]
    except Exception:
        return PrintResult(sent=False, error="pycups non disponible (dev ?)")
    try:
        if settings.CUPS_HOST:
            conn = cups.Connection(host=settings.CUPS_HOST, port=settings.CUPS_PORT)
        else:
            conn = cups.Connection()
        printer = conn.getDefault()
        if not printer:
            return PrintResult(sent=False, error="Aucune imprimante par défaut")
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as fh:
            fh.write(pdf_bytes)
            tmp_path = fh.name
        job_id = conn.printFile(printer, tmp_path, job_title, {})
        return PrintResult(sent=True, job_id=job_id)
    except Exception as exc:
        return PrintResult(sent=False, error=str(exc))


def _library_name() -> str:
    from apps.core.models import Setting

    return Setting.get("library_name", "BibliOfelia") or "BibliOfelia"
