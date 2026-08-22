"""FEAT-077 — libellés de fuseau horaire.

Partagé par l'accueil (abréviation affichée à côté de l'heure de la Box) et par
l'écran Paramètres → Fuseau horaire (libellés de la liste déroulante).
"""
from __future__ import annotations

import zoneinfo
from datetime import datetime

from django.utils import timezone


def _now(name: str | None) -> datetime | None:
    """Instant courant dans `name`, ou dans le fuseau actif si `name` est vide."""
    if not name:
        return timezone.localtime(timezone.now())
    try:
        return datetime.now(zoneinfo.ZoneInfo(name))
    except Exception:  # noqa: BLE001 — zone inconnue : l'appelant retombe sur le nom
        return None


def city(name: str) -> str:
    """Dernier segment d'un nom IANA, lisible : `America/Caracas` → `Caracas`."""
    return (name or "").rsplit("/", 1)[-1].replace("_", " ")


def abbreviation(name: str | None = None) -> str:
    """Sigle du fuseau : `CEST`, `IST`… ou le nom de la ville à défaut.

    La base IANA a retiré les sigles littéraux de la plupart des zones
    d'Amérique du Sud : `America/Caracas` renvoie `-04` et non `VET`. Un
    décalage numérique n'apprend rien à un bibliothécaire — on lui montre alors
    la ville, qui est le repère qu'il a choisi dans les Paramètres.
    """
    now = _now(name)
    if now is None:
        return city(name or "")
    abbr = now.tzname() or ""
    if abbr and abbr[0] not in "+-":
        return abbr
    return city(name or str(now.tzinfo))


def utc_offset(name: str | None = None) -> str:
    """Décalage lisible : `UTC+2`, `UTC-4`, `UTC+5:30`."""
    now = _now(name)
    offset = now.utcoffset() if now else None
    total = int(offset.total_seconds()) // 60 if offset else 0
    sign = "-" if total < 0 else "+"
    hours, minutes = divmod(abs(total), 60)
    return f"UTC{sign}{hours}" + (f":{minutes:02d}" if minutes else "")


def zone_label(name: str) -> str:
    """Entrée de la liste déroulante des Paramètres.

    `Europe/Zurich — CEST (UTC+2)` quand le sigle existe ; `America/Caracas
    (UTC-4)` sinon — le nom IANA porte déjà la ville, inutile de la répéter.
    """
    if _now(name) is None:
        return name
    abbr = abbreviation(name)
    shift = utc_offset(name)
    if abbr in {city(name), "UTC"}:
        return f"{name} ({shift})"
    return f"{name} — {abbr} ({shift})"
