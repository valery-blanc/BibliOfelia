"""Source OpenLibrary (FEAT-031)."""
from __future__ import annotations

import logging
import re

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")


def _normalize_isbn(raw: str) -> str:
    return re.sub(r"[^0-9Xx]", "", raw or "").upper()


def lookup(raw_isbn: str) -> dict | None:
    isbn = _normalize_isbn(raw_isbn)
    if len(isbn) not in (10, 13):
        return None
    url = f"{settings.OPENLIBRARY_BASE_URL}/api/books"
    params = {"bibkeys": f"ISBN:{isbn}", "format": "json", "jscmd": "data"}
    try:
        resp = httpx.get(url, params=params, timeout=settings.OPENLIBRARY_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info("OpenLibrary KO ISBN %s : %s", isbn, exc)
        return None
    entry = data.get(f"ISBN:{isbn}")
    if not entry:
        return None
    year_match = _YEAR_RE.search(entry.get("publish_date", "") or "")

    # Summary : description (str ou dict), sinon notes, sinon premier excerpt
    summary = ""
    desc = entry.get("description")
    if isinstance(desc, dict):
        summary = (desc.get("value") or "").strip()
    elif isinstance(desc, str):
        summary = desc.strip()
    if not summary:
        notes = entry.get("notes")
        if isinstance(notes, dict):
            summary = (notes.get("value") or "").strip()
        elif isinstance(notes, str):
            summary = notes.strip()
    if not summary:
        excerpts = entry.get("excerpts") or []
        if excerpts and isinstance(excerpts[0], dict):
            summary = (excerpts[0].get("text") or "").strip()

    # Subjects : liste de {"name": ...} ou de chaînes
    subjects = []
    for s in entry.get("subjects") or []:
        if isinstance(s, dict):
            name = (s.get("name") or "").strip()
        else:
            name = str(s).strip()
        if name:
            subjects.append(name)

    # Cover : entry["cover"] = {"small": URL, "medium": URL, "large": URL}
    cover_url = ""
    cover = entry.get("cover") or {}
    if isinstance(cover, dict):
        cover_url = cover.get("large") or cover.get("medium") or cover.get("small") or ""

    return {
        "isbn_13": isbn if len(isbn) == 13 else "",
        "isbn_10": isbn if len(isbn) == 10 else "",
        "title": entry.get("title", "") or "",
        "subtitle": entry.get("subtitle", "") or "",
        "authors_text": "; ".join(
            a.get("name", "") for a in entry.get("authors", []) if a.get("name")
        ),
        "publisher": ", ".join(
            p.get("name", "") for p in entry.get("publishers", []) if p.get("name")
        ),
        "publication_year": int(year_match.group()) if year_match else None,
        "language": "",
        "summary": summary,
        "subjects": subjects,
        "cover_url": cover_url,
    }


def search(title: str, author: str = "", limit: int = 5) -> list[dict]:
    """Recherche par titre + auteur (FEAT-050, passe 2).

    Retourne jusqu'à ``limit`` candidats normalisés (mêmes clés que ``lookup``,
    au minimum ``title``, ``authors_text``, ``isbn_13``/``isbn_10``). Liste vide
    si rien ou erreur réseau (jamais d'exception).
    """
    title = (title or "").strip()
    if not title:
        return []
    params = {"title": title, "limit": str(max(1, min(limit, 20))), "fields": "*"}
    if (author or "").strip():
        params["author"] = author.strip()
    url = f"{settings.OPENLIBRARY_BASE_URL}/search.json"
    try:
        resp = httpx.get(url, params=params, timeout=settings.OPENLIBRARY_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.info("OpenLibrary search KO « %s » : %s", title, exc)
        return []
    out: list[dict] = []
    for doc in (data.get("docs") or [])[:limit]:
        isbns = [_normalize_isbn(x) for x in (doc.get("isbn") or [])]
        isbn_13 = next((x for x in isbns if len(x) == 13), "")
        isbn_10 = next((x for x in isbns if len(x) == 10), "")
        out.append(
            {
                "isbn_13": isbn_13,
                "isbn_10": isbn_10,
                "title": (doc.get("title") or "").strip(),
                "subtitle": (doc.get("subtitle") or "").strip(),
                "authors_text": "; ".join(doc.get("author_name") or []),
                "publisher": "; ".join((doc.get("publisher") or [])[:1]),
                "publication_year": doc.get("first_publish_year"),
                "language": "",
                "summary": "",
                "subjects": [],
                "cover_url": "",
            }
        )
    return out
