"""Génération PDF des étiquettes exemplaires et cartes membres.

SPEC §6.7 :
- Étiquettes exemplaires : 80×40 mm par défaut (planche A4 = 3×7 = 21 par page)
  avec titre wrap 2 lignes, logo Ofelia, code-barres centré. Paramètres dans
  Setting `item_label_format` (FEAT-039).
- Cartes membres : 8 par A4 (2×4), fond crème rgb(248,238,229), photo en
  haut-gauche, logo OFELIA en filigrane centré, bloc texte à droite. Paramètres
  dans Setting `card_format` (FEAT-038).
- Ruban continu Brother QL-810W 62 mm : une étiquette (62×35 mm, entièrement
  monochrome) ou une carte membre (62×89 mm, dessin couché au format carte
  bancaire) par page. Paramètres dans Setting `roll_printer_format` (FEAT-062).

L'impression passe toujours par un PDF servi au navigateur : l'étiqueteuse est
branchée sur le poste client, pas sur le serveur (cf. FEAT-074).
"""
from __future__ import annotations

import io
import logging
from typing import Sequence

from django.conf import settings
from django.utils.translation import gettext as _

from barcode import EAN13
from barcode.writer import ImageWriter
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

logger = logging.getLogger(__name__)


CARD_BG_RGB = (248 / 255, 238 / 255, 229 / 255)
FAMILY_LINE_RATIO = 1.45  # interligne de la colonne « Famille » (FEAT-072)


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


