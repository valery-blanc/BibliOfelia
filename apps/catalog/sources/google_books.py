"""Source Google Books (FEAT-031).

Nécessite une clé API Google Books, stockée via
``Setting.get('metadata.google_books_api_key')`` (UI : Paramètres → Sources
de métadonnées). Sans clé : la source renvoie ``None`` silencieusement.
"""
from __future__ import annotations

import logging
import re
import threading
import time

import httpx

from apps.core.models import Setting

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r"\d{4}")
_API_URL = "https://www.googleapis.com/books/v1/volumes"

# --- Quota Google Books -------------------------------------------------
# L'API gratuite est plafonnée (≈100 requêtes/100 s en rafale, ≈1000/jour).
# Pour ne pas perdre des notices au catalogage (BUG-019) SANS ralentir le cas
# normal, le throttle est **adaptatif** :
#   - régime normal (aucun 429 récent) : pleine vitesse, aucun bridage ;
#   - après un 429 : on espace les requêtes d'au moins _MIN_INTERVAL_SLOW s
#     pendant _SLOW_WINDOW s (le temps que la fenêtre rafale Google se libère),
#     puis retour automatique à pleine vitesse.
# En complément : back-off exponentiel sur 429 (respecte `Retry-After`) et levée
# de `SourceRateLimited` si le 429 persiste (≠ « rien trouvé »).
_MIN_INTERVAL_SLOW = 1.2     # espacement en mode lent (après un 429)
_SLOW_WINDOW = 100.0         # durée du mode lent après le dernier 429 (s)
_MAX_RETRIES_429 = 3         # nombre de réessais sur 429 avant abandon
_BACKOFF_CAP = 30.0          # plafond d'attente d'un réessai (s)

_throttle_lock = threading.Lock()
_last_request_at = 0.0
_slowed_until = 0.0          # monotonic() jusqu'auquel on bride (mode lent)


def _note_rate_limited() -> None:
    """Active le mode lent pour ``_SLOW_WINDOW`` s suite à un 429."""
    global _slowed_until
    with _throttle_lock:
        _slowed_until = time.monotonic() + _SLOW_WINDOW


def _throttle() -> None:
    """Pas de bridage en régime normal ; ≥ ``_MIN_INTERVAL_SLOW`` s entre deux
    requêtes tant qu'un 429 a été vu récemment (mode lent adaptatif)."""
    global _last_request_at
    with _throttle_lock:
        now = time.monotonic()
        interval = _MIN_INTERVAL_SLOW if now < _slowed_until else 0.0
        wait = interval - (now - _last_request_at)
        if wait > 0:
            time.sleep(wait)
            now = time.monotonic()
        _last_request_at = now


def _get_json(params: dict) -> dict | None:
    """GET throttlé avec back-off sur 429.

    Renvoie le JSON, ``None`` sur erreur réseau/HTTP non-429, et lève
    ``SourceRateLimited`` si le quota (429) persiste après les réessais.
    """
    from . import SourceRateLimited

    delay = 2.0
    for attempt in range(_MAX_RETRIES_429 + 1):
        _throttle()
        try:
            resp = httpx.get(_API_URL, params=params, timeout=10)
        except httpx.HTTPError as exc:
            logger.info("Google Books réseau KO : %s", exc)
            return None
        if resp.status_code == 429:
            _note_rate_limited()  # passe en mode lent (adaptatif) pour ~100 s
            if attempt >= _MAX_RETRIES_429:
                logger.warning("Google Books : quota atteint (429 persistant).")
                raise SourceRateLimited("google_books")
            retry_after = resp.headers.get("Retry-After", "")
            wait = float(retry_after) if retry_after.isdigit() else delay
            logger.info(
                "Google Books 429 (essai %d/%d), attente %.1fs.",
                attempt + 1, _MAX_RETRIES_429, min(wait, _BACKOFF_CAP),
            )
            time.sleep(min(wait, _BACKOFF_CAP))
            delay *= 2
            continue
        try:
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            logger.info("Google Books KO : %s", exc)
            return None
    return None


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
    data = _get_json(params)  # lève SourceRateLimited si quota 429 persistant
    if not data:
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
    data = _get_json(params)  # lève SourceRateLimited si quota 429 persistant
    if not data:
        return []
    return [_volume_to_candidate(v) for v in (data.get("items") or [])[:limit]]
