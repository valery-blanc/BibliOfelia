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


# Sources interrogées au scan catalogage (FEAT-046), par ordre de préférence :
# la 1re source qui renvoie un titre gagne. Google Books et la BnF couvrent
# beaucoup mieux les livres FR que la seule OpenLibrary.
_MULTI_SOURCE_ORDER = ["openlibrary", "google_books", "bnf", "bne"]


def lookup_isbn_multi(raw_isbn: str) -> dict | None:
    """Lookup ISBN multi-sources pour le scan catalogage.

    Interroge OpenLibrary + Google Books + BnF + BNE **en parallèle** (latence
    bornée par la source la plus lente, pas par leur somme) et renvoie le 1er
    résultat non vide dans l'ordre de préférence. Bien meilleure couverture FR
    que `lookup_isbn` (OpenLibrary seule). Jamais d'exception réseau.
    """
    isbn = normalize_isbn(raw_isbn)
    if len(isbn) not in (10, 13):
        return None

    from concurrent.futures import ThreadPoolExecutor

    from .sources import SOURCES  # {name: lookup(isbn) -> dict | None}

    results: dict[str, dict | None] = {}
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as ex:
        futures = {ex.submit(fn, isbn): name for name, fn in SOURCES.items()}
        for fut, name in futures.items():
            try:
                results[name] = fut.result()
            except Exception as exc:  # filet : une source qui casse ne bloque pas
                logger.info("Source %s en échec pour ISBN %s : %s", name, isbn, exc)
                results[name] = None

    for name in _MULTI_SOURCE_ORDER:
        data = results.get(name)
        if data and data.get("title"):
            return _clean_multi_result(data)
    return None


# FEAT-052 : sources ISSN interrogées au scan d'un périodique (préfixe 977),
# par ordre de préférence. La BnF couvre les revues FR ; la BNE en complément.
_ISSN_SOURCE_ORDER = ["bnf", "bne"]


def lookup_issn_multi(raw_issn: str) -> dict | None:
    """Lookup ISSN multi-sources pour le scan d'un périodique (FEAT-052).

    Miroir de `lookup_isbn_multi` mais sur `ISSN_SOURCES` (bibliothèques
    nationales SRU). Interroge en parallèle, renvoie le 1er résultat avec un
    titre. None si aucune source ne répond → titre saisi à la main. Jamais
    d'exception réseau.
    """
    from apps.core.issn import normalize_issn

    issn = normalize_issn(raw_issn)
    if len(issn) != 8:
        return None

    from concurrent.futures import ThreadPoolExecutor

    from .sources import ISSN_SOURCES  # {name: lookup_issn(issn) -> dict | None}

    results: dict[str, dict | None] = {}
    with ThreadPoolExecutor(max_workers=len(ISSN_SOURCES)) as ex:
        futures = {ex.submit(fn, issn): name for name, fn in ISSN_SOURCES.items()}
        for fut, name in futures.items():
            try:
                results[name] = fut.result()
            except Exception as exc:  # filet : une source qui casse ne bloque pas
                logger.info("Source %s en échec pour ISSN %s : %s", name, issn, exc)
                results[name] = None

    for name in _ISSN_SOURCE_ORDER:
        data = results.get(name)
        if data and data.get("title"):
            return _clean_multi_result(data)
    return None


def _clean_multi_result(data: dict) -> dict:
    """Normalise un résultat de source pour le scan catalogage.

    - Titre des notices SRU (BnF/BNE) : la mention de responsabilité est collée
      au titre par un ` / ` (« Le Bélier / Vincent Villeminot ; ill. … »). On
      coupe au premier ` / ` pour ne garder que le titre propre (l'auteur a son
      propre champ `authors_text`).
    - Garantit les clés attendues par l'appelant (`authors_text`, etc.).
    """
    out = dict(data)
    title = (out.get("title") or "").strip()
    if " / " in title:
        title = title.split(" / ", 1)[0].strip()
    out["title"] = title
    out.setdefault("authors_text", "")
    out.setdefault("publisher", "")
    out.setdefault("publication_year", None)
    return out