def family_column_lines(names: Sequence[str], available_h: float,
                        name_pt: float) -> tuple[list[str], bool]:
    """Prénoms qui tiennent dans la hauteur disponible, et s'il y a eu coupe.

    Extraite du dessin pour être vérifiable directement : le contenu d'un flux
    PDF ReportLab ne se relit pas de façon fiable.
    """
    line_h = name_pt * FAMILY_LINE_RATIO
    if line_h <= 0 or available_h <= 0:
        return [], bool(names)
    room = int(available_h // line_h)
    if room >= len(names):
        return list(names), False
    # Une ligne est réservée à l'ellipse, qui dit qu'il en reste.
    return list(names[: max(0, room - 1)]), True


def _draw_family_column(pdf, left: float, top: float, bottom: float, width: float,
                        names: Sequence[str], title_pt: float, name_pt: float) -> None:
    """FEAT-072 : colonne « Famille » à droite de la carte, un prénom par ligne.

    Choix Val (2026-08-20) : une colonne plutôt qu'une ligne sous le nom — une
    famille nombreuse reste lisible. Quand la place manque, on tronque par « … »
    plutôt que d'écrire par-dessus le code-barres.
    """
    if not names:
        return
    pdf.setFont("Helvetica-Bold", title_pt)
    pdf.drawString(left, top, _fit_to_width(str(_("Famille")), "Helvetica-Bold",
                                            title_pt, width))
    line_h = name_pt * FAMILY_LINE_RATIO
    shown, truncated = family_column_lines(names, top - line_h - bottom, name_pt)
    y = top - line_h
    pdf.setFont("Helvetica", name_pt)
    for name in shown:
        pdf.drawString(left, y, _fit_to_width(name, "Helvetica", name_pt, width))
        y -= line_h
    if truncated:
        pdf.drawString(left, y, "…")


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

    # FEAT-072 : colonne « Famille » à droite ; le bloc texte se rétrécit d'autant.
    family = list(getattr(member, "family_first_names", []) or [])
    fam_w = w * 0.22 if family else 0
    fam_x = x + w - 4 * mm - fam_w
    _draw_family_column(pdf, fam_x, y + h - 10 * mm, y + 26 * mm, fam_w,
                        family, title_pt=8, name_pt=7.5)

    # Bloc texte : nom, catégorie, validité. Sans famille, il reste où il était
    # (rendu validé au Sprint 27) ; avec, il récupère la place laissée libre à
    # gauche — sinon le nom serait tronqué pour loger les prénoms.
    right_x = x + w * 0.45
    if family:
        right_x = x + 5 * mm + (photo_w + 4 * mm if photo_w else 0)
    text_w = (fam_x - 3 * mm if family else x + w - 5 * mm) - right_x
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(right_x, y + h - 10 * mm,
                   _fit_to_width(library_name, "Helvetica-Bold", 12, text_w))
    pdf.setFont("Helvetica", 8)
    pdf.drawString(right_x, y + h - 15 * mm, _("Carte de membre"))
    pdf.setFont("Helvetica-Bold", 13)
    full_name = f"{member.last_name} {member.first_name}".strip()
    pdf.drawString(right_x, y + h - 24 * mm,
                   _fit_to_width(full_name, "Helvetica-Bold", 13, text_w))
    pdf.setFont("Helvetica", 8)
    if member.category_id:
        pdf.drawString(right_x, y + h - 29 * mm, _fit_to_width(
            str(_("Catégorie : %(c)s") % {"c": member.category.name}),
            "Helvetica", 8, text_w))
    if member.expiration_date:
        pdf.drawString(right_x, y + h - 34 * mm, _fit_to_width(
            str(_("Valide jusqu'au %(d)s") % {"d": member.expiration_date.isoformat()}),
            "Helvetica", 8, text_w))

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


def _library_name() -> str:
    from apps.core.models import Setting

    return Setting.get("library_name", "BibliOfelia") or "BibliOfelia"


# ----------------------------------------------------------------------
# FEAT-062 — Ruban continu Brother QL-810W (62 mm, noir/rouge)
# ----------------------------------------------------------------------
# L'imprimante est branchée en USB sur un poste client : ni la Box ni les
# instances hébergées ne peuvent lui parler directement. On produit donc un PDF
# à la géométrie exacte du ruban (une étiquette par page, marges nulles) que le
# navigateur du poste envoie au pilote Brother.

ROLL_INSET_MM = 2.0  # zone imprimable réelle ≈ 58.9 mm sur un ruban de 62 mm
ROLL_FEED_INSET_MM = 3.0  # marge d'avance papier en tête et en pied de bande
# Les cartes se contentent d'une marge d'avance réduite : le format continu
# « 62mm » du pilote Brother mesure 62 × 89,9 mm, et il faut y loger 85,6 mm de
# carte pour garder le format carte bancaire exact (85,6 + 2 × 1,7 = 89).
ROLL_CARD_FEED_INSET_MM = 1.5
# Étiquettes : une seule police, une seule taille pour tous les textes, les
# auteurs s'en distinguant par l'italique (demande Val 2026-08-18).
ROLL_FONT = "Helvetica-Bold"
ROLL_FONT_ITALIC = "Helvetica-BoldOblique"
ROLL_TEXT_PT = 7.5
ROLL_LINE_MM = 3.1
CARD_W_MM = 85.6  # format carte bancaire ISO 7810 ID-1
CARD_H_MM = 54.0
RED = colors.Color(1, 0, 0)  # rouge pur : seul déclencheur de la 2e couleur DK-22251


def _roll_settings() -> dict:
    from apps.core.models import Setting

    data = Setting.get("roll_printer_format", {}) or {}
    return {
        "enabled": bool(data.get("enabled", True)),
        "tape_width_mm": int(data.get("tape_width_mm", 62)),
        "label_length_mm": int(data.get("label_length_mm", 35)),
        "card_length_mm": int(data.get("card_length_mm", 89)),
        "two_color": bool(data.get("two_color", True)),
        "show_logo": bool(data.get("show_logo", True)),
    }


def _accent(two_color: bool):
    """Couleur d'accent des cartes membres : rouge pur si ruban bicolore.

    Ne s'applique plus aux étiquettes : elles sont entièrement monochromes.
    """
    return RED if two_color else colors.black


def _text_width(text: str, font: str, size: float) -> float:
    return pdfmetrics.stringWidth(text or "", font, size)


def _fit_to_width(text: str, font: str, size: float, max_width: float) -> str:
    """Tronque `text` avec '…' pour qu'il tienne dans `max_width` points."""
    text = (text or "").strip()
    if not text or _text_width(text, font, size) <= max_width:
        return text
    while text and _text_width(text + "…", font, size) > max_width:
        text = text[:-1]
    return (text + "…") if text else ""


def _wrap_to_width(text: str, font: str, size: float,
                   max_width: float, max_lines: int) -> list[str]:
    """Découpe `text` en lignes qui remplissent réellement `max_width`.

    Contrairement à `_wrap_title` (budget en nombre de caractères), on mesure
    la chaîne : sur une étiquette de 62 mm, un titre étroit occupe donc toute
    la largeur au lieu de casser au bout d'un quota arbitraire.
    """
    words = (text or "").split()
    if not words or max_lines <= 0:
        return []
    lines: list[str] = []
    current = ""
    truncated = False
    for index, word in enumerate(words):
        candidate = f"{current} {word}".strip()
        if not current or _text_width(candidate, font, size) <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
        if len(lines) == max_lines:
            truncated = True
            current = ""
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    elif current:
        truncated = True
    if truncated and lines:
        lines[-1] = _fit_to_width(lines[-1] + " …", font, size, max_width)
    return [_fit_to_width(line, font, size, max_width) for line in lines]


def _static_logo_grayscale(name: str) -> ImageReader | None:
    """`static/img/<name>` converti en niveaux de gris, transparence conservée.

    L'étiqueteuse est thermique : elle ne connaît que le noir (et le rouge du
    ruban bicolore). Un logo couleur laissé tel quel est tramé au hasard par
    le pilote — on fait la conversion nous-mêmes.
    """
    try:
        path = settings.BASE_DIR / "static" / "img" / name
        if not path.exists():
            return None
        source = Image.open(path).convert("RGBA")
        grey = source.convert("L").convert("RGBA")
        grey.putalpha(source.getchannel("A"))
        buf = io.BytesIO()
        grey.save(buf, format="PNG")
        buf.seek(0)
        return ImageReader(buf)
    except Exception as exc:
        logger.warning("Logo %s en niveaux de gris : %s", name, exc)
        return None


def render_item_labels_roll_pdf(items: Sequence) -> bytes:
    """Génère un PDF « ruban » : **une étiquette par page**, 62 × 35 mm.

    Une page = une étiquette = une coupe. La QL est réglée pour couper tous les
    35 mm : grouper plusieurs étiquettes sur une page plus longue (tentative du
    2026-08-18 pour forcer l'orientation portrait du dialogue) produisait une
    page que l'imprimante ne pouvait pas honorer.
    """
    fmt = _roll_settings()
    w = fmt["tape_width_mm"] * mm
    h = fmt["label_length_mm"] * mm
    logo = _static_logo_grayscale("ofelia-logo.png") if fmt["show_logo"] else None
    library_name = _library_name()

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=(w, h))
    for item in items:
        _draw_roll_item_label(pdf, w, h, item, library_name, logo)
        pdf.showPage()
    if not items:
        pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _draw_roll_item_label(pdf, w, h, item, library_name: str,
                          logo: ImageReader | None) -> None:
    """Étiquette entièrement monochrome, tous les textes à la même taille.

    De haut en bas : logo en niveaux de gris + nom de la bibliothèque, titre
    sur 2 lignes pleine largeur, auteurs en italique, code-barres, puis code
    Ofelia et emplacement. Pas d'identifiant interne (demande Val).
    """
    left = ROLL_INSET_MM * mm
    right = w - ROLL_INSET_MM * mm
    bottom = ROLL_FEED_INSET_MM * mm
    top = h - ROLL_FEED_INSET_MM * mm
    inner_w = right - left

    pdf.setFillColor(colors.black)
    pdf.setFont(ROLL_FONT, ROLL_TEXT_PT)

    # Bandeau : logo à gauche, nom de la bibliothèque à droite
    head_y = top - 3.2 * mm
    reserved = 0.0
    if logo is not None:
        try:
            pdf.drawImage(logo, left, head_y - 0.7 * mm, width=11 * mm, height=3.9 * mm,
                          preserveAspectRatio=True, anchor="sw", mask="auto")
            reserved = 13 * mm
        except Exception as exc:
            logger.warning("Item %s : logo ruban KO : %s", item.pk, exc)
    pdf.drawRightString(right, head_y,
                        _fit_to_width(library_name, ROLL_FONT, ROLL_TEXT_PT,
                                      inner_w - reserved))

    # Pied : code Ofelia à gauche, emplacement à droite
    foot_y = bottom + 0.6 * mm
    pdf.drawString(left, foot_y, item.ean13)
    loc = item.location.code if item.location_id else ""
    if loc:
        pdf.drawRightString(right, foot_y, loc)

    # Code-barres, ancré au-dessus du pied
    bar_y = bottom + 4.4 * mm
    bar_h = max(6 * mm, (top - bottom) * 0.32)
    bar_w = min(inner_w, 50 * mm)

    # Titre pleine largeur puis auteurs en italique : le bloc est centré
    # verticalement entre le bandeau et le code-barres, pour qu'un titre d'une
    # seule ligne ne laisse pas un trou au milieu de l'étiquette.
    title_lines = _wrap_to_width(item.record.title, ROLL_FONT, ROLL_TEXT_PT, inner_w, 2)
    authors = _fit_to_width(
        ", ".join(a.full_name for a in item.record.authors.all()[:3]),
        ROLL_FONT_ITALIC, ROLL_TEXT_PT, inner_w,
    )
    rows = len(title_lines) + (1 if authors else 0)
    if rows:
        region_top = top - 5.6 * mm
        region_bottom = bar_y + bar_h + 0.8 * mm
        block_h = rows * ROLL_LINE_MM * mm
        slack = max(0.0, (region_top - region_bottom) - block_h)
        line_y = region_top - slack / 2 - 2.4 * mm
        for line in title_lines:
            pdf.drawString(left, line_y, line)
            line_y -= ROLL_LINE_MM * mm
        if authors:
            pdf.setFont(ROLL_FONT_ITALIC, ROLL_TEXT_PT)
            pdf.drawString(left, line_y, authors)
            pdf.setFont(ROLL_FONT, ROLL_TEXT_PT)

    try:
        pdf.drawImage(_barcode_image(item.ean13), (w - bar_w) / 2, bar_y,
                      width=bar_w, height=bar_h,
                      preserveAspectRatio=False, anchor="sw")
    except Exception as exc:
        logger.warning("Item %s : barcode ruban KO : %s", item.pk, exc)


