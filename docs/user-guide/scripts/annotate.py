"""Annotations sur captures d'ecran (Pillow).

Utilise pour ajouter des encadres rouges + fleches numerotees sur les boutons
critiques des captures, afin d'attirer l'oeil du lecteur.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont

RED = (220, 38, 38, 255)  # red-600
WHITE = (255, 255, 255, 255)
BLACK = (15, 23, 42, 255)  # slate-900
ARROW_WIDTH = 3
BOX_WIDTH = 3
LABEL_FONT_SIZE = 22


def _load_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, LABEL_FONT_SIZE)
    return ImageFont.load_default()


def annotate(
    source: Path,
    target: Path,
    boxes: Iterable[tuple[int, int, int, int, str]] = (),
) -> Path:
    """Genere une copie annotee de `source` vers `target`.

    `boxes` : iterable de (x1, y1, x2, y2, label). label = court texte ou numero.
    Encadre rouge autour du rectangle + pastille numero a cote.
    """
    img = Image.open(source).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font = _load_font()

    for x1, y1, x2, y2, label in boxes:
        draw.rectangle([(x1, y1), (x2, y2)], outline=RED, width=BOX_WIDTH)
        # Pastille label en haut a droite du rectangle
        pad = 6
        text_bbox = draw.textbbox((0, 0), label, font=font)
        tw = text_bbox[2] - text_bbox[0]
        th = text_bbox[3] - text_bbox[1]
        bx1 = x2 + 8
        by1 = y1
        bx2 = bx1 + tw + 2 * pad
        by2 = by1 + th + 2 * pad
        draw.rectangle([(bx1, by1), (bx2, by2)], fill=RED)
        draw.text((bx1 + pad, by1 + pad), label, fill=WHITE, font=font)

    out = Image.alpha_composite(img, overlay).convert("RGB")
    target.parent.mkdir(parents=True, exist_ok=True)
    out.save(target, format="PNG")
    return target
