"""Source K10plus — SRU Dublin Core (FEAT-060).

Catalogue collectif des bibliothèques allemandes, autrichiennes et suisses
alémaniques (successeur de GVK/SWB). Sans clé d'API, contrairement à la DNB qui
exige un `accessToken`. Couvre les livres en allemand, absents des autres
sources.

Particularité du DC servi par K10plus : ni `dc:creator` ni `dc:publisher`. Tout
est en `dc:contributor`, suffixé du rôle entre parenthèses :

    <dc:contributor>Wilpert, Bettina , 1989- (VerfasserIn)</dc:contributor>
    <dc:contributor>btb Verlag (TB) (Verlag)</dc:contributor>

On route donc les contributeurs selon leur rôle : `Verlag` → éditeur, le reste
→ auteurs.
"""
from __future__ import annotations

import logging
import re
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

# `opac-de-627` = vue « toutes bibliothèques » du réseau K10plus.
_K10_SRU = "https://sru.k10plus.de/opac-de-627"
_YEAR_RE = re.compile(r"\d{4}")
_ROLE_RE = re.compile(r"\(([^()]+)\)\s*$")
_PUBLISHER_ROLES = {"verlag", "publisher", "hrsg. v.", "druck"}

_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "srw": "http://www.loc.gov/zing/srw/",
}


def _texts(record_data, tag: str) -> list[str]:
    return [
        (el.text or "").strip()
        for el in record_data.findall(f".//dc:{tag}", _NS)
        if (el.text or "").strip()
    ]


def _split_role(raw: str) -> tuple[str, str]:
    """« Nom (VerfasserIn) » → (« Nom », « verfasserin »)."""
    m = _ROLE_RE.search(raw)
    if not m:
        return re.sub(r"\s{2,}", " ", raw).strip(" ,;"), ""
    name = raw[: m.start()].strip()
    return re.sub(r"\s{2,}", " ", name).strip(" ,;"), m.group(1).strip().lower()


def _record_to_candidate(record_data) -> dict:
    titles = _texts(record_data, "title")
    authors: list[str] = []
    publishers: list[str] = []
    for raw in _texts(record_data, "creator") + _texts(record_data, "contributor"):
        name, role = _split_role(raw)
        if not name:
            continue
        (publishers if role in _PUBLISHER_ROLES else authors).append(name)
    publishers += _texts(record_data, "publisher")
    year = None
    for d in _texts(record_data, "date"):
        m = _YEAR_RE.search(d)
        if m:
            year = int(m.group())
            break
    languages = _texts(record_data, "language")
    descriptions = _texts(record_data, "description")
    return {
        "isbn_13": "",
        "isbn_10": "",
        "title": titles[0] if titles else "",
        "subtitle": "",
        "authors_text": "; ".join(authors),
        "publisher": publishers[0] if publishers else "",
        "publication_year": year,
        "language": (languages[0][:10] if languages else ""),
        # dc:description de K10plus = mention de responsabilité (« Bettina
        # Wilpert »), pas un résumé : on ne la remonte pas comme summary.
        "summary": "" if len(descriptions) < 2 else descriptions[-1],
        "subjects": _texts(record_data, "subject"),
        "cover_url": "",
    }


def _query(cql: str, limit: int = 1):
    url = (
        f"{_K10_SRU}?version=1.1&operation=searchRetrieve&recordSchema=dc"
        f"&maximumRecords={max(1, min(limit, 20))}&query={cql}"
    )
    try:
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()
        return ET.fromstring(resp.content)
    except (httpx.HTTPError, ET.ParseError) as exc:
        logger.info("K10plus KO (%s) : %s", cql, exc)
        return None


def lookup(raw_isbn: str) -> dict | None:
    isbn = re.sub(r"[^0-9Xx]", "", raw_isbn or "").upper()
    if len(isbn) not in (10, 13):
        return None
    root = _query(f"pica.isb={isbn}")
    if root is None:
        return None
    num = root.find("srw:numberOfRecords", _NS)
    if num is None or (num.text or "0").strip() == "0":
        return None
    record = root.find(".//srw:recordData", _NS)
    if record is None:
        return None
    data = _record_to_candidate(record)
    data["isbn_13"] = isbn if len(isbn) == 13 else ""
    data["isbn_10"] = isbn if len(isbn) == 10 else ""
    return data


def search(title: str, author: str = "", limit: int = 5) -> list[dict]:
    """Recherche par titre (+ auteur) — FEAT-050 passe 2. Jamais d'exception."""
    title = (title or "").replace('"', " ").strip()
    if not title:
        return []
    cql = f'pica.tit="{title}"'
    author = (author or "").replace('"', " ").strip()
    if author:
        cql += f'+and+pica.per="{author}"'
    root = _query(cql, limit=limit)
    if root is None:
        return []
    return [
        _record_to_candidate(rd)
        for rd in root.findall(".//srw:recordData", _NS)[:limit]
    ]
