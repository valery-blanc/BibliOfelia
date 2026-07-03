"""Validation d'ISSN et extraction depuis un EAN-13 périodique (préfixe 977).

FEAT-052 : support des périodiques. Un magazine/revue porte un code-barres
EAN-13 commençant par ``977`` (« Bookland » des périodiques) :

    977  + 7 chiffres (les 7 premiers de l'ISSN, sans sa clé)
         + 2 chiffres de variante (numéro / prix)
         + 1 clé EAN-13

Exemple : ``9771828552248`` → segment ``1828552`` → clé ISSN (mod 11) ``X``
→ **ISSN 1828-552X**. On stocke l'ISSN normalisé sans tiret (``1828552X``).

Ne dépend pas de Django : utilisable partout (helpers, tests stdlib).
"""
from __future__ import annotations

import re

ISSN_EAN13_PREFIX = "977"


def issn_check_digit(seven_digits: str) -> str:
    """Clé de contrôle ISSN (mod 11) des 7 premiers chiffres. '0'-'9' ou 'X'."""
    if len(seven_digits) != 7 or not seven_digits.isdigit():
        raise ValueError("issn_check_digit: 7 chiffres requis")
    total = sum(int(ch) * weight for ch, weight in zip(seven_digits, range(8, 1, -1)))
    remainder = total % 11
    check = (11 - remainder) % 11
    return "X" if check == 10 else str(check)


def normalize_issn(value: str) -> str:
    """Retire tiret/espaces et met en majuscule (la clé peut être 'X')."""
    return re.sub(r"[^0-9Xx]", "", value or "").upper()


def validate_issn(value: str) -> bool:
    """True si `value` est un ISSN valide (8 caractères, clé correcte)."""
    issn = normalize_issn(value)
    if len(issn) != 8 or not issn[:7].isdigit():
        return False
    if not (issn[7].isdigit() or issn[7] == "X"):
        return False
    return issn_check_digit(issn[:7]) == issn[7]


def issn_from_ean13(code: str) -> str | None:
    """Extrait l'ISSN normalisé (8 car.) d'un EAN-13 977. None si pas 977/invalide.

    Reconstruit la clé ISSN à partir des 7 chiffres embarqués (les chiffres 4 à
    10 de l'EAN) ; la clé de l'EAN et les 2 chiffres de variante ne font pas
    partie de l'ISSN.
    """
    code = normalize_issn(code)
    if len(code) != 13 or not code.isdigit() or not code.startswith(ISSN_EAN13_PREFIX):
        return None
    seven = code[3:10]
    return seven + issn_check_digit(seven)


def format_issn(value: str) -> str:
    """Affichage lisible : ``1828552X`` → ``1828-552X``. Renvoie tel quel sinon."""
    issn = normalize_issn(value)
    if len(issn) != 8:
        return value or ""
    return f"{issn[:4]}-{issn[4:]}"
