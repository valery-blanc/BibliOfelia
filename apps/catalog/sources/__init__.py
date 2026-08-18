"""Sources externes de métadonnées (FEAT-031).

Chaque module expose ``lookup(isbn: str) -> dict | None``. Le dict retourné
contient les champs normalisés : ``title``, ``subtitle``, ``authors_text``,
``publisher``, ``publication_year``, ``language``, ``summary``. Renvoie
``None`` si la source n'a pas répondu ou n'a rien trouvé.
"""
from __future__ import annotations


class SourceRateLimited(Exception):
    """Levée par une source quand le fournisseur répond 429 (quota atteint)
    et que le back-off n'a pas suffi. Permet à l'appelant de distinguer
    « quota épuisé, réessayer plus tard » de « rien trouvé »."""


from . import bne, bnf, google_books, k10plus, openlibrary, swisscovery  # noqa: E402

SOURCES = {
    "openlibrary": openlibrary.lookup,
    "google_books": google_books.lookup,
    "bnf": bnf.lookup,
    "bne": bne.lookup,
    # FEAT-060 : couvrent les éditeurs suisses et germanophones absents des
    # bibliothèques nationales FR/ES.
    "swisscovery": swisscovery.lookup,
    "k10plus": k10plus.lookup,
}

# FEAT-052 : lookup par ISSN (périodiques). Seules les sources SRU des
# bibliothèques nationales cataloguent les publications en série ; OpenLibrary
# et Google Books n'indexent pas l'ISSN → absentes de ce registre. La BnF est
# la source réaliste pour les revues FR ; la BNE est un complément.
# FEAT-060 : Swisscovery indexe aussi l'ISSN (Alma) ; K10plus non (`pica.iss`
# ne répond pas) → absent d'ici.
ISSN_SOURCES = {
    "bnf": bnf.lookup_issn,
    "bne": bne.lookup_issn,
    "swisscovery": swisscovery.lookup_issn,
}

# FEAT-050 : recherche par titre + auteur (passe 2 du catalogage Excel).
# Chaque ``search(title, author, limit)`` renvoie une liste de candidats
# normalisés (même schéma que ``lookup``). Jamais d'exception réseau.
SEARCHES = {
    "openlibrary": openlibrary.search,
    "google_books": google_books.search,
    "bnf": bnf.search,
    "bne": bne.search,
    "swisscovery": swisscovery.search,
    "k10plus": k10plus.search,
}

SOURCE_LABELS = {
    "openlibrary": "OpenLibrary",
    "google_books": "Google Books",
    "bnf": "BnF (livres FR)",
    "bne": "BNE (livres ES)",
    "swisscovery": "Swisscovery (livres CH)",
    "k10plus": "K10plus (livres DE)",
}
