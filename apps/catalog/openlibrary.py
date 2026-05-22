"""Lookup ISBN via OpenLibrary. SPEC §6.1.

`lookup_isbn` fait un appel HTTP direct court (timeout configurable). En cas
d'échec réseau (box hors-ligne) la fonction renvoie None et l'utilisateur
saisit la notice manuellement. La mise en file d'attente hors-ligne est un
raffinement ultérieur (dépend de la détection de connectivité, SPEC §7.3).
"""
from __future__ import annotations

import logging
import re

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")


def normalize_isbn(raw: str) -> str:
    return re.sub(r"[^0-9Xx]", "", raw or "").upper()


def lookup_isbn(raw_isbn: str) -> dict | None:
    """Interroge OpenLibrary. Retourne un dict de champs notice, ou None."""
    isbn = normalize_isbn(raw_isbn)
    if len(isbn) not in (10, 13):
        return None
    url = f"{settings.OPENLIBRARY_BASE_URL}/api/books"
    params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}
    try:
        resp = httpx.get(url, params=params, timeout=settings.OPENLIBRARY_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info("OpenLibrary indisponible pour ISBN %s : %s", isbn, exc)
        return None
    entry = data.get(f"ISBN:{isbn}")
    if not entry:
        return None
    year_match = _YEAR_RE.search(entry.get("publish_date", "") or "")
    return {
        "isbn_13": isbn if len(isbn) == 13 else "",
        "isbn_10": isbn if len(isbn) == 10 else "",
        "title": entry.get("title", ""),
        "subtitle": entry.get("subtitle", ""),
        "authors_text": "; ".join(
            a.get("name", "") for a in entry.get("authors", []) if a.get("name")
        ),
        "publisher": ", ".join(
            p.get("name", "") for p in entry.get("publishers", []) if p.get("name")
        ),
        "publication_year": year_match.group() if year_match else "",
    }
