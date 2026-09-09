"""Le travail de l'équipe. FEAT-093.

Les trois états du logiciel de ludothèque, dans l'ordre où on les consulte :
par nature de travail, par personne, puis le détail mois par mois.

Les heures sont données **en heures**, jamais valorisées en argent. Une
valorisation du bénévolat au tarif horaire suisse appliquée à une bibliothèque
malgache produit un chiffre qui ne veut rien dire localement et qu'un bailleur
peut lire de travers.
"""
from __future__ import annotations

from django.db.models import Count, Sum
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Table
from ..periods import months_between


def _hours(minutes) -> float:
    return (minutes or 0) / 60


def _person(user) -> str:
    full = f"{user.first_name} {user.last_name}".strip()
    return full or user.get_username()


def build(period, params) -> ReportPage:
    from apps.closing.models import ActivityEntry, AnimationSession

    entries = ActivityEntry.objects.filter(
        occurred_on__gte=period.start, occurred_on__lte=period.end
    ).select_related("user", "activity_type")

    total_minutes = entries.aggregate(n=Sum("minutes"))["n"] or 0
    people = entries.values("user_id").distinct().count()
    animation_minutes = AnimationSession.objects.filter(
        occurred_on__gte=period.start, occurred_on__lte=period.end
    ).aggregate(n=Sum("minutes"))["n"] or 0

    kpis = [
        Kpi(_("Heures de travail"), fmt.ratio(_hours(total_minutes)),
            _("saisies sur la période"), "burgundy"),
        Kpi(_("Personnes"), fmt.number(people),
            _("ont travaillé sur la période"), "forest"),
        Kpi(_("Heures d'animation"), fmt.ratio(_hours(animation_minutes)),
            _("comptées séparément des activités"), "orange"),
        Kpi(_("Saisies"), fmt.number(entries.count()),
            _("lignes de temps enregistrées"), "sky"),
    ]

    blocks = [
        # « Les heures par nature » et « Le temps par nature » disaient la même
        # chose deux fois, l'une en barres l'autre en tableau. Un seul
        # sous-rapport, tableau et camembert côte à côte (retour Val).
        _by_kind(entries, total_minutes),
        _by_person(entries, total_minutes),
        _monthly_chart(period),
        _detail(entries),
    ]

    return ReportPage(
        slug="team",
        title=_("Le travail de l'équipe"),
        subtitle=_("Le temps donné à la bibliothèque, par nature de travail et par personne."),
        kpis=kpis,
        blocks=blocks,
        period=period,
    )


def _by_kind(entries, total_minutes: int) -> Table:
    """Le temps par nature de travail : tableau et camembert des mêmes chiffres.

    Camembert plutôt que barres (retour Val) : la question posée ici est « à
    quoi passe-t-on le temps ? », c'est-à-dire un partage d'un tout — ce que des
    barres ne montrent pas.
    """
    rows_qs = list(
        entries.values("activity_type__label")
        .annotate(n=Count("id"), minutes=Sum("minutes"))
        .order_by("-minutes")
    )
    rows = [
        [
            row["activity_type__label"],
            fmt.number(row["n"]),
            fmt.ratio(_hours(row["minutes"])),
            fmt.percent(row["minutes"] or 0, total_minutes),
        ]
        for row in rows_qs
    ]
    chart = Chart(
        title=_("Le temps par nature de travail"), kind="pie",
        labels=[row["activity_type__label"] for row in rows_qs],
        values=[round(_hours(row["minutes"]), 1) for row in rows_qs],
        unit=_("heures"),
    )
    return Table(
        title=_("Le temps par nature de travail"),
        columns=[
            Column(_("Nature du travail")), Column(_("Saisies"), "right"),
            Column(_("Heures"), "right"), Column(_("Part"), "right"),
        ],
        rows=rows,
        total_row=[_("Total"), "", fmt.ratio(_hours(total_minutes)), "100 %"] if rows else None,
        empty_text=_("Aucun temps de travail saisi sur cette période."),
        chart=chart,
    )


def _monthly_chart(period) -> Chart:
    from apps.closing.models import ActivityEntry

    labels, values = [], []
    for start, end, label in months_between(period):
        minutes = ActivityEntry.objects.filter(
            occurred_on__gte=start, occurred_on__lte=end
        ).aggregate(n=Sum("minutes"))["n"] or 0
        labels.append(label)
        values.append(round(_hours(minutes), 1))
    return Chart(
        title=_("Les heures mois par mois"), kind="bar",
        labels=labels, values=values, unit=_("heures"),
    )


def _by_person(entries, total_minutes: int) -> Table:
    rows_qs = (
        entries.values("user__first_name", "user__last_name", "user__username")
        .annotate(minutes=Sum("minutes"), n=Count("id"))
        .order_by("-minutes")
    )
    rows = []
    for row in rows_qs:
        name = f"{row['user__first_name']} {row['user__last_name']}".strip()
        rows.append([
            name or row["user__username"],
            fmt.number(row["n"]),
            fmt.ratio(_hours(row["minutes"])),
            fmt.percent(row["minutes"] or 0, total_minutes),
        ])
    return Table(
        title=_("Le temps par personne"),
        columns=[
            Column(_("Personne")), Column(_("Saisies"), "right"),
            Column(_("Heures"), "right"), Column(_("Part"), "right"),
        ],
        rows=rows,
        total_row=[_("Total"), "", fmt.ratio(_hours(total_minutes)), "100 %"] if rows else None,
        empty_text=_("Aucun temps de travail saisi sur cette période."),
    )


def _detail(entries) -> Table:
    """Le détail par mois, personne et nature — l'équivalent du « Détail des
    présences par postes » du logiciel de ludothèque."""
    from django.db.models.functions import TruncMonth

    rows_qs = (
        entries.annotate(month=TruncMonth("occurred_on"))
        .values("month", "user__first_name", "user__last_name", "user__username",
                "activity_type__label")
        .annotate(minutes=Sum("minutes"))
        .order_by("month", "user__last_name", "activity_type__label")
    )
    rows = []
    for row in rows_qs:
        name = f"{row['user__first_name']} {row['user__last_name']}".strip()
        month = row["month"]
        rows.append([
            _month_label(month) if month else "—",
            name or row["user__username"],
            row["activity_type__label"],
            fmt.ratio(_hours(row["minutes"])),
        ])
    return Table(
        title=_("Le détail mois par mois"),
        columns=[
            Column(_("Mois")), Column(_("Personne")),
            Column(_("Nature du travail")), Column(_("Heures"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucun temps de travail saisi sur cette période."),
    )


def _month_label(value) -> str:
    from django.utils import formats

    return formats.date_format(value, "F Y")
