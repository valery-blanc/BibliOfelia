"""Recherche de devises. FEAT-088.

Val (2026-09-01) : « plutôt qu'une liste déroulante, fais un moteur de
recherche qui recherche parmi toutes les devises. Le moteur attend la 2ᵉ lettre.
On pourra donc taper soit une partie ou tout le trigramme, soit une partie ou
tout le nom du pays. »

Les libellés viennent du **CLDR embarqué dans Babel**, pas de nos `.po` :
153 devises × leurs pays × 4 langues resteraient sinon à traduire à la main, et
à maintenir à chaque changement politique. Babel embarque ses données — aucune
requête réseau, la contrainte hors-ligne est respectée.

Ne sont proposées que les devises **effectivement en circulation**
(`tender=True`) : les 306 codes ISO 4217 de Babel comprennent les monnaies
mortes (franc français, mark…), qu'il serait absurde de proposer.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from functools import lru_cache

from django.utils.translation import get_language

DEFAULT_CURRENCY = "CHF"
# Le moteur attend la 2ᵉ lettre (demande Val) : sur un trigramme, une seule
# lettre remonterait la moitié de la liste.
MIN_QUERY_LENGTH = 2
MAX_RESULTS = 30

# Devises des instances existantes, remontées en tête à requête vide.
SUGGESTED = ("CHF", "VES", "EUR", "USD", "ARS", "MGA")


@dataclass(frozen=True)
class Currency:
    code: str
    name: str
    countries: tuple[str, ...]

    @property
    def countries_display(self) -> str:
        return ", ".join(self.countries)

    def as_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "countries": self.countries_display,
        }


def _fold(text: str) -> str:
    """Minuscules sans accents — « pérou » doit se trouver en tapant « perou »."""
    normalized = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in normalized if not unicodedata.combining(c)).lower()


@lru_cache(maxsize=8)
def catalogue(language: str) -> tuple[Currency, ...]:
    """Devises en circulation, libellées dans `language`, triées par nom.

    Mise en cache par langue : la construction parcourt tous les territoires du
    CLDR, ce qui est trop lent pour être refait à chaque frappe.
    """
    from babel import Locale, UnknownLocaleError
    from babel.numbers import get_currency_name, get_territory_currencies

    try:
        locale = Locale.parse(language)
    except (ValueError, UnknownLocaleError, TypeError):
        locale = Locale.parse("en")

    by_code: dict[str, list[str]] = {}
    for territory, territory_name in locale.territories.items():
        # Les territoires du CLDR mêlent pays (« CH ») et zones numériques
        # (« 150 » = Europe) : seuls les premiers ont une devise.
        if len(territory) != 2 or not territory.isalpha():
            continue
        try:
            codes = get_territory_currencies(territory, tender=True)
        except Exception:  # pragma: no cover — territoire sans donnée monétaire
            continue
        for code in codes:
            by_code.setdefault(code, []).append(territory_name)

    result = []
    for code, countries in by_code.items():
        name = get_currency_name(code, locale=locale)
        # Le CLDR n'a pas tous les noms dans toutes les langues (en malgache,
        # `VES` se rend « VES ») : on garde le code plutôt qu'une chaîne vide.
        result.append(
            Currency(code=code, name=name or code, countries=tuple(sorted(countries)))
        )
    result.sort(key=lambda c: (_fold(c.name), c.code))
    return tuple(result)


def search(query: str, language: str | None = None, limit: int = MAX_RESULTS) -> list[Currency]:
    """Devises dont le code, le nom ou un pays correspond à `query`.

    Une requête plus courte que `MIN_QUERY_LENGTH` renvoie les devises
    suggérées plutôt que rien : le champ n'est jamais vide au premier clic.
    """
    language = language or get_language() or "fr"
    items = catalogue(language)
    needle = _fold((query or "").strip())
    if len(needle) < MIN_QUERY_LENGTH:
        index = {c.code: c for c in items}
        return [index[code] for code in SUGGESTED if code in index][:limit]

    exact, prefix, contains = [], [], []
    for currency in items:
        code = currency.code.lower()
        haystack = _fold(currency.name) + " " + _fold(currency.countries_display)
        if code == needle:
            exact.append(currency)
        elif code.startswith(needle) or haystack.startswith(needle):
            prefix.append(currency)
        elif needle in code or needle in haystack:
            contains.append(currency)
    return (exact + prefix + contains)[:limit]


def is_valid(code: str) -> bool:
    """Le code est-il une devise en circulation ? Garde-fou serveur : le champ
    de recherche envoie un code que rien n'empêche de bricoler à la main."""
    code = (code or "").strip().upper()
    return any(c.code == code for c in catalogue("en"))


def describe(code: str, language: str | None = None) -> Currency | None:
    """Devise `code` libellée dans la langue courante, ou None."""
    code = (code or "").strip().upper()
    language = language or get_language() or "fr"
    for currency in catalogue(language):
        if currency.code == code:
            return currency
    return None


def precision(code: str) -> int:
    """Décimales usuelles de la devise (0 pour l'ariary, 2 pour le franc)."""
    from babel.numbers import get_currency_precision

    try:
        return int(get_currency_precision((code or "").strip().upper()))
    except Exception:  # pragma: no cover — code inconnu de Babel
        return 2
