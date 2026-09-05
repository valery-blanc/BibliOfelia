"""FEAT-063 : résolution d'un code d'exemplaire saisi ou scanné.

Un exemplaire peut être désigné par trois codes : le **code Ofelia** que
BibliOfelia lui a attribué (EAN13 préfixe 290, imprimé sur l'étiquette), un
**code Ofelia externe** posé hors du système — étiquette d'une autre
bibliothèque, d'un donateur, d'un catalogage antérieur au projet — et le
**code interne** ``OFL-YYYYMMDD-NNNN`` affiché à l'écran.

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
# OFL-YYYYMMDD-NNNN compacté (tirets retirés par normalize_code).
_INTERNAL_ID_COMPACT = re.compile(r"^OFL(\d{8})(\d{4})$")
_INTERNAL_ID_HYPHEN = re.compile(r"^OFL-\d{8}-\d{4}$", re.IGNORECASE)


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


def _stored_internal_id(code: str, raw: str) -> str | None:
    """Forme stockée ``OFL-YYYYMMDD-NNNN``, ou None si ça n'en a pas l'air.

    On accepte la saisie avec ou sans tirets : le bibliothécaire recopie
    souvent ``OFL-20260525-0014`` depuis l'écran, et ``normalize_code``
    (prêt, retour) a déjà retiré les séparateurs.
    """
    compact = _INTERNAL_ID_COMPACT.fullmatch(code)
    if compact:
        return f"OFL-{compact.group(1)}-{compact.group(2)}"
    stripped = (raw or "").strip()
    if _INTERNAL_ID_HYPHEN.fullmatch(stripped):
        return stripped.upper()
    return None


def find_item(raw: str, queryset=None) -> Item | None:
    """Exemplaire désigné par `raw`, ou None.

    Ordre : code Ofelia (290…) d'abord, puis code externe, puis code interne
    ``OFL-…``. Un code externe qui aurait la forme d'un EAN13 Ofelia ne peut
    donc jamais détourner le scan d'une étiquette maison.
    """
    code = normalize_code(raw)
    qs = Item.objects.all() if queryset is None else queryset
    if is_valid_external_code(code):
        hit = qs.filter(ean13=code).first() or qs.filter(external_code=code).first()
        if hit:
            return hit
    internal = _stored_internal_id(code, raw)
    if internal:
        return qs.filter(internal_id__iexact=internal).first()
    return None
