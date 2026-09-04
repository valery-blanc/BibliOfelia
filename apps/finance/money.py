"""Devise et mise en forme des montants. FEAT-084, FEAT-088.

La devise est un **réglage par instance** (décision Val, 2026-08-31) : la Box
`canaima` facture en bolívar, `grand-saconnex` en franc suisse. Elle se règle
au même endroit que le fuseau horaire, dans `/admin/settings/`, et se choisit
depuis le **moteur de recherche** de `currencies.py` (FEAT-088) — toutes les
devises en circulation, par trigramme ou par nom de pays.

Le **stockage** garde toujours deux décimales (`DecimalField`) quelle que soit
la devise : c'est l'affichage qui arrondit. Passer une instance de MGA à EUR ne
doit pas détruire des centimes déjà saisis.
"""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from .currencies import DEFAULT_CURRENCY, precision

DEFAULT_PAYMENT_TERMS_DAYS = 30
SETTING_KEY = "finance_config"


def config() -> dict:
    """Réglages de caisse, complétés par leurs valeurs par défaut."""
    from apps.core.models import Setting

    data = Setting.get(SETTING_KEY, {}) or {}
    currency = data.get("currency") or DEFAULT_CURRENCY
    decimals = data.get("decimals")
    if decimals is None:
        decimals = precision(currency)
    return {
        "currency": currency,
        "decimals": int(decimals),
        "payment_terms_days": int(
            data.get("payment_terms_days") or DEFAULT_PAYMENT_TERMS_DAYS
        ),
    }


def format_amount(amount, with_currency: bool = True) -> str:
    """« 12.50 CHF » / « 1250 VES », selon le réglage de l'instance."""
    cfg = config()
    if amount is None:
        amount = Decimal("0")
    quantum = Decimal(1).scaleb(-cfg["decimals"])
    value = Decimal(amount).quantize(quantum, rounding=ROUND_HALF_UP)
    # Séparateur de milliers : espace fine insécable (U+202F). Une espace
    # ordinaire laisserait « 1 200 » se couper en fin de ligne, et la virgule
    # anglo-saxonne se lirait comme une décimale en français et en espagnol.
    text = f"{value:,.{cfg['decimals']}f}".replace(",", " ")
    return f"{text} {cfg['currency']}" if with_currency else text