def render_member_cards_roll_pdf(members: Sequence) -> bytes:
    """Génère un PDF « ruban » : une carte membre par page, 62 × 89 mm par défaut.

    Le dessin est tourné à 90° dans la page pour sortir une carte au format
    carte bancaire (85,6 × 54 mm) en travers du ruban.

    89 mm n'est pas un choix esthétique : le format continu « 62mm » du pilote
    Brother se déclare à Windows en 62 × 89,9 mm. En restant juste en dessous,
    la page tombe sur le format natif — plus de longueur à saisir dans le
    dialogue système — et 89 > 62 donne une page portrait.
    """
    fmt = _roll_settings()
    card_fmt = _card_settings()
    w = fmt["tape_width_mm"] * mm
    h = fmt["card_length_mm"] * mm
    card_w = CARD_W_MM * mm
    card_h = CARD_H_MM * mm
    # Réduction si le ruban configuré est plus étroit / plus court que la carte
    scale = min(
        1.0,
        (w - 2 * ROLL_INSET_MM * mm) / card_h,
        (h - 2 * ROLL_CARD_FEED_INSET_MM * mm) / card_w,
    )
    draw_w = card_w * scale  # dans le sens de défilement du ruban
    draw_h = card_h * scale  # en travers du ruban

    logo = _static_logo("ofelia-grandes-lettres.png") if card_fmt["show_logo"] else None
    library_name = _library_name()

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=(w, h))
    for member in members:
        pdf.saveState()
        pdf.translate(w / 2 + draw_h / 2, (h - draw_w) / 2)
        pdf.rotate(90)
        pdf.scale(scale, scale)
        _draw_roll_member_card(pdf, card_w, card_h, member, library_name,
                               logo=logo, show_photo=card_fmt["show_photo"],
                               two_color=fmt["two_color"])
        pdf.restoreState()
        pdf.showPage()
    if not members:
        pdf.showPage()
    pdf.save()
    return buf.getvalue()


