"""Sélecteur de période. FEAT-093.

Quatre boutons portant le **libellé réel** de la période — « août 2026 », pas
« mois précédent ». Un bénévole qui lit « août 2026 » sait de quoi on parle ;
« mois précédent » demande un calcul mental et une confiance dans l'horloge de
la machine.

La saisie libre et la période par défaut sont les mêmes : les 12 derniers jours
glissants ne veulent rien dire, les 12 derniers *mois* si.
"""
from __future__ import annotations

from calendar import monthrange
from datetime import date, timedelta

from django.utils import formats
from django.utils.translation import gettext as _

from .pages import Period



def _month_label(day: date) -> str:
    """« août 2026 » — le nom du mois dans la langue de l'utilisateur."""
    return formats.date_format(day, "F Y")


def _month_bounds(day: date) -> tuple[date, date]:
    first = day.replace(day=1)
    return first, first.replace(day=monthrange(day.year, day.month)[1])


def _previous_month(today: date) -> date:
    return today.replace(day=1) - timedelta(days=1)


def default_period(today: date | None = None) -> Period:
    """Les douze mois qui se terminent aujourd'hui, bornes comprises.

    Le début est le lendemain du même jour l'an dernier, et non
    `aujourd'hui − 365 jours` : cette seconde forme donne une fenêtre de **366**
    jours une fois les bornes comptées, et décale d'un jour la période de
    comparaison.
    """
    today = today or date.today()
    return Period(
        start=_same_day_last_year(today) + timedelta(days=1),
        end=today,
        label=_("12 derniers mois"),
        key="custom",
    )


def named_period(key: str, today: date | None = None) -> Period | None:
    """Une des quatre périodes en un clic, ou None si `key` n'en est pas une."""
    today = today or date.today()
    if key == "month":
        start, end = _month_bounds(today)
        return Period(start, end, _month_label(today), "month")
    if key == "prev_month":
        previous = _previous_month(today)
        start, end = _month_bounds(previous)
        return Period(start, end, _month_label(previous), "prev_month")
    if key == "year":
        return Period(date(today.year, 1, 1), date(today.year, 12, 31), str(today.year), "year")
    if key == "prev_year":
        year = today.year - 1
        return Period(date(year, 1, 1), date(year, 12, 31), str(year), "prev_year")
    return None


def shortcuts(today: date | None = None) -> list[Period]:
    """Les quatre boutons, dans l'ordre demandé : mois, année, mois-1, année-1."""
    today = today or date.today()
    return [
        named_period(key, today)
        for key in ("month", "year", "prev_month", "prev_year")
    ]


def custom_label(start: date, end: date) -> str:
    return _("du %(start)s au %(end)s") % {
        "start": formats.date_format(start, "SHORT_DATE_FORMAT"),
        "end": formats.date_format(end, "SHORT_DATE_FORMAT"),
    }


def parse(params, today: date | None = None) -> tuple[Period, str]:
    """Lit la période dans un `request.GET`. Renvoie `(période, avertissement)`.

    Une date illisible ou une fin avant le début ne produit **pas** de page
    d'erreur : on retombe sur les 12 derniers mois avec un message. Un écran de
    rapport qui refuse de s'afficher parce qu'une date est mal tapée est un
    écran qu'on n'ouvre plus.
    """
    today = today or date.today()
    key = (params.get("p") or "").strip()

    named = named_period(key, today)
    if named is not None:
        return named, ""

    if key == "custom" or params.get("start") or params.get("end"):
        start = _parse_date(params.get("start"))
        end = _parse_date(params.get("end"))
        if start is None or end is None:
            return default_period(today), _("Dates incomplètes : voici les 12 derniers mois.")
        if start > end:
            return default_period(today), _(
                "La date de début doit précéder la date de fin : "
                "voici les 12 derniers mois."
            )
        return Period(start, end, custom_label(start, end), "custom"), ""

    return default_period(today), ""


def _parse_date(raw) -> date | None:
    if not raw:
        return None
    try:
        return date.fromisoformat(raw.strip())
    except (ValueError, AttributeError):
        return None


def previous_equivalent(period: Period) -> Period:
    """La période à laquelle comparer celle qu'on regarde. Règle Val (2026-09-09).

    Pour une période **nommée**, c'est la même, un an plus tôt : septembre 2026
    se compare à septembre 2025, et 2026 à 2025. Comparer septembre au mois
    d'août n'aurait rien dit — une bibliothèque ne fait pas le même mois en
    pleine rentrée et en plein été ; d'une année sur l'autre, si.

    Pour une période **libre**, c'est le bloc de même durée qui la précède
    immédiatement : on ne peut pas décaler d'un an une fenêtre dont on ignore
    l'intention. Ce bloc s'arrête la **veille** du début — il ne chevauche pas
    la période regardée, sans quoi une journée serait comptée des deux côtés.

    Val donne l'exemple des 12 derniers mois au 09/09/2026 : du 10/09/2024 au
    09/09/2025. C'est bien ce que rend cette règle.
    """
    if period.key in {"month", "prev_month"}:
        start = _same_day_last_year(period.start)
        first, last = _month_bounds(start)
        return Period(first, last, _month_label(first), "custom")
    if period.key in {"year", "prev_year"}:
        year = period.start.year - 1
        return Period(date(year, 1, 1), date(year, 12, 31), str(year), "custom")
    end = period.start - timedelta(days=1)
    start = end - timedelta(days=period.days - 1)
    return Period(start, end, short_label(start, end), "custom")


def _same_day_last_year(day: date) -> date:
    """Le même jour, un an plus tôt. Le 29 février recule au 28.

    `date.replace(year=…)` lève sur un 29 février d'année bissextile ; un mois
    nommé se compare toujours au même mois, la retombée au 28 ne change donc
    aucun résultat.
    """
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def short_label(start: date, end: date) -> str:
    """« 10/09/24 – 09/09/25 » — le titre d'une période libre de comparaison.

    Plus court que « du … au … » : ce libellé sert d'en-tête de colonne dans le
    bilan, où la place manque.

    Le séparateur est un **tiret demi-cadratin**, pas une flèche : les polices
    du site sont des sous-ensembles Google Fonts, qui couvrent la ponctuation
    générale mais **pas** le bloc des flèches. Une flèche sortirait en carré
    dans le PDF, où reportlab ne sait pas retomber sur une autre police.
    """
    return f"{start.strftime('%d/%m/%y')} – {end.strftime('%d/%m/%y')}"


def months_between(period: Period) -> list[tuple[date, date, str]]:
    """Découpe la période en mois : `[(début, fin, « août 2026 »)]`.

    Sert aux histogrammes mensuels. Une période de plus de trois ans produirait
    trop de barres pour être lue : au-delà, on retourne des années.
    """
    out: list[tuple[date, date, str]] = []
    if period.days > 365 * 3:
        for year in range(period.start.year, period.end.year + 1):
            start = max(period.start, date(year, 1, 1))
            end = min(period.end, date(year, 12, 31))
            out.append((start, end, str(year)))
        return out

    cursor = period.start.replace(day=1)
    while cursor <= period.end:
        first, last = _month_bounds(cursor)
        out.append((max(first, period.start), min(last, period.end), _month_label(cursor)))
        cursor = last + timedelta(days=1)
    return out
