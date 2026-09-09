"""La fréquentation et les animations. FEAT-093.

L'animation **« Bibliothèque »** n'est pas une animation comme les autres :
elle enregistre une simple venue à la bibliothèque. C'est l'animation
principale, et l'écran la traite comme telle — en tête, à part.

L'âge d'un participant est calculé **à la date de la séance**, pas aujourd'hui :
un enfant venu à 6 ans il y a trois ans doit rester dans la tranche 6-10 du
rapport de cette année-là, sinon réimprimer un vieux rapport le change de
colonne.
"""
from __future__ import annotations

from django.db.models import Count, Sum
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Table
from ..periods import months_between

# Le libellé qui désigne la simple venue à la bibliothèque. Comparé sans tenir
# compte de la casse, comme `AnimationType.get_or_create_by_label`.
LIBRARY_VISIT_LABEL = "Bibliothèque"


def build(period, params) -> ReportPage:
    from apps.closing.models import AnimationAttendance, AnimationSession
    from apps.loans.models import InHouseConsultation

    sessions = AnimationSession.objects.filter(
        occurred_on__gte=period.start, occurred_on__lte=period.end
    ).select_related("animation_type")

    visits = sessions.filter(animation_type__label__iexact=LIBRARY_VISIT_LABEL)
    others = sessions.exclude(animation_type__label__iexact=LIBRARY_VISIT_LABEL)

    attendances = AnimationAttendance.objects.filter(session__in=sessions).select_related(
        "session", "session__animation_type", "member"
    )
    totals = sessions.aggregate(
        minutes=Sum("minutes"),
        adults=Sum("non_member_adults"),
        children=Sum("non_member_children"),
    )
    consultations = InHouseConsultation.objects.filter(
        date__gte=period.start, date__lte=period.end
    ).aggregate(n=Sum("count"))["n"] or 0

    visit_members = AnimationAttendance.objects.filter(session__in=visits).count()
    visit_non_members = visits.aggregate(
        n=Sum("non_member_adults") + Sum("non_member_children")
    )["n"] or 0

    kpis = [
        Kpi(_("Venues à la bibliothèque"), fmt.number(visit_members + visit_non_members),
            _("présences enregistrées, membres et non-membres"), "burgundy"),
        Kpi(_("Animations organisées"), fmt.number(others.count()),
            _("hors simple venue"), "orange"),
        Kpi(_("Participations d'usagers"), fmt.number(attendances.count()),
            _("toutes séances confondues"), "forest"),
        Kpi(_("Non-membres adultes"), fmt.number(totals["adults"] or 0),
            _("venus sans être inscrits"), "sky"),
        Kpi(_("Non-membres enfants"), fmt.number(totals["children"] or 0),
            _("venus sans être inscrits"), "amber"),
        Kpi(_("Heures d'animation"), fmt.ratio((totals["minutes"] or 0) / 60),
            _("temps d'accueil et d'atelier"), "olive"),
        Kpi(_("Consultations sur place"), fmt.number(consultations),
            _("livres lus sans être empruntés"), "blush"),
    ]

    # Chaque tableau porte le graphe de ses propres chiffres (retour Val) : le
    # camembert des âges accompagne le tableau croisé qui les détaille, plutôt
    # que de flotter seul en tête d'écran et de répéter la même information.
    blocks = [
        _monthly_chart(period),
        _by_animation(sessions),
        _age_by_animation(sessions, attendances),
    ]

    return ReportPage(
        slug="attendance",
        title=_("La fréquentation"),
        subtitle=_("Qui vient à la bibliothèque et aux animations, et de quel âge."),
        kpis=kpis,
        blocks=blocks,
        period=period,
        note=_(
            "« %(label)s » enregistre une simple venue à la bibliothèque : c'est "
            "l'animation principale, comptée à part des ateliers."
        ) % {"label": LIBRARY_VISIT_LABEL},
    )


def _brackets(attendances) -> dict[str, int]:
    buckets = {label: 0 for label in fmt.bracket_labels()}
    for attendance in attendances:
        age = fmt.age_on(attendance.member.birth_date, attendance.session.occurred_on)
        buckets[fmt.age_bracket(age)] += 1
    return buckets


def _age_chart(attendances) -> Chart:
    buckets = _brackets(attendances)
    labels = [label for label in fmt.bracket_labels() if buckets[label]]
    return Chart(
        title=_("L'âge des personnes présentes"), kind="pie",
        labels=labels, values=[buckets[label] for label in labels],
        unit=_("présences"),
        note=_("Seuls les usagers inscrits ont un âge connu ; les non-membres sont comptés à part."),
    )


