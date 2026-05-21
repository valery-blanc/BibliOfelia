"""Génération et validation d'EAN13 internes (préfixes 290/291).

SPEC §5.2 Item : préfixe 290 pour exemplaires, 291 pour cartes membres.
"""
from __future__ import annotations


def ean13_checksum(twelve_digits: str) -> int:
    """Calcule le 13e chiffre de contrôle EAN-13."""
    if len(twelve_digits) != 12 or not twelve_digits.isdigit():
        raise ValueError("ean13_checksum: 12 chiffres requis")
    total = 0
    for i, ch in enumerate(twelve_digits):
        n = int(ch)
        total += n * (3 if i % 2 else 1)
    return (10 - total % 10) % 10


def build_ean13(prefix: str, sequence: int) -> str:
    """Construit un EAN13 = prefix(3) + sequence(9) + checksum(1)."""
    if len(prefix) != 3 or not prefix.isdigit():
        raise ValueError("prefix doit faire 3 chiffres")
    if not 0 < sequence < 10**9:
        raise ValueError("sequence hors plage")
    body = f"{prefix}{sequence:09d}"
    return body + str(ean13_checksum(body))


def validate_ean13(code: str) -> bool:
    if len(code) != 13 or not code.isdigit():
        return False
    return ean13_checksum(code[:12]) == int(code[12])
