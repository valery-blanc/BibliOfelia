#!/usr/bin/env python3
"""Traductions Sprint 29 — FR → EN/ES/MG.

Couvre FEAT-074 (suppression du chemin d'impression CUPS). Une seule chaîne
change : la description de l'écran « Étiquettes codes Ofelia » dans le menu
Avancé, qui annonçait un envoi direct à une imprimante CUPS et parle désormais
du ruban 62 mm. Le vocabulaire suit celui déjà retenu pour le bouton
« Ruban %(w)s mm (Brother QL) » : *tape* / *cinta* / *riban*.

Les chaînes supprimées (« Imprimer (CUPS) », « Serveur CUPS », étape
« Imprimante » du wizard…) sortent d'elles-mêmes des `.po` grâce au
`--no-obsolete` de `makemessages`.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint29.py
"""
from __future__ import annotations

from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

_LABELS_HELP = (
    "Génère les étiquettes (code Ofelia + titre + emplacement) à coller sur les "
    "ouvrages. PDF planche A4 ou ruban 62 mm pour l'étiqueteuse Brother QL."
)

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        _LABELS_HELP: (
            "Generates the labels (Ofelia code + title + location) to stick on the "
            "books. A4 PDF sheet or 62 mm tape for the Brother QL label printer."
        ),
    },
    "es": {
        _LABELS_HELP: (
            "Genera las etiquetas (código Ofelia + título + ubicación) para pegar en "
            "los libros. Hoja PDF A4 o cinta de 62 mm para la etiquetadora Brother QL."
        ),
    },
    "mg": {
        _LABELS_HELP: (
            "Mamorona ny marika (kaody Ofelia + lohateny + toerana) hapetaka amin'ny "
            "boky. Taratasy PDF A4 na riban 62 mm ho an'ny mpanonta marika Brother QL."
        ),
    },
}


def _unescape(value: str) -> str:
    return (
        value.replace('\\"', '"')
        .replace("\n", "\n")
        .replace("\t", "\t")
        .replace("\\\\", "\\")
    )


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\n")
        .replace("\t", "\t")
    )


def _read_value(lines: list[str], start: int, keyword: str) -> tuple[str, int]:
    """Lit `keyword "..."` + ses lignes de continuation. Renvoie (valeur, index suivant)."""
    first = lines[start][len(keyword):].strip()
    parts = [_unescape(first.strip('"'))]
    i = start + 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(_unescape(lines[i].strip().strip('"')))
        i += 1
    return "".join(parts), i


def _clean_comments(block: list[str]) -> list[str]:
    """Retire le drapeau `fuzzy` et les anciens msgid `#|` d'un bloc traduit."""
    out = []
    for line in block:
        if line.startswith("#|"):
            continue
        if line.startswith("#,"):
            flags = [f.strip() for f in line[2:].split(",") if f.strip() != "fuzzy"]
            if not flags:
                continue
            line = "#, " + ", ".join(flags)
        out.append(line)
    return out


def apply_lang(lang: str) -> int:
    """Applique les traductions du sprint à un `.po`. Renvoie le nombre de chaînes."""
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0
    singles = TRANSLATIONS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []  # commentaires en attente du msgid courant
    count = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            pending.append(line)
            i += 1
            continue
        if not line.startswith("msgid "):
            out.extend(pending)
            pending = []
            out.append(line)
            i += 1
            continue

        msgid, j = _read_value(lines, i, "msgid ")
        header = lines[i:j]

        if j < len(lines) and lines[j].startswith("msgstr ") and msgid in singles:
            _v, k = _read_value(lines, j, "msgstr ")
            out.extend(_clean_comments(pending))
            out.extend(header)
            out.append(f'msgstr "{_escape(singles[msgid])}"')
            count += 1
            pending = []
            i = k
            continue

        out.extend(pending)
        pending = []
        out.extend(header)
        i = j

    out.extend(pending)
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return count


def main() -> None:
    for lang in ("en", "es", "mg"):
        print(f"[{lang}] {apply_lang(lang)} chaîne(s)")


if __name__ == "__main__":
    main()
