#!/usr/bin/env python3
"""Traductions Sprint 21 / FEAT-052 (périodiques ISSN) — FR → EN/ES/MG.

Applique les traductions directement aux fichiers .po (stdlib, sans Docker).
À rejouer APRÈS `makemessages` (qui insère les nouveaux msgid) :
    python scripts/translations_sprint21.py
"""
from __future__ import annotations

from pathlib import Path

_ISSN_HELP = "Pour les revues/magazines (code-barres 977). Ex. 1234-5679."
_ISSN_ERR = "ISSN invalide (8 caractères, ex. 1234-5679)."

TRANSLATIONS = {
    "en": {
        "ISSN": "ISSN",
        _ISSN_HELP: "For magazines/journals (977 barcode). E.g. 1234-5679.",
        _ISSN_ERR: "Invalid ISSN (8 characters, e.g. 1234-5679).",
    },
    "es": {
        "ISSN": "ISSN",
        _ISSN_HELP: "Para revistas/periódicos (código de barras 977). Ej. 1234-5679.",
        _ISSN_ERR: "ISSN no válido (8 caracteres, ej. 1234-5679).",
    },
    "mg": {
        "ISSN": "ISSN",
        _ISSN_HELP: "Ho an'ny gazety/magazine (barcode 977). Oh. 1234-5679.",
        _ISSN_ERR: "ISSN diso (litera 8, oh. 1234-5679).",
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
