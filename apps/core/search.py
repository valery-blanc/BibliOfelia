"""Recherche globale : classification de requête + FTS5. SPEC §6.1.

La barre de recherche unique sert à la fois de moteur plein-texte sur les
notices et de point d'entrée scan (EAN13 exemplaire 290…, carte membre 291…,
ISBN 10/13). `classify_query` décide du type ; `fts_search` interroge la table
virtuelle `catalog_record_fts` créée par la migration `catalog/0002_fts5`.
"""
from __future__ import annotations

from django.db import connection

_CODE_TRANSLATE = {ord(c): None for c in " -."}


def normalize_code(raw: str) -> str:
    """Retire séparateurs courants d'un code scanné/saisi."""
    return (raw or "").translate(_CODE_TRANSLATE).strip().upper()


def looks_like_isbn10(code: str) -> bool:
    return len(code) == 10 and code[:9].isdigit() and (code[9].isdigit() or code[9] == "X")


def classify_query(raw: str) -> tuple[str, str]:
    """Retourne (kind, value).

    kind ∈ {"item", "member", "isbn", "text"} :
    - "item"   : EAN13 commençant par 290 (exemplaire Ofelia)
    - "member" : EAN13 commençant par 291 (carte membre Ofelia)
    - "isbn"   : ISBN-13 ou ISBN-10 plausible
    - "text"   : recherche plein-texte
    """
    code = normalize_code(raw)
    if len(code) == 13 and code.isdigit():
        if code.startswith("290"):
            return "item", code
        if code.startswith("291"):
            return "member", code
        return "isbn", code
    if looks_like_isbn10(code):
        return "isbn", code
    return "text", (raw or "").strip()


def fts_match_expression(text: str) -> str:
    """Construit une expression MATCH FTS5 : préfixe sur chaque terme."""
    terms = [t.replace('"', '""') for t in text.split() if t]
    return " ".join(f'"{t}"*' for t in terms)


def fts_search(text: str, limit: int = 200) -> list[int]:
    """Retourne les record_id classés par pertinence FTS5 (meilleur d'abord)."""
    match = fts_match_expression(text.strip())
    if not match:
        return []
    with connection.cursor() as cur:
        cur.execute(
            "SELECT record_id FROM catalog_record_fts "
            "WHERE catalog_record_fts MATCH %s ORDER BY rank LIMIT %s",
            [match, limit],
        )
        return [row[0] for row in cur.fetchall()]
