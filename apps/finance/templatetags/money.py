"""Filtre `|money` : montant mis en forme dans la devise de l'instance.

FEAT-084. La devise est un réglage par instance (`canaima` en bolívar,
`grand-saconnex` en franc suisse) : aucun gabarit ne doit écrire un symbole
monétaire en dur.
"""
from django import template

from ..money import config, format_amount

register = template.Library()


@register.filter(name="money")
def money(value):
    return format_amount(value)


@register.filter(name="money_plain")
def money_plain(value):
    """Sans le code de devise — pour une colonne de tableau déjà titrée."""
    return format_amount(value, with_currency=False)


@register.simple_tag(name="currency_code")
def currency_code():
    return config()["currency"]
