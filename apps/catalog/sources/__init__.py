"""Sources externes de métadonnées (FEAT-031).

Chaque module expose ``lookup(isbn: str) -> dict | None``. Le dict retourné
contient les champs normalisés : ``title``, ``subtitle``, ``authors_text``,
``publisher``, ``publication_year``, ``language``, ``summary``. Renvoie
``None`` si la source n'a pas répondu ou n'a rien trouvé.
"""
from __future__ import annotations

from . import bne, bnf, google_books, openlibrary

SOURCES = {
    "openlibrary": openlibrary.lookup,
    "google_books": google_books.lookup,
    "bnf": bnf.lookup,
    "bne": bne.lookup,
}

SOURCE_LABELS = {
    "openlibrary": "OpenLibrary",
    "google_books": "Google Books",
    "bnf": "BNF",
    "bne": "BNE",
}