def _draw_roll_member_card(pdf, w, h, member, library_name: str,
                           logo: ImageReader | None, show_photo: bool,
                           two_color: bool) -> None:
    """Carte 85,6 × 54 mm dessinée à l'origine du repère courant."""
    accent = _accent(two_color)

    pdf.setFillColorRGB(*CARD_BG_RGB)
    pdf.setStrokeColor(colors.grey)
    pdf.setLineWidth(0.4)
    pdf.rect(0, 0, w, h, fill=1, stroke=1)
    pdf.setFillColor(colors.black)

    # Logo OFELIA en filigrane centré
    if logo is not None:
        try:
            target_w = w * 0.55
            target_h = h * 0.55
            pdf.saveState()
            try:
                pdf.setFillAlpha(0.18)
                pdf.setStrokeAlpha(0.18)
            except Exception:
                pass
            pdf.drawImage(logo, (w - target_w) / 2, (h - target_h) / 2,
                          width=target_w, height=target_h,
                          preserveAspectRatio=True, anchor="c", mask="auto")
            pdf.restoreState()
        except Exception as exc:
            logger.warning("Member %s : logo ruban KO : %s", member.pk, exc)

    # Photo en haut-gauche
    if show_photo and getattr(member, "photo", None):
        try:
            pdf.drawImage(ImageReader(member.photo.path), 4 * mm, h - 24 * mm,
                          width=20 * mm, height=20 * mm,
                          preserveAspectRatio=True, anchor="nw", mask="auto")
        except Exception as exc:
            logger.warning("Member %s : photo ruban KO : %s", member.pk, exc)

    # FEAT-072 : colonne « Famille » à droite, avant le bloc texte.
    family = list(getattr(member, "family_first_names", []) or [])
    fam_w = 21 * mm if family else 0
    fam_x = w - 3.5 * mm - fam_w
    _draw_family_column(pdf, fam_x, h - 8 * mm, 21 * mm, fam_w,
                        family, title_pt=6.5, name_pt=6.5)

    # Bloc texte à droite de la photo
    tx = 28 * mm
    text_w = (fam_x - 2 * mm if family else w - 3.5 * mm) - tx
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 9.5)
    pdf.drawString(tx, h - 8 * mm,
                   _fit_to_width(library_name, "Helvetica-Bold", 9.5, text_w))
    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(accent)
    pdf.drawString(tx, h - 12 * mm, _("Carte de membre"))
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica-Bold", 11)
    full_name = f"{member.last_name} {member.first_name}".strip()
    pdf.drawString(tx, h - 18.5 * mm,
                   _fit_to_width(full_name, "Helvetica-Bold", 11, text_w))
    pdf.setFont("Helvetica", 7)
    if member.category_id:
        pdf.drawString(tx, h - 23.5 * mm, _fit_to_width(
            str(_("Catégorie : %(c)s") % {"c": member.category.name}),
            "Helvetica", 7, text_w))
    if member.expiration_date:
        pdf.drawString(tx, h - 28 * mm, _fit_to_width(
            str(_("Valide jusqu'au %(d)s") % {"d": member.expiration_date.isoformat()}),
            "Helvetica", 7, text_w))

    # Code-barres bas-droite — toujours noir
    try:
        pdf.drawImage(_barcode_image(member.card_number), tx, 7 * mm,
                      width=52 * mm, height=12 * mm,
                      preserveAspectRatio=False, anchor="sw")
    except Exception as exc:
        logger.warning("Member %s : barcode ruban KO : %s", member.pk, exc)
    pdf.setFont("Helvetica", 7)
    pdf.drawString(tx, 4 * mm, member.card_number)

    # Langue préférée en bas-gauche
    if member.preferred_language:
        pdf.setFont("Helvetica-Bold", 8)
        pdf.drawString(4 * mm, 4 * mm, member.preferred_language.upper())