def _monthly_chart(period) -> Chart:
    from apps.closing.models import AnimationAttendance, AnimationSession

    labels, values = [], []
    for start, end, label in months_between(period):
        sessions = AnimationSession.objects.filter(
            occurred_on__gte=start, occurred_on__lte=end
        )
        members = AnimationAttendance.objects.filter(session__in=sessions).count()
        non_members = sessions.aggregate(
            n=Sum("non_member_adults") + Sum("non_member_children")
        )["n"] or 0
        labels.append(label)
        values.append(members + non_members)
    return Chart(
        title=_("La fréquentation mois par mois"), kind="bar",
        labels=labels, values=values, unit=_("présences"),
    )


def _by_animation(sessions) -> Table:
    # `Count("attendances")` dans le même `annotate` que `Sum("minutes")`
    # multiplierait les minutes par le nombre de présents : la jointure sur les
    # présences duplique la ligne de la séance. Deux requêtes, recollées ici.
    from apps.closing.models import AnimationAttendance

    members_by_label = dict(
        AnimationAttendance.objects.filter(session__in=sessions)
        .values_list("session__animation_type__label")
        .annotate(n=Count("id"))
        .values_list("session__animation_type__label", "n")
    )
    rows_qs = (
        sessions.values("animation_type__label")
        .annotate(
            n=Count("id"),
            minutes=Sum("minutes"),
            adults=Sum("non_member_adults"),
            children=Sum("non_member_children"),
        )
        .order_by("-n")
    )
    rows_qs = list(rows_qs)
    rows, totals, chart_values = [], [0, 0, 0, 0, 0], []
    for row in rows_qs:
        members = members_by_label.get(row["animation_type__label"], 0)
        adults = row["adults"] or 0
        children = row["children"] or 0
        hours = (row["minutes"] or 0) / 60
        rows.append([
            row["animation_type__label"],
            fmt.number(row["n"]),
            fmt.number(members),
            fmt.number(adults + children),
            fmt.ratio(hours),
        ])
        totals[0] += row["n"]
        totals[1] += members
        totals[2] += adults + children
        totals[3] += hours
        chart_values.append(members + adults + children)
    chart = Chart(
        # Ce que le camembert partage : le monde vu ce jour-là, membres et
        # non-membres réunis — pas le nombre de séances, qui ne dit rien de
        # la fréquentation.
        title=_("Les présences par animation"), kind="pie",
        labels=[row[0] for row in rows],
        values=chart_values,
        unit=_("présences"),
    )
    return Table(
        title=_("Ce qui a été organisé"),
        columns=[
            Column(_("Animation")), Column(_("Séances"), "right"),
            Column(_("Usagers présents"), "right"), Column(_("Non-membres"), "right"),
            Column(_("Heures"), "right"),
        ],
        rows=rows,
        total_row=[
            _("Total"), fmt.number(totals[0]), fmt.number(totals[1]),
            fmt.number(totals[2]), fmt.ratio(totals[3]),
        ] if rows else None,
        empty_text=_("Aucune séance sur cette période."),
        chart=chart,
    )


def _age_by_animation(sessions, attendances) -> Table:
    """Le tableau croisé demandé par Val : présences par tranche d'âge et par
    animation. Les non-membres n'ont pas de date de naissance : le modèle ne les
    connaît qu'en « adultes » et « enfants », d'où deux colonnes séparées."""
    brackets = fmt.bracket_labels()
    grid: dict[str, dict[str, int]] = {}
    for attendance in attendances:
        label = attendance.session.animation_type.label
        age = fmt.age_on(attendance.member.birth_date, attendance.session.occurred_on)
        grid.setdefault(label, {b: 0 for b in brackets})[fmt.age_bracket(age)] += 1

    non_members = {
        row["animation_type__label"]: (row["adults"] or 0, row["children"] or 0)
        for row in sessions.values("animation_type__label").annotate(
            adults=Sum("non_member_adults"), children=Sum("non_member_children")
        )
    }

    rows = []
    for label in sorted(set(grid) | set(non_members)):
        counts = grid.get(label, {b: 0 for b in brackets})
        adults, children = non_members.get(label, (0, 0))
        rows.append(
            [label]
            + [fmt.number(counts[b]) for b in brackets]
            + [fmt.number(adults), fmt.number(children)]
        )

    return Table(
        title=_("Les présences par âge et par animation"),
        columns=(
            [Column(_("Animation"))]
            + [Column(bracket, "right") for bracket in brackets]
            + [Column(_("Non-membres adultes"), "right"),
               Column(_("Non-membres enfants"), "right")]
        ),
        rows=rows,
        empty_text=_("Aucune présence enregistrée sur cette période."),
        note=_("L'âge est celui de la personne le jour de la séance."),
        chart=_age_chart(attendances),
    )
