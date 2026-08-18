"""Source Swisscovery / SLSP — SRU Alma Dublin Core (FEAT-060).

Réseau des bibliothèques scientifiques suisses. Seule source qui couvre les
éditeurs suisses (Zoé, éditeurs romands, Helvetiq…) que ni la BnF ni la BNE ne
cataloguent — cas concret : `9782882415417` (Barilier, *Muses*) absent de
OpenLibrary / BnF / BNE, présent ici. Trilingue fr/de/it, sans clé d'API.
"""
from __future__ import annotations

from ._alma_sru import AlmaSruSource

_SLSP = AlmaSruSource(
    "Swisscovery", "https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK"
)


def lookup(raw_isbn: str) -> dict | None:
    return _SLSP.lookup(raw_isbn)


def lookup_issn(raw_issn: str) -> dict | None:
    return _SLSP.lookup_issn(raw_issn)


def search(title: str, author: str = "", limit: int = 5) -> list[dict]:
    return _SLSP.search(title, author, limit)