# ── FEAT-068 : étiquettes de tranche (cote de catégorie) ───────────────────
# Même ruban et même géométrie que les étiquettes de livres, mais un seul
# contenu : l'abréviation de la catégorie, en très gros, pour se lire à un
# mètre du rayon sans sortir le livre.

SPINE_MIN_PT = 10.0
# Plafond large à dessein : sur une étiquette de 62 × 35 mm, une cote courte
# comme « PER » doit remplir la place disponible, c'est tout l'intérêt d'une
# cote de rayon. C'est la largeur (ou la hauteur) utile qui arrête la
# recherche, pas ce plafond.
SPINE_MAX_PT = 96.0
SPINE_LINE_RATIO = 1.12  # interligne, en multiples de la taille de police
SPINE_CAP_RATIO = 0.72   # hauteur des capitales, pour le centrage vertical


def spine_label_text(item) -> str:
    """Cote à imprimer pour cet exemplaire (vide s'il n'y en a pas)."""
    category = getattr(item.record, "category", None)
    if category is None:
        return ""
    return (category.abbreviation or "").strip()


def _wrap_words(words: list[str], font: str, size: float, max_width: float) -> list[str]:
    """Découpe en lignes sans jamais couper un mot ni tronquer.

    Sert à chercher la taille de police : on veut la largeur réelle des lignes,
    y compris quand un mot seul dépasse (cas traité par l'appelant).
    """
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if not current or _text_width(candidate, font, size) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render_spine_labels_roll_pdf(items: Sequence) -> bytes:
    """PDF « ruban » des étiquettes de tranche : une page par exemplaire.

    Les exemplaires dont la notice n'a pas de catégorie — ou dont la catégorie
    n'a pas d'abréviation — n'ont rien à imprimer et sont ignorés ici ; la vue
    prévient l'utilisateur avant d'en arriver là.
    """
    fmt = _roll_settings()
    w = fmt["tape_width_mm"] * mm
    h = fmt["label_length_mm"] * mm

    buf = io.BytesIO()
    pdf = canvas.Canvas(buf, pagesize=(w, h))
    drawn = 0
    for item in items:
        text = spine_label_text(item)
        if not text:
            continue
        _draw_roll_spine_label(pdf, w, h, text)
        pdf.showPage()
        drawn += 1
    if not drawn:
        pdf.showPage()
    pdf.save()
    return buf.getvalue()


