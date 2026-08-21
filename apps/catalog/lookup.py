"""FEAT-063 : résolution d'un code d'exemplaire saisi ou scanné.

Un exemplaire peut être désigné par deux codes : le **code Ofelia** que
BibliOfelia lui a attribué (EAN13 préfixe 290, imprimé sur l'étiquette) et un
**code Ofelia externe** posé hors du système — étiquette d'une autre
bibliothèque, d'un donateur, d'un catalogage antérieur au projet.

Toutes les entrées qui acceptent un code d'exemplaire (prêt, retour,
récolement, recherche, API) passent par `find_item` : le jour où un troisième
code apparaît, il n'y a qu'un endroit à changer.

`apps.core.search.classify_query` reste sans accès base — la classification
d'une requête est syntaxique, la résolution est ici.
"""
from __future__ import annotations

import re

from apps.core.search import normalize_code

from .models import Item

EXTERNAL_CODE_MAX_LENGTH = 20
_EXTERNAL_CODE_RE = re.compile(r"^[A-Z0-9]+$")


def normalize_external_code(raw: str) -> str:
    """Majuscules, sans espaces, tirets ni points.

    `BCF-1329 8781x` et `BCF13298781X` sont le même code, qu'il soit tapé au
    clavier ou envoyé par une douchette.
    """
    return normalize_code(raw)


def is_valid_external_code(code: str) -> bool:
    """Code externe déjà normalisé : alphanumérique, 20 caractères au plus."""
    return (
        bool(code)
        and len(code) <= EXTERNAL_CODE_MAX_LENGTH
        and bool(_EXTERNAL_CODE_RE.match(code))
    )


def find_item(raw: str, queryset=None) -> Item | None:
    """Exemplaire désigné par `raw`, ou None.

    Le code Ofelia est essayé en premier : un code externe qui aurait la forme
    d'un EAN13 Ofelia ne peut donc jamais détourner le scan d'une étiquette
    maison.
    """
    code = normalize_code(raw)
    if not is_valid_external_code(code):
        # Ni un code Ofelia (13 chiffres) ni un code externe possible : c'est du
        # texte libre, inutile d'interroger la base.
        return None
    qs = Item.objects.all() if queryset is None else queryset
    return qs.filter(ean13=code).first() or qs.filter(external_code=code).first()
