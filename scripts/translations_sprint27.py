#!/usr/bin/env python3
"""Traductions Sprint 27 — FR → EN/ES/MG.

FEAT-062 : support de l'imprimante à ruban continu Brother QL-810W
(réglages « Impressions — Ruban continu » et boutons ruban sur les écrans de
sélection). La page intermédiaire d'impression a été retirée en cours de
sprint : ses chaînes ne sont plus ici.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint27.py
"""
from __future__ import annotations

from pathlib import Path

_ENABLED_HELP = "Affiche le bouton « Ruban » sur les écrans d'impression."
_LABEL_LEN_HELP = "Doit correspondre à la longueur de coupe réglée dans le pilote Brother."
_CARD_LEN_HELP = (
    "89 mm : juste sous le format continu natif du pilote Brother (62 × 89,9 mm)."
)
_TWO_COLOR_HELP = "Rouge sur les cartes membres. Les étiquettes restent monochromes."

TRANSLATIONS = {
    "en": {
        "Impressions — Ruban continu (Brother QL)": "Printing — Continuous tape (Brother QL)",
        "Imprimante à ruban disponible": "Tape printer available",
        _ENABLED_HELP: "Shows the “Tape” button on the printing screens.",
        "Largeur du ruban (mm)": "Tape width (mm)",
        "Longueur d'une étiquette (mm)": "Label length (mm)",
        _LABEL_LEN_HELP: "Must match the cut length set in the Brother driver.",
        "Longueur d'une carte membre (mm)": "Member card length (mm)",
        _CARD_LEN_HELP: (
            "89 mm: just under the Brother driver's native continuous size (62 × 89.9 mm)."
        ),
        "Ruban bicolore noir/rouge": "Two-colour black/red tape",
        _TWO_COLOR_HELP: "Red on member cards. Labels stay monochrome.",
        "Logo Ofelia sur les étiquettes": "Ofelia logo on labels",
        "Ruban %(w)s mm (Brother QL)": "%(w)s mm tape (Brother QL)",
    },
    "es": {
        "Impressions — Ruban continu (Brother QL)": "Impresiones — Cinta continua (Brother QL)",
        "Imprimante à ruban disponible": "Impresora de cinta disponible",
        _ENABLED_HELP: "Muestra el botón « Cinta » en las pantallas de impresión.",
        "Largeur du ruban (mm)": "Ancho de la cinta (mm)",
        "Longueur d'une étiquette (mm)": "Longitud de una etiqueta (mm)",
        _LABEL_LEN_HELP: (
            "Debe coincidir con la longitud de corte configurada en el controlador Brother."
        ),
        "Longueur d'une carte membre (mm)": "Longitud de una tarjeta de socio (mm)",
        _CARD_LEN_HELP: (
            "89 mm: justo por debajo del tamaño continuo nativo del controlador "
            "Brother (62 × 89,9 mm)."
        ),
        "Ruban bicolore noir/rouge": "Cinta bicolor negro/rojo",
        _TWO_COLOR_HELP: "Rojo en las tarjetas de socio. Las etiquetas siguen monocromas.",
        "Logo Ofelia sur les étiquettes": "Logotipo Ofelia en las etiquetas",
        "Ruban %(w)s mm (Brother QL)": "Cinta de %(w)s mm (Brother QL)",
    },
    "mg": {
        "Impressions — Ruban continu (Brother QL)": "Fanontana — Riban mitohy (Brother QL)",
        "Imprimante à ruban disponible": "Misy mpanonta riban",
        _ENABLED_HELP: "Mampiseho ny bokotra « Riban » eo amin'ny pejy fanontana.",
        "Largeur du ruban (mm)": "Sakan'ny riban (mm)",
        "Longueur d'une étiquette (mm)": "Halavan'ny marika (mm)",
        _LABEL_LEN_HELP: (
            "Tsy maintsy mifanaraka amin'ny halavan'ny fanapahana voafaritra ao "
            "amin'ny pilote Brother."
        ),
        "Longueur d'une carte membre (mm)": "Halavan'ny karatra mpikambana (mm)",
        _CARD_LEN_HELP: (
            "89 mm: eo ambanin'ny refy mitohy voajanahary ao amin'ny pilote "
            "Brother (62 × 89,9 mm)."
        ),
        "Ruban bicolore noir/rouge": "Riban loko roa mainty/mena",
        _TWO_COLOR_HELP: "Mena amin'ny karatra mpikambana. Mainty ihany ny marika.",
        "Logo Ofelia sur les étiquettes": "Logo Ofelia eo amin'ny marika",
        "Ruban %(w)s mm (Brother QL)": "Riban %(w)s mm (Brother QL)",
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
