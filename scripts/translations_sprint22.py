#!/usr/bin/env python3
"""Traductions Sprint 22 / FEAT-053 (import Excel — métadonnées fiche) — FR → EN/ES/MG.

Applique les traductions directement aux fichiers .po (stdlib, sans Docker).
À rejouer APRÈS `makemessages` (qui insère les nouveaux msgid) :
    python scripts/translations_sprint22.py
"""
from __future__ import annotations

from pathlib import Path

_TITLE = "optionnel : titre de la fiche"
_AUTHOR = "optionnel : auteur(s), séparés par des points-virgules"
_TYPE = "optionnel : type de document (Livre, BD / manga, Revue, Journal, CD audio, Autre)"
_EDITOR = "optionnel : éditeur"
_YEAR = "optionnel : année de publication"
_LANGUAGE = "optionnel : code langue (ex. fr, en, es)"
_TAGS = "optionnel : liste de tags séparés par des virgules"
_CONDITION = "optionnel : état de l'exemplaire (Neuf, Bon, Usé, Abîmé)"
_OVERWRITE = (
    "Chaque colonne ci-dessus est facultative. Si elle est présente et remplie, "
    "elle écrase l'information correspondante de la fiche (même déjà existante) ; "
    "une cellule vide laisse l'information en place."
)

TRANSLATIONS = {
    "en": {
        _TITLE: "optional: record title",
        _AUTHOR: "optional: author(s), separated by semicolons",
        _TYPE: "optional: document type (Book, Comic / manga, Magazine, Newspaper, Audio CD, Other)",
        _EDITOR: "optional: publisher",
        _YEAR: "optional: publication year",
        _LANGUAGE: "optional: language code (e.g. fr, en, es)",
        _TAGS: "optional: list of tags separated by commas",
        _CONDITION: "optional: copy condition (New, Good, Worn, Damaged)",
        _OVERWRITE: (
            "Each column above is optional. If it is present and filled in, it "
            "overwrites the matching field of the record (even an existing one); "
            "an empty cell leaves the information in place."
        ),
    },
    "es": {
        _TITLE: "opcional: título de la ficha",
        _AUTHOR: "opcional: autor(es), separados por puntos y comas",
        _TYPE: "opcional: tipo de documento (Libro, Cómic / manga, Revista, Periódico, CD de audio, Otro)",
        _EDITOR: "opcional: editorial",
        _YEAR: "opcional: año de publicación",
        _LANGUAGE: "opcional: código de idioma (ej. fr, en, es)",
        _TAGS: "opcional: lista de etiquetas separadas por comas",
        _CONDITION: "opcional: estado del ejemplar (Nuevo, Bueno, Desgastado, Dañado)",
        _OVERWRITE: (
            "Cada columna anterior es opcional. Si está presente y rellenada, "
            "sobrescribe el campo correspondiente de la ficha (incluso una ya "
            "existente); una celda vacía deja la información en su lugar."
        ),
    },
    "mg": {
        _TITLE: "tsy voatery: lohatenin'ny rakitra",
        _AUTHOR: "tsy voatery: mpanoratra, sarahina amin'ny teboka sy faingo (;)",
        _TYPE: "tsy voatery: karazana boky (Boky, BD / manga, Gazetiboky, Gazety, CD audio, Hafa)",
        _EDITOR: "tsy voatery: mpamoaka",
        _YEAR: "tsy voatery: taona namoahana",
        _LANGUAGE: "tsy voatery: kaody fiteny (oh. fr, en, es)",
        _TAGS: "tsy voatery: lisitry ny tag sarahina amin'ny faingo",
        _CONDITION: "tsy voatery: toetran'ny santiona (Vaovao, Tsara, Simba kely, Simba)",
        _OVERWRITE: (
            "Tsy voatery ny tsanganana rehetra etsy ambony. Raha misy sy feno "
            "izy, dia manoloana ny saha mifanaraka amin'ny rakitra (na efa misy "
            "aza); ny sela banga dia mamela ny mombamomba misy."
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
