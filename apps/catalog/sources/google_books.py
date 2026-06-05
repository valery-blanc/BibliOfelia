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
    # La clé API est facultative : l'API Google Books répond aussi sans clé
    # (quota par IP). Sans clé → on interroge quand même (meilleure couverture,
    # notamment les ISBN hors fonds FR/EN — cf. FEAT-050).
    api_key = (Setting.get("metadata.google_books_api_key", "") or "").strip()
    params = {"q": f"isbn:{isbn}"}
    if api_key:
        params["key"] = api_key
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


def _volume_to_candidate(volume: dict) -> dict:
    info = (volume or {}).get("volumeInfo") or {}
    isbn_13 = isbn_10 = ""
    for ident in info.get("industryIdentifiers", []) or []:
        val = re.sub(r"[^0-9Xx]", "", ident.get("identifier", "") or "").upper()
        if ident.get("type") == "ISBN_13" or len(val) == 13:
            isbn_13 = isbn_13 or val
        elif ident.get("type") == "ISBN_10" or len(val) == 10:
            isbn_10 = isbn_10 or val
    year_match = _YEAR_RE.search(info.get("publishedDate", "") or "")
    return {
        "isbn_13": isbn_13 if len(isbn_13) == 13 else "",
        "isbn_10": isbn_10 if len(isbn_10) == 10 else "",
        "title": (info.get("title") or "").strip(),
        "subtitle": (info.get("subtitle") or "").strip(),
        "authors_text": "; ".join(info.get("authors", []) or []),
        "publisher": info.get("publisher", "") or "",
        "publication_year": int(year_match.group()) if year_match else None,
        "language": (info.get("language", "") or "")[:10],
        "summary": "",
        "subjects": [],
        "cover_url": "",
    }


def search(title: str, author: str = "", limit: int = 5) -> list[dict]:
    """Recherche par titre + auteur (FEAT-050, passe 2).

    Sans clé API Google Books configurée → liste vide silencieusement.
    """
    title = (title or "").strip()
    if not title:
        return []
    # Clé facultative (cf. lookup) : on interroge même sans clé.
    api_key = (Setting.get("metadata.google_books_api_key", "") or "").strip()
    q = f'intitle:"{title}"'
    if (author or "").strip():
        q += f' inauthor:"{author.strip()}"'
    params = {"q": q, "maxResults": max(1, min(limit, 40))}
    if api_key:
        params["key"] = api_key
    try:
        resp = httpx.get(_API_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info("Google Books search KO « %s » : %s", title, exc)
        return []
    return [_volume_to_candidate(v) for v in (data.get("items") or [])[:limit]]
