#!/usr/bin/env python3
"""Traductions Sprint 37 — FR → EN/ES/MG.

FEAT-096 : bouton Export Excel sur la page catalogue.

À rejouer APRÈS `makemessages` :
    python scripts/translations_sprint37.py
"""
from __future__ import annotations

import re
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

# fr: (en, es, mg)
TABLE: dict[str, tuple[str, str, str]] = {
    "Export Excel": (
        "Excel export",
        "Exportar Excel",
        "Export Excel",
    ),
    "Télécharge toutes les lignes de la recherche, pas seulement la page affichée.": (
        "Downloads every row of the search, not just the current page.",
        "Descarga todas las filas de la búsqueda, no solo la página visible.",
        "Maka ny andalana rehetra amin'ny fikarohana, tsy ny pejy hita ihany.",
    ),
}

TRANSLATIONS = {
    "en": {fr: values[0] for fr, values in TABLE.items()},
    "es": {fr: values[1] for fr, values in TABLE.items()},
    "mg": {fr: values[2] for fr, values in TABLE.items()},
}

PLURALS: dict[str, dict[str, tuple[str, str]]] = {
    "en": {},
    "es": {},
    "mg": {},
}


def _unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _read_value(lines: list[str], start: int, keyword: str) -> tuple[str, int]:
    first = lines[start][len(keyword):].strip()
    parts = [_unescape(first.strip('"'))]
    i = start + 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(_unescape(lines[i].strip().strip('"')))
        i += 1
    return "".join(parts), i


def _clean_comments(block: list[str]) -> list[str]:
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


def apply_lang(lang: str) -> tuple[int, int]:
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0, 0
    singles = TRANSLATIONS.get(lang, {})
    plurals = PLURALS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []
    n_single = n_plural = 0
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

        if j < len(lines) and lines[j].startswith("msgid_plural "):
            _plural_id, k = _read_value(lines, j, "msgid_plural ")
            header = header + lines[j:k]
            while k < len(lines) and re.match(r"^msgstr\[\d\] ", lines[k]):
                _v, k = _read_value(lines, k, lines[k][: lines[k].index(" ") + 1])
            if msgid in plurals:
                sing, plur = plurals[msgid]
                out.extend(_clean_comments(pending))
                out.extend(header)
                out.append(f'msgstr[0] "{_escape(sing)}"')
                out.append(f'msgstr[1] "{_escape(plur)}"')
                n_plural += 1
            else:
                out.extend(pending)
                out.extend(lines[i:k])
            pending = []
            i = k
            continue

        if j < len(lines) and lines[j].startswith("msgstr "):
            _v, k = _read_value(lines, j, "msgstr ")
            if msgid in singles and singles[msgid]:
                out.extend(_clean_comments(pending))
                out.extend(header)
                out.append(f'msgstr "{_escape(singles[msgid])}"')
                n_single += 1
            else:
                out.extend(pending)
                out.extend(lines[i:k])
            pending = []
            i = k
            continue

        out.extend(pending)
        pending = []
        out.extend(header)
        i = j

    out.extend(pending)
    payload = ("\n".join(out) + "\n").encode("utf-8")
    with open(po_path, "wb") as handle:
        handle.write(payload)
    return n_single, n_plural


def main() -> None:
    for lang in ("en", "es", "mg"):
        single, plural = apply_lang(lang)
        print(f"[{lang}] {single} chaîne(s) + {plural} pluriel(s)")


if __name__ == "__main__":
    main()