def spine_layout(text: str, inner_w: float, inner_h: float) -> tuple[float, list[str]]:
    """Taille de police et lignes retenues pour une cote, en points.

    On part du plafond et on descend jusqu'à ce que la cote tienne en largeur
    **et** en hauteur : une cote courte occupe donc toute l'étiquette, une cote
    longue passe à la ligne et rétrécit. Sous `SPINE_MIN_PT` on arrête : mieux
    vaut rogner que produire une cote illisible.
    """
    words = text.split()
    size = SPINE_MAX_PT
    lines = _wrap_words(words, ROLL_FONT, size, inner_w)
    while size > SPINE_MIN_PT:
        lines = _wrap_words(words, ROLL_FONT, size, inner_w)
        widest = max(_text_width(line, ROLL_FONT, size) for line in lines)
        block_h = (len(lines) - 1) * size * SPINE_LINE_RATIO + size * SPINE_CAP_RATIO
        if widest <= inner_w and block_h <= inner_h:
            break
        size -= 0.5
    return size, [_fit_to_width(line, ROLL_FONT, size, inner_w) for line in lines]


def _draw_roll_spine_label(pdf, w, h, text: str) -> None:
    """Cote centrée, à la plus grande taille qui tienne sur l'étiquette."""
    left = ROLL_INSET_MM * mm
    right = w - ROLL_INSET_MM * mm
    bottom = ROLL_FEED_INSET_MM * mm
    top = h - ROLL_FEED_INSET_MM * mm

    size, lines = spine_layout(text, right - left, top - bottom)
    line_h = size * SPINE_LINE_RATIO
    cap = size * SPINE_CAP_RATIO
    block_h = (len(lines) - 1) * line_h + cap
    baseline = (bottom + top + block_h) / 2 - cap

    pdf.setFillColor(colors.black)
    pdf.setFont(ROLL_FONT, size)
    for line in lines:
        pdf.drawCentredString(w / 2, baseline, line)
        baseline -= line_h
