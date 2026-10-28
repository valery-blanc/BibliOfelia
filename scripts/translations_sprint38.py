#!/usr/bin/env python3
"""Traductions Sprint 38 — bouton « Réserver un livre ».

À rejouer après `makemessages`. Insère la chaîne si elle n'est pas encore
dans le catalogue (le poste de dev n'a pas toujours Docker).
"""
from __future__ import annotations

from pathlib import Path

LOCALE = Path(__file__).resolve().parent.parent / "locale"

# msgid -> (en, es, mg). Le français est la langue source (msgstr vide).
TABLE: dict[str, tuple[str, str, str]] = {
    "Réserver un livre": (
        "Reserve a book",
        "Reservar un libro",
        "Mamandrika boky",
    ),
    "Titre, auteur, ISBN ou code": (
        "Title, author, ISBN or code",
        "Título, autor, ISBN o código",
        "Lohateny, mpanoratra, ISBN na kaody",
    ),
    "Rechercher": ("Search", "Buscar", "Hikaroka"),
    "Aucun livre ne correspond.": (
        "No book matches.",
        "Ningún libro coincide.",
        "Tsy misy boky mifanaraka.",
    ),
    "Choisissez le livre à réserver.": (
        "Choose the book to reserve.",
        "Elija el libro que quiere reservar.",
        "Fidio ny boky hofandrihana.",
    ),
    "Tapez un nom pour filtrer": (
        "Type a name to filter",
        "Escriba un nombre para filtrar",
        "Soraty ny anarana iray hanivana",
    ),
}


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _has_msgid(text: str, msgid: str) -> bool:
    return f'msgid "{_escape(msgid)}"' in text


def _entry(msgid: str, msgstr: str) -> str:
    return f'\nmsgid "{_escape(msgid)}"\nmsgstr "{_escape(msgstr)}"\n'


def main() -> None:
    added = 0
    for lang, index in (("fr", None), ("en", 0), ("es", 1), ("mg", 2)):
        path = LOCALE / lang / "LC_MESSAGES" / "django.po"
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        chunks = []
        for msgid, translations in TABLE.items():
            if _has_msgid(text, msgid):
                continue
            msgstr = "" if index is None else translations[index]
            chunks.append(_entry(msgid, msgstr))
            added += 1
        if chunks:
            extra = ("".join(chunks)).encode("utf-8")
            if not raw.endswith(b"\n"):
                extra = b"\n" + extra
            path.write_bytes(raw + extra)
            print(f"{lang}: +{len(chunks)}")
        else:
            print(f"{lang}: déjà à jour")
    print(f"added={added}")


if __name__ == "__main__":
    main()
