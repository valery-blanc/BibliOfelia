#!/usr/bin/env python3
"""Traductions Sprint 24 — FR → EN/ES/MG.

- BUG-021 : restauration des sections d'impression dans /admin/settings/
  (libellés + sous-titres retirés par FEAT-047, donc supprimés des .po par
  makemessages --no-obsolete). Traductions reprises de l'historique git.
- FEAT-055 : récolement à la douchette — aucune nouvelle chaîne d'app (attribut
  HTML seul), documenté ici pour mémoire.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint24.py
"""
from __future__ import annotations

from pathlib import Path

_CARDS_SUB = "Cartes membres : nombre par A4, photo, logo OFELIA"
_LABELS_SUB = "Étiquettes codes Ofelia : dimensions, titre, logo"

TRANSLATIONS = {
    "en": {
        "Impressions — Cartes membres": "Printing — Member cards",
        "Impressions — Étiquettes codes Ofelia": "Printing — Ofelia code labels",
        _CARDS_SUB: "Member cards: number per A4, photo, OFELIA logo",
        _LABELS_SUB: "Ofelia code labels: dimensions, title, logo",
    },
    "es": {
        "Impressions — Cartes membres": "Impresiones — Tarjetas de miembro",
        "Impressions — Étiquettes codes Ofelia": "Impresiones — Etiquetas códigos Ofelia",
        _CARDS_SUB: "Tarjetas de miembro: número por A4, foto, logo OFELIA",
        _LABELS_SUB: "Etiquetas códigos Ofelia: dimensiones, título, logo",
    },
    "mg": {
        "Impressions — Cartes membres": "Fanontana — Karatra mpikambana",
        "Impressions — Étiquettes codes Ofelia": "Fanontana — Marika kaody Ofelia",
        _CARDS_SUB: "Karatra mpikambana : isa isaky ny A4, sary, logo OFELIA",
        _LABELS_SUB: "Marika kaody Ofelia : haben'izany, lohateny, logo",
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
