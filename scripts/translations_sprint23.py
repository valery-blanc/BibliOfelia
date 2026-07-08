#!/usr/bin/env python3
"""Traductions Sprint 23 / FEAT-054 (douchette USB keyboard-wedge) — FR → EN/ES/MG.

Applique les traductions directement aux fichiers .po (stdlib, sans Docker).
À rejouer APRÈS `makemessages` (qui insère les nouveaux msgid) :
    python scripts/translations_sprint23.py
"""
from __future__ import annotations

from pathlib import Path

_FORM_SUB = (
    "Choisissez les valeurs par défaut du lot, puis scannez les livres avec la "
    "douchette USB branchée sur ce poste."
)
_PANEL_HINT = (
    "Scannez sans cliquer nulle part. Représentez un même livre après quelques "
    "secondes pour ajouter un 2ᵉ exemplaire."
)
_TILE_SUB = (
    "Scanner les ISBN avec la douchette USB branchée sur ce poste, sans caméra."
)
_FINISH_HINT = (
    "Quand vous avez fini de scanner, cliquez ici pour vérifier la liste et "
    "l’envoyer au catalogue."
)
_EMPTY_DOUCHETTE = (
    "Scannez vos livres avec la douchette ci-dessus. La liste se remplit au fur "
    "et à mesure ; cliquez sur « Terminer et voir le lot » pour l’éditer et "
    "l’envoyer au catalogue."
)

TRANSLATIONS = {
    "en": {
        "OfeliaScan": "OfeliaScan",
        "Caméra": "Camera",
        "Douchette": "Barcode scanner",
        "Catalogage par douchette": "Cataloguing with a barcode scanner",
        "Cataloguer à la douchette": "Catalogue with a barcode scanner",
        _FORM_SUB: (
            "Choose the batch defaults, then scan the books with the USB barcode "
            "scanner plugged into this computer."
        ),
        "Scannez les livres avec la douchette": "Scan the books with the barcode scanner",
        _PANEL_HINT: (
            "Scan without clicking anywhere. Present the same book again after a "
            "few seconds to add a 2nd copy."
        ),
        _TILE_SUB: (
            "Scan ISBNs with the USB barcode scanner plugged into this computer, "
            "without a camera."
        ),
        "Terminer et voir le lot": "Finish and review the batch",
        _FINISH_HINT: (
            "When you have finished scanning, click here to review the list and "
            "send it to the catalogue."
        ),
        _EMPTY_DOUCHETTE: (
            "Scan your books with the barcode scanner above. The list fills up as "
            "you go; click “Finish and review the batch” to edit it and "
            "send it to the catalogue."
        ),
    },
    "es": {
        "OfeliaScan": "OfeliaScan",
        "Caméra": "Cámara",
        "Douchette": "Lector de código de barras",
        "Catalogage par douchette": "Catalogación con lector de código de barras",
        "Cataloguer à la douchette": "Catalogar con lector de código de barras",
        _FORM_SUB: (
            "Elija los valores por defecto del lote y luego escanee los libros con "
            "el lector de código de barras USB conectado a este equipo."
        ),
        "Scannez les livres avec la douchette": "Escanee los libros con el lector",
        _PANEL_HINT: (
            "Escanee sin hacer clic en ningún sitio. Vuelva a presentar el mismo "
            "libro tras unos segundos para añadir un 2.º ejemplar."
        ),
        _TILE_SUB: (
            "Escanear los ISBN con el lector de código de barras USB conectado a "
            "este equipo, sin cámara."
        ),
        "Terminer et voir le lot": "Terminar y revisar el lote",
        _FINISH_HINT: (
            "Cuando haya terminado de escanear, haga clic aquí para revisar la "
            "lista y enviarla al catálogo."
        ),
        _EMPTY_DOUCHETTE: (
            "Escanee sus libros con el lector de arriba. La lista se rellena sobre "
            "la marcha; haga clic en «Terminar y revisar el lote» para editarla y "
            "enviarla al catálogo."
        ),
    },
    "mg": {
        "OfeliaScan": "OfeliaScan",
        "Caméra": "Kamera",
        "Douchette": "Mpamaky barcode",
        "Catalogage par douchette": "Katalaogy amin'ny mpamaky barcode",
        "Cataloguer à la douchette": "Manao katalaogy amin'ny mpamaky barcode",
        _FORM_SUB: (
            "Fidio ny sanda mialoha ho an'ny andiany, avy eo scannerao ny boky "
            "amin'ny mpamaky barcode USB mifandray amin'ity solosaina ity."
        ),
        "Scannez les livres avec la douchette": "Scannerao ny boky amin'ny mpamaky barcode",
        _PANEL_HINT: (
            "Scannerao fa tsy mila mikitika na aiza na aiza. Asehoy indray ilay "
            "boky rehefa afaka segondra vitsivitsy mba hanampiana kopia faha-2."
        ),
        _TILE_SUB: (
            "Scannerao ny ISBN amin'ny mpamaky barcode USB mifandray amin'ity "
            "solosaina ity, tsy misy kamera."
        ),
        "Terminer et voir le lot": "Vitao ary jereo ny andiany",
        _FINISH_HINT: (
            "Rehefa vita ny fanaovana scan, tsindrio eto mba hijerena ny lisitra "
            "sy handefasana azy any amin'ny katalaogy."
        ),
        _EMPTY_DOUCHETTE: (
            "Scannerao ny bokinao amin'ny mpamaky barcode eo ambony. Mihafeno "
            "tsikelikely ny lisitra ; tsindrio « Vitao ary jereo ny andiany » "
            "mba hanova azy sy handefa azy any amin'ny katalaogy."
        ),
    },
}

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"


def _po_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def _defuzz(comment: str) -> str | None:
    if not comment.startswith("#,"):
        return comment
    flags = [f.strip() for f in comment[2:].split(",") if f.strip()]
    flags = [f for f in flags if f != "fuzzy"]
    return ("#, " + ", ".join(flags)) if flags else None


def _strip_trailing_fuzzy(out: list[str]) -> None:
    k = len(out) - 1
    while k >= 0 and out[k].startswith("#"):
        k -= 1
    block = out[k + 1:]
    if not block:
        return
    new: list[str] = []
    for c in block:
        if c.startswith("#|"):
            continue
        d = _defuzz(c)
        if d is not None:
            new.append(d)
    out[k + 1:] = new


def apply_lang(lang: str, mapping: dict[str, str]) -> int:
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0
    lines = po_path.read_text(encoding="utf-8").splitlines(keepends=False)
    out: list[str] = []
    count = 0
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("msgid ") and not (
            i + 1 < n and lines[i + 1].startswith("msgid_plural")
        ):
            parts = [_unescape(line[len("msgid "):].strip().strip('"'))]
            j = i + 1
            while j < n and lines[j].startswith('"'):
                parts.append(_unescape(lines[j].strip().strip('"')))
                j += 1
            msgid = "".join(parts)
            if msgid in mapping and mapping[msgid]:
                _strip_trailing_fuzzy(out)
                m = j + 1
                while m < n and lines[m].startswith('"'):
                    m += 1
                out.extend(lines[i:j])
                out.append(f'msgstr "{_po_escape(mapping[msgid])}"')
                count += 1
                i = m
                continue
        out.append(line)
        i += 1
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return count


def main() -> None:
    for lang, mapping in TRANSLATIONS.items():
        print(f"[{lang}] {apply_lang(lang, mapping)} entrée(s) traitée(s)")


if __name__ == "__main__":
    main()
