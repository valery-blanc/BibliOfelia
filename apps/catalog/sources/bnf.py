"""Source BNF — SRU Dublin Core (FEAT-031)."""
from __future__ import annotations

import logging
import re
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")
_BNF_SRU = (
    "https://catalogue.bnf.fr/api/SRU"
    "?version=1.2&operation=searchRetrieve"
    "&recordSchema=dublincore&maximumRecords=1"
    '&query=bib.isbn+adj+"{isbn}"'
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


def lookup(raw_isbn: str) -> dict | None:
    isbn = re.sub(r"[^0-9Xx]", "", raw_isbn or "").upper()
    if len(isbn) not in (10, 13):
        return None
    url = _BNF_SRU.format(isbn=isbn)
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
    except (httpx.HTTPError, ET.ParseError) as exc:
        logger.info("BNF KO ISBN %s : %s", isbn, exc)
        return None
    num_records = root.find("srw:numberOfRecords", _NS)
    if num_records is None or (num_records.text or "0").strip() == "0":
        return None
    record_data = root.find(".//srw:recordData", _NS)
    if record_data is None:
        return None
    titles = _texts(record_data, "title")
    creators = _texts(record_data, "creator")
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
        "publisher": ", ".join(publishers),
        "publication_year": year,
        "language": (languages[0][:10] if languages else ""),
        "summary": descriptions[0] if descriptions else "",
        "subjects": subjects,
        "cover_url": "",
    }
