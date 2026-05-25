"""Génération PDF des étiquettes exemplaires et cartes membres.

SPEC §6.7 :
- Étiquettes exemplaires : 80×40 mm par défaut (planche A4 = 3×7 = 21 par page)
  avec titre wrap 2 lignes, logo Ofelia, code-barres centré. Paramètres dans
  Setting `item_label_format` (FEAT-039).
- Cartes membres : 8 par A4 (2×4), fond crème rgb(248,238,229), photo en
  haut-gauche, logo OFELIA en filigrane centré, bloc texte à droite. Paramètres
  dans Setting `card_format` (FEAT-038).

L'intégration CUPS (pycups) reste limitée à l'image Docker Linux (cf.
`requirements.txt` ; le package est installé conditionnellement dans le
Dockerfile). En dev Windows et en l'absence de CUPS, on génère le PDF.
"""
from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Sequence

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


CARD_BG_RGB = (248 / 255, 238 / 255, 229 / 255)


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


def _wrap_title(text: str, max_chars: int, max_lines: int) -> list[str]:
    """Découpe un titre en `max_lines` lignes en respectant les mots.

    `max_chars` est le total cumulé. Chaque ligne reçoit au plus
    `max_chars // max_lines` caractères ; les mots ne sont coupés que si
    nécessaire. Dernière ligne tronquée avec '…' si débordement.
    """
    text = (text or "").strip()
    if max_lines <= 0:
        return []
    per_line = max(1, max_chars // max_lines)
    words = text.split()
    lines: list[str] = []
    current = ""
    for w in words:
        candidate = (current + " " + w).strip() if current else w
        if len(candidate) <= per_line:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = w
        else:
            lines.append(w[:per_line])
            current = w[per_line:]
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    # Tronquer la dernière ligne si on n'a pas fini
    consumed = sum(len(l) for l in lines) + max(0, len(lines) - 1)
    if consumed < len(text.replace("  ", " ")):
        last = lines[-1] if lines else ""
        if len(last) > per_line - 1:
            last = last[: per_line - 1]
        lines[-1] = last + "…" if lines else "…"
    return lines


def _card_settings() -> dict:
    from apps.core.models import Setting

    data = Setting.get("card_format", {}) or {}
    # Migration douce : ancien `label_format.card_per_a4`
    if "per_a4" not in data:
        legacy = Setting.get("label_format", {}) or {}
        if "card_per_a4" in legacy:
            data["per_a4"] = legacy["card_per_a4"]
    return {
        "per_a4": int(data.get("per_a4", 8)),
        "show_logo": bool(data.get("show_logo", True)),
        "show_photo": bool(data.get("show_photo", True)),
    }


def _item_label_settings() -> dict:
    from apps.core.models import Setting

    data = Setting.get("item_label_format", {}) or {}
    # Migration douce : ancien `label_format.item_*`
    if "width_mm" not in data:
        legacy = Setting.get("label_format", {}) or {}
        if "item_width_mm" in legacy:
            data["width_mm"] = legacy["item_width_mm"]
        if "item_height_mm" in legacy:
            data["height_mm"] = legacy["item_height_mm"]
        if "item_title_max_chars" in legacy:
            data["title_max_chars"] = legacy["item_title_max_chars"]
    return {
        "width_mm": int(data.get("width_mm", 70)),
        "height_mm": int(data.get("height_mm", 42)),
        "title_max_chars": int(data.get("title_max_chars", 50)),
        "title_lines": int(data.get("title_lines", 2)),
        "author_lines": int(data.get("author_lines", 2)),
        "show_logo": bool(data.get("show_logo", True)),
    }


def _static_logo(name: str) -> ImageReader | None:
    """Renvoie un ImageReader pour `static/img/<name>` ou None si absent."""
    try:
        path = settings.BASE_DIR / "static" / "img" / name
        if not path.exists():
            return None
        return ImageReader(str(path))
    except Exception as exc:
        logger.warning("Logo statique %s : %s", name, exc)
        return None


# ----------------------------------------------------------------------
# Planches d'étiquettes exemplaires
# ----------------------------------------------------------------------
def render_item_labels_pdf(items: Sequence) -> bytes:
    """Génère un PDF A4 de planches d'étiquettes pour `items`.

    Layout par défaut : 80×40 mm → 3 colonnes × 7 lignes = 21 étiquettes par
    page. En cas de personnalisation, on recalcule cols/rows pour tenir dans A4.
    """
    fmt = _item_label_settings()
    label_w = fmt["width_mm"] * mm
    label_h = fmt["height_mm"] * mm
    cols = max(1, int(A4[0] // label_w))
    rows = max(1, int(A4[1] // label_h))
    per_page = cols * rows

    logo = _static_logo("ofelia-logo.png") if fmt["show_logo"] else None
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
            title_max=fmt["title_max_chars"],
            title_lines=fmt["title_lines"],
            author_lines=fmt["author_lines"],
            logo=logo,
        )
        if slot == per_page - 1 and idx != len(items) - 1:
            pdf.showPage()

    pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _draw_item_label(pdf, x, y, w, h, item, library_name: str,
                     title_max: int, title_lines: int, author_lines: int,
                     logo: ImageReader | None) -> None:
    pdf.setLineWidth(0.2)
    pdf.setStrokeColor(colors.lightgrey)
    pdf.setFillColor(colors.black)
    pdf.rect(x + 1, y + 1, w - 2, h - 2)

    # Logo Ofelia haut-gauche
    logo_w = 0
    if logo is not None:
        try:
            logo_h = 6 * mm
            logo_w = 14 * mm
            pdf.drawImage(logo, x + 2 * mm, y + h - logo_h - 2 * mm,
                          width=logo_w, height=logo_h,
                          preserveAspectRatio=True, anchor="nw", mask="auto")
            logo_w += 2 * mm  # marge après logo
        except Exception as exc:
            logger.warning("Item %s : logo KO : %s", item.pk, exc)
            logo_w = 0

    # Titre wrap 2 lignes
    title_lines_text = _wrap_title(item.record.title, title_max, title_lines)
    pdf.setFont("Helvetica-Bold", 8.5)
    title_x = x + 3 * mm + logo_w
    line_y = y + h - 4 * mm
    for line in title_lines_text:
        pdf.drawString(title_x, line_y, line)
        line_y -= 3.2 * mm

    # Auteurs sous le titre (wrap N lignes par mots)
    pdf.setFont("Helvetica", 7)
    authors = ", ".join(a.full_name for a in item.record.authors.all()[:4])
    if authors:
        author_y = line_y - 0.5 * mm
        for line in _wrap_title(authors, max_chars=author_lines * 35, max_lines=author_lines):
            pdf.drawString(title_x, author_y, line)
            author_y -= 2.8 * mm

    # Code-barres centré, ~45% hauteur cellule
    try:
        img = _barcode_image(item.ean13)
        bw = w - 8 * mm
        bh = h * 0.40
        pdf.drawImage(img, x + 4 * mm, y + 7 * mm, width=bw, height=bh,
                      preserveAspectRatio=True, anchor="sw")
    except Exception as exc:
        logger.warning("Item %s : barcode KO : %s", item.pk, exc)

    # Bas : internal_id (gauche), code Ofelia (centre), location (droite)
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(x + 3 * mm, y + 3 * mm, item.internal_id)
    pdf.drawCentredString(x + w / 2, y + 3 * mm, item.ean13)
    loc = item.location.code if item.location_id else ""
    if loc:
        pdf.drawRightString(x + w - 3 * mm, y + 3 * mm, loc)
    pdf.setFont("Helvetica-Oblique", 5.5)
    pdf.drawRightString(x + w - 3 * mm, y + 1 * mm, library_name[:24])


# ----------------------------------------------------------------------
# Cartes membres
# ----------------------------------------------------------------------
def render_member_cards_pdf(members: Sequence) -> bytes:
    """Génère un PDF A4 de cartes membres.

    Layout 8/A4 par défaut (2 col × 4 lignes), chaque cellule 105×74 mm.
    """
    fmt = _card_settings()
    per_page = int(fmt["per_a4"])
    cols = 2 if per_page >= 2 else 1
    rows = max(1, per_page // cols)
    card_w = A4[0] / cols
    card_h = A4[1] / rows
    library_name = _library_name()

    logo = _static_logo("ofelia-grandes-lettres.png") if fmt["show_logo"] else None

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=A4)
    for idx, member in enumerate(members):
        slot = idx % (cols * rows)
        col = slot % cols
        row = slot // cols
        x = col * card_w
        y = A4[1] - (row + 1) * card_h
        _draw_member_card(pdf, x, y, card_w, card_h, member, library_name,
                          logo=logo, show_photo=fmt["show_photo"])
        if slot == cols * rows - 1 and idx != len(members) - 1:
            pdf.showPage()
    pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _draw_member_card(pdf, x, y, w, h, member, library_name: str,
                      logo: ImageReader | None, show_photo: bool) -> None:
    # Fond crème
    pdf.setFillColorRGB(*CARD_BG_RGB)
    pdf.setStrokeColor(colors.grey)
    pdf.setLineWidth(0.5)
    pdf.rect(x + 2 * mm, y + 2 * mm, w - 4 * mm, h - 4 * mm, fill=1, stroke=1)
    pdf.setFillColor(colors.black)

    # Logo OFELIA centré (en filigrane / léger)
    if logo is not None:
        try:
            margin = 4 * mm
            inner_w = w - 2 * margin
            inner_h = h - 2 * margin
            target_w = inner_w * 0.55
            target_h = inner_h * 0.55
            cx = x + w / 2 - target_w / 2
            cy = y + h / 2 - target_h / 2
            pdf.saveState()
            try:
                pdf.setFillAlpha(0.18)
                pdf.setStrokeAlpha(0.18)
            except Exception:
                pass
            pdf.drawImage(logo, cx, cy, width=target_w, height=target_h,
                          preserveAspectRatio=True, anchor="c", mask="auto")
            pdf.restoreState()
        except Exception as exc:
            logger.warning("Member %s : logo KO : %s", member.pk, exc)

    # Photo en haut à gauche
    photo_w = 0
    if show_photo and getattr(member, "photo", None):
        try:
            photo_path = member.photo.path
            photo_w = 22 * mm
            photo_h = 22 * mm
            pdf.drawImage(ImageReader(photo_path), x + 5 * mm, y + h - photo_h - 5 * mm,
                          width=photo_w, height=photo_h,
                          preserveAspectRatio=True, anchor="nw", mask="auto")
        except Exception as exc:
            logger.warning("Member %s : photo KO : %s", member.pk, exc)
            photo_w = 0

    # Bloc texte côté droit : nom, catégorie, validité
    right_x = x + w * 0.45
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(right_x, y + h - 10 * mm, library_name[:28])
    pdf.setFont("Helvetica", 8)
    pdf.drawString(right_x, y + h - 15 * mm, _("Carte de membre"))
    pdf.setFont("Helvetica-Bold", 13)
    full_name = f"{member.last_name} {member.first_name}".strip()
    pdf.drawString(right_x, y + h - 24 * mm, _truncate(full_name, 28))
    pdf.setFont("Helvetica", 8)
    if member.category_id:
        pdf.drawString(right_x, y + h - 29 * mm,
                       _("Catégorie : %(c)s") % {"c": member.category.name})
    if member.expiration_date:
        pdf.drawString(right_x, y + h - 34 * mm,
                       _("Valide jusqu'au %(d)s") % {"d": member.expiration_date.isoformat()})

    # Code-barres bas-droite
    try:
        img = _barcode_image(member.card_number)
        bc_w = w * 0.50
        bc_h = 16 * mm
        bc_x = x + w - bc_w - 5 * mm
        bc_y = y + 8 * mm
        pdf.drawImage(img, bc_x, bc_y, width=bc_w, height=bc_h,
                      preserveAspectRatio=True, anchor="sw")
        pdf.setFont("Helvetica", 8)
        pdf.drawString(bc_x, y + 5 * mm, member.card_number)
    except Exception as exc:
        logger.warning("Member %s : barcode KO : %s", member.pk, exc)

    # Langue en bas-gauche
    if member.preferred_language:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(x + 5 * mm, y + 5 * mm,
                       member.preferred_language.upper())


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
