"""FEAT-052 — helpers ISSN (validation + extraction depuis EAN-13 977)."""
from apps.core.issn import (
    format_issn,
    issn_check_digit,
    issn_from_ean13,
    normalize_issn,
    validate_issn,
)


def test_check_digit_x():
    assert issn_check_digit("1828552") == "X"


def test_issn_from_ean13_real_example():
    assert issn_from_ean13("9771828552248") == "1828552X"


def test_issn_from_ean13_ignores_variant_digits():
    # Deux numéros (variantes) d'une même revue → même ISSN.
    assert issn_from_ean13("9771828552248") == issn_from_ean13("9771828552019")


def test_issn_from_ean13_rejects_isbn():
    assert issn_from_ean13("9782070368228") is None


def test_validate_issn_ok():
    assert validate_issn("1828552X")
    assert validate_issn("1828-552X")  # tiret toléré (normalisé)


def test_validate_issn_bad_checksum():
    assert not validate_issn("18285521")


def test_validate_issn_bad_length():
    assert not validate_issn("123456")


def test_normalize_and_format():
    assert normalize_issn(" 1828-552x ") == "1828552X"
    assert format_issn("1828552X") == "1828-552X"
