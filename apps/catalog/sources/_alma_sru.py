"""Client SRU Dublin Core générique pour les catalogues Alma (Ex Libris).

Plusieurs bibliothèques que nous interrogeons tournent sur Alma et exposent
exactement le même contrat SRU : `<base>?version=1.2&operation=searchRetrieve
&recordSchema=dc&query=alma.<index>="<valeur>"`. C'est le cas de la BNE
(FEAT-031) et de Swisscovery/SLSP (FEAT-060). Ce module porte le parsing une
seule fois ; chaque source ne déclare que son URL de base et son nom.

Structure de réponse (identique BNE / Swisscovery) :

    <searchRetrieveResponse>
      <numberOfRecords>1</numberOfRecords>
      <records><record><recordData>
        <srw_dc:dc><dc:title>…</dc:title>…</srw_dc:dc>
      </recordData></record></records>

BUG-022 : les champs `dc:*` sont **imbriqués** sous `srw_dc:dc`, donc les
recherches doivent être en descendant (`.//dc:title`) et pas en enfant direct.
"""
from __future__ import annotations

import logging
import re
from xml.etree import ElementTree as ET

import httpx

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")
_ISBN_RE = re.compile(r"[0-9Xx]{10,17}")

_NS = {
    "dc": "http://purl.org/dc/elements/1.1/",
    "srw": "http://www.loc.gov/zing/srw/",
}

# Bruit des zones auteur MARC exportées en Dublin Core par Alma :
# « 880-01 Barilier, Étienne 1947-.... (IDREF)026705370 aut »
_LINK_PREFIX_RE = re.compile(r"^\d{3}-\d{2}\s+")
_AUTHORITY_RE = re.compile(r"\((?:IDREF|BNE|SUDOC|VIAF|ISNI)\)[0-9Xx]+")
_ROLE_SUFFIX_RE = re.compile(
    r"\s+(?:aut|edt|trl|ill|com|ctb|pbl|art|nrt|prf|ths|dgs)\.?$", re.IGNORECASE
)


def _texts(record_data, tag: str) -> list[str]:
    """Textes non vides des `dc:<tag>` **descendants** de `record_data`."""
    return [
        (el.text or "").strip()
        for el in record_data.findall(f".//dc:{tag}", _NS)
        if (el.text or "").strip()
    ]


def clean_contributor(raw: str) -> str:
    """Nettoie une zone auteur Alma : préfixe de liaison, autorité, code de rôle."""
    value = _LINK_PREFIX_RE.sub("", raw or "")
    value = _AUTHORITY_RE.sub("", value)
    value = _ROLE_SUFFIX_RE.sub("", value.strip())
    return re.sub(r"\s{2,}", " ", value).strip(" ,;")


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


def record_to_candidate(record_data) -> dict:
    """Normalise un `recordData` Alma en dict de source (schéma commun)."""
    titles = _texts(record_data, "title")
    contributors = _texts(record_data, "creator") + _texts(record_data, "contributor")
    authors = [c for c in (clean_contributor(x) for x in contributors) if c]
    publishers = _texts(record_data, "publisher")
    descriptions = _texts(record_data, "description")
    languages = _texts(record_data, "language")
    year = None
    for d in _texts(record_data, "date"):
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
        "authors_text": "; ".join(authors),
        # Alma répète dc:publisher (lieu puis éditeur) : le dernier est l'éditeur.
        "publisher": publishers[-1] if publishers else "",
        "publication_year": year,
        "language": (languages[0][:10] if languages else ""),
        "summary": descriptions[0] if descriptions else "",
        "subjects": _texts(record_data, "subject"),
        "cover_url": "",
    }


def _quote(value: str) -> str:
    return (value or "").replace('"', " ").strip()


class AlmaSruSource:
    """Source de métadonnées adossée à un catalogue Alma.

    `base_url` = endpoint SRU complet de l'institution, p. ex.
    ``https://catalogo.bne.es/view/sru/34BNE_INST``.
    """

    def __init__(self, name: str, base_url: str, timeout: int = 10):
        self.name = name
        self.base_url = base_url
        self.timeout = timeout

    # -- HTTP ----------------------------------------------------------
    def _query(self, cql: str, limit: int = 1):
        url = (
            f"{self.base_url}?version=1.2&operation=searchRetrieve"
            f"&recordSchema=dc&maximumRecords={max(1, min(limit, 20))}&query={cql}"
        )
        try:
            resp = httpx.get(url, timeout=self.timeout)
            resp.raise_for_status()
            return ET.fromstring(resp.content)
        except (httpx.HTTPError, ET.ParseError) as exc:
            logger.info("%s KO (%s) : %s", self.name, cql, exc)
            return None

    def _first_record(self, cql: str):
        root = self._query(cql)
        if root is None:
            return None
        num = root.find("srw:numberOfRecords", _NS)
        if num is None or (num.text or "0").strip() == "0":
            return None
        return root.find(".//srw:recordData", _NS)

    # -- API des sources ----------------------------------------------
    def lookup(self, raw_isbn: str) -> dict | None:
        isbn = re.sub(r"[^0-9Xx]", "", raw_isbn or "").upper()
        if len(isbn) not in (10, 13):
            return None
        record = self._first_record(f'alma.isbn="{isbn}"')
        if record is None:
            return None
        data = record_to_candidate(record)
        data["isbn_13"] = isbn if len(isbn) == 13 else data["isbn_13"]
        data["isbn_10"] = isbn if len(isbn) == 10 else data["isbn_10"]
        return data

    def lookup_issn(self, raw_issn: str) -> dict | None:
        """Périodique par ISSN (FEAT-052). Alma indexe l'ISSN avec tiret."""
        issn = re.sub(r"[^0-9Xx]", "", raw_issn or "").upper()
        if len(issn) != 8:
            return None
        record = self._first_record(f'alma.issn="{issn[:4]}-{issn[4:]}"')
        if record is None:
            return None
        return record_to_candidate(record)

    def search(self, title: str, author: str = "", limit: int = 5) -> list[dict]:
        """Recherche titre + auteur (FEAT-050, passe 2). Jamais d'exception."""
        title = _quote(title)
        if not title:
            return []
        cql = f'alma.title="{title}"'
        if _quote(author):
            cql += f'+and+alma.author="{_quote(author)}"'
        root = self._query(cql, limit=limit)
        if root is None:
            return []
        return [
            record_to_candidate(rd)
            for rd in root.findall(".//srw:recordData", _NS)[:limit]
        ]
