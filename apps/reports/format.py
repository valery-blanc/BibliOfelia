"""Mise en forme des chiffres d'un rapport. FEAT-093.

Un rapport lu par des bénévoles peu à l'aise avec l'informatique n'a pas le
droit d'écrire `1234.0`, `12.7 %` ou une case vide. Tout passe par ici, pour
que l'écran, le PDF et le fichier Excel disent le nombre de la même façon.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.utils import formats
from django.utils.translation import gettext as _

# Espace fine insécable, comme dans `apps/finance/money.py` : une espace
# ordinaire laisserait « 1 200 » se couper en fin de ligne.
THIN_SPACE = " "

# Tranches d'âge reprises du logiciel de ludothèque, qui sont aussi celles dont
# parlent les bailleurs (petite enfance, primaire, adolescence, adultes).
AGE_BRACKETS = [
    (0, 5, "0-5"),
    (6, 10, "6-10"),
    (11, 15, "11-15"),
    (16, 20, "16-20"),
    (21, 200, "21+"),
]


def number(value) -> str:
    """`1 234`, `12,5` — jamais `1234.0`."""
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        value = float(value)
    if isinstance(value, float) and value != int(value):
        text = f"{value:,.1f}".replace(",", THIN_SPACE).replace(".", ",")
        return text
    return f"{int(value):,}".replace(",", THIN_SPACE)


def percent(part, whole) -> str:
    """`38 %` — sans décimale : un pourcentage à la virgule près fait croire à
    une précision que des effectifs de bibliothèque associative n'ont pas."""
    if not whole:
        return "—"
    return f"{round(part / whole * 100)}{THIN_SPACE}%"


def ratio(value) -> str:
    """`1,4` — une rotation, un taux par exemplaire."""
    if value is None:
        return "—"
    return f"{value:.1f}".replace(".", ",")


def days(value) -> str:
    if value is None:
        return "—"
    count = int(round(value))
    return _("%(n)s jours") % {"n": number(count)} if count != 1 else _("1 jour")


def money(amount) -> str:
    from apps.finance.money import format_amount

    return format_amount(amount)


def day(value: date | None) -> str:
    """`09/09/2026`, dans le format de la langue de l'utilisateur."""
    if value is None:
        return "—"
    return formats.date_format(value, "SHORT_DATE_FORMAT")


def blank(text) -> str:
    """Une case jamais vide : `—` se lit, une case blanche fait douter."""
    value = (text or "").strip() if isinstance(text, str) else text
    return value if value else "—"


def age_bracket(age: int | None) -> str:
    """Le libellé de tranche d'un âge, ou « âge inconnu »."""
    if age is None:
        return _("âge inconnu")
    for low, high, label in AGE_BRACKETS:
        if low <= age <= high:
            return label
    return _("âge inconnu")


def bracket_labels() -> list[str]:
    """Les tranches dans l'ordre, « âge inconnu » à la fin."""
    return [label for _low, _high, label in AGE_BRACKETS] + [_("âge inconnu")]


def age_on(birth_date: date | None, reference: date) -> int | None:
    """Âge révolu à la date `reference` — pas aujourd'hui.

    Un enfant venu à 6 ans il y a trois ans doit rester dans la tranche 6-10 du
    rapport de cette année-là ; calculer son âge d'aujourd'hui réécrirait
    l'histoire à chaque réimpression.
    """
    if not birth_date:
        return None
    return (
        reference.year
        - birth_date.year
        - ((reference.month, reference.day) < (birth_date.month, birth_date.day))
    )
