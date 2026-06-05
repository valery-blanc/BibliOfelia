"""Source BNE — SRU Alma Dublin Core (FEAT-031).

Endpoint BNE Alma (l'ancien `catalogo.bne.es/uhtbin/sru/opac` est obsolète,
remplacé par `catalogo.bne.es/view/sru/34BNE_INST`).
"""
from __future__ import annotations

import logging
import re
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")
_BNE_SRU = (
    "https://catalogo.bne.es/view/sru/34BNE_INST"
    "?version=1.2&operation=searchRetrieve"
    "&recordSchema=dc&maximumRecords=1"
    '&query=alma.isbn="{isbn}"'
)

_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "srw": "http://www.loc.gov/zing/srw/",
}


def _texts(record_data, tag):
    return [
        (el.text or "").strip()
        for el in record_data.findall(f"dc:{tag}", _NS)
        if (el.text or "").strip()
    ]


_BNE_SRU_SEARCH = (
    "https://catalogo.bne.es/view/sru/34BNE_INST"
    "?version=1.2&operation=searchRetrieve"
    "&recordSchema=dc&maximumRecords={limit}"
    '&query=alma.title="{title}"{author_clause}'
)

_ISBN_RE = re.compile(r"[0-9Xx]{10,17}")


def _quote(value: str) -> str:
    return (value or "").replace('"', " ").strip()


def _isbns_from_identifiers(record_data) -> tuple[str, str]:
    isbn_13 = isbn_10 = ""
    for ident in _texts(record_data, "identifier"):
        m = _ISBN_RE.search(re.sub(r"[ \-]", "", ident))
        if not m:
            continue
        val = m.group().upper()
        if len(val) == 13 and not isbn_13:
            isbn_13 = val
        elif len(val) == 10 and not isbn_10:
            isbn_10 = val
    return isbn_13, isbn_10


def _record_to_candidate(record_data) -> dict:
    titles = _texts(record_data, "title")
    creators = _texts(record_data, "creator") + _texts(record_data, "contributor")
    publishers = _texts(record_data, "publisher")
    dates = _texts(record_data, "date")
    languages = _texts(record_data, "language")
    year = None
    for d in dates:
        m = _YEAR_RE.search(d)
        if m:
            year = int(m.group())
            break
    isbn_13, isbn_10 = _isbns_from_identifiers(record_data)
    return {
        "isbn_13": isbn_13,
        "isbn_10": isbn_10,
        "title": titles[0] if titles else "",
        "subtitle": "",
        "authors_text": "; ".join(creators),
        "publisher": publishers[-1] if publishers else "",
        "publication_year": year,
        "language": (languages[0][:10] if languages else ""),
        "summary": "",
        "subjects": [],
        "cover_url": "",
    }


def search(title: str, author: str = "", limit: int = 5) -> list[dict]:
    """Recherche par titre + auteur (FEAT-050, passe 2). SRU Alma Dublin Core."""
    title = _quote(title)
    if not title:
        return []
    author_clause = ""
    if _quote(author):
        author_clause = f'+and+alma.author="{_quote(author)}"'
    url = _BNE_SRU_SEARCH.format(
        title=title, author_clause=author_clause, limit=max(1, min(limit, 20))
    )
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (httpx.HTTPError, ET.ParseError) as exc:
        logger.info("BNE search KO « %s » : %s", title, exc)
        return []
    out: list[dict] = []
    for record_data in root.findall(".//srw:recordData", _NS)[:limit]:
        out.append(_record_to_candidate(record_data))
    return out


def lookup(raw_isbn: str) -> dict | None:
    isbn = re.sub(r"[^0-9Xx]", "", raw_isbn or "").upper()
    if len(isbn) not in (10, 13):
        return None
    url = _BNE_SRU.format(isbn=isbn)
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (httpx.HTTPError, ET.ParseError) as exc:
        logger.info("BNE KO ISBN %s : %s", isbn, exc)
        return None
    num_records = root.find("srw:numberOfRecords", _NS)
    if num_records is None or (num_records.text or "0").strip() == "0":
        return None
    record_data = root.find(".//srw:recordData", _NS)
    if record_data is None:
        return None
    titles = _texts(record_data, "title")
    creators = _texts(record_data, "creator") + _texts(record_data, "contributor")
    publishers = _texts(record_data, "publisher")
    dates = _texts(record_data, "date")
    languages = _texts(record_data, "language")
    descriptions = _texts(record_data, "description")
    subjects = _texts(record_data, "subject")
    year = None
    for d in dates:
        m = _YEAR_RE.search(d)
        if m:
            year = int(m.group())
            break
    return {
        "isbn_13": isbn if len(isbn) == 13 else "",
        "isbn_10": isbn if len(isbn) == 10 else "",
        "title": titles[0] if titles else "",
        "subtitle": "",
        "authors_text": "; ".join(creators),
        "publisher": publishers[-1] if publishers else "",
        "publication_year": year,
        "language": (languages[0][:10] if languages else ""),
        "summary": descriptions[0] if descriptions else "",
        "subjects": subjects,
        "cover_url": "",
    }
