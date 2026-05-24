"""Source Google Books (FEAT-031).

Nécessite une clé API Google Books, stockée via
``Setting.get('metadata.google_books_api_key')`` (UI : Paramètres → Sources
de métadonnées). Sans clé : la source renvoie ``None`` silencieusement.
"""
from __future__ import annotations

import logging
import re

import httpx

from apps.core.models import Setting

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")
_API_URL = "https://www.googleapis.com/books/v1/volumes"


def lookup(raw_isbn: str) -> dict | None:
    isbn = re.sub(r"[^0-9Xx]", "", raw_isbn or "").upper()
    if len(isbn) not in (10, 13):
        return None
    api_key = (Setting.get("metadata.google_books_api_key", "") or "").strip()
    if not api_key:
        return None
    params = {"q": f"isbn:{isbn}", "key": api_key}
    try:
        resp = httpx.get(_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info("Google Books KO ISBN %s : %s", isbn, exc)
        return None
    items = data.get("items") or []
    if not items:
        return None
    info = (items[0] or {}).get("volumeInfo") or {}
    year_match = _YEAR_RE.search(info.get("publishedDate", "") or "")

    # Categories : ex ["Fiction / Adventure"] → on splitte par " / "
    subjects = []
    for cat in info.get("categories", []) or []:
        if not cat:
            continue
        for part in cat.split("/"):
            name = part.strip()
            if name:
                subjects.append(name)

    # Cover : imageLinks fournit smallThumbnail / thumbnail (parfois small/medium/large/extraLarge)
    image_links = info.get("imageLinks") or {}
    cover_url = (
        image_links.get("extraLarge")
        or image_links.get("large")
        or image_links.get("medium")
        or image_links.get("thumbnail")
        or image_links.get("smallThumbnail")
        or ""
    )
    # Force HTTPS (Google renvoie parfois http://)
    if cover_url.startswith("http://"):
        cover_url = "https://" + cover_url[len("http://"):]

    return {
        "isbn_13": isbn if len(isbn) == 13 else "",
        "isbn_10": isbn if len(isbn) == 10 else "",
        "title": info.get("title", "") or "",
        "subtitle": info.get("subtitle", "") or "",
        "authors_text": "; ".join(info.get("authors", []) or []),
        "publisher": info.get("publisher", "") or "",
        "publication_year": int(year_match.group()) if year_match else None,
        "language": (info.get("language", "") or "")[:10],
        "summary": info.get("description", "") or "",
        "subjects": subjects,
        "cover_url": cover_url,
    }
