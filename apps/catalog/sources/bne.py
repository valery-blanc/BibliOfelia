"""Source BNE — SRU Alma Dublin Core (FEAT-031).

Endpoint BNE Alma (l'ancien `catalogo.bne.es/uhtbin/sru/opac` est obsolète,
remplacé par `catalogo.bne.es/view/sru/34BNE_INST`).

BUG-022 : le parsing (imbrication `srw_dc:dc`) est porté par `_alma_sru`, commun
avec Swisscovery — les deux catalogues tournent sur Alma et répondent à
l'identique.
"""
from __future__ import annotations

from ._alma_sru import AlmaSruSource

_BNE = AlmaSruSource("BNE", "https://catalogo.bne.es/view/sru/34BNE_INST")


def lookup(raw_isbn: str) -> dict | None:
    return _BNE.lookup(raw_isbn)


def lookup_issn(raw_issn: str) -> dict | None:
    """Recherche un périodique par ISSN via SRU Alma (FEAT-052). None sinon."""
    return _BNE.lookup_issn(raw_issn)


def search(title: str, author: str = "", limit: int = 5) -> list[dict]:
    """Recherche par titre + auteur (FEAT-050, passe 2). SRU Alma Dublin Core."""
    return _BNE.search(title, author, limit)
