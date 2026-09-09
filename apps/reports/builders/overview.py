"""La vue d'ensemble. FEAT-093.

C'est la page qu'on imprime pour le comité ou pour un bailleur. Elle ne montre
rien qui ne soit détaillé ailleurs : elle rassemble, et chaque chiffre de la
période est accompagné du même chiffre sur la période équivalente précédente —
un total seul ne dit pas si l'année a été bonne.

L'histogramme « prêtés et disponibles » se reconstitue à la volée depuis les
dates de prêt et de retour : aucun historique n'est stocké.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Table
from ..periods import months_between, previous_equivalent


def build(period, params) -> ReportPage:
    from apps.catalog.models import BibliographicRecord, Item, ItemStatus
    from apps.loans.models import Loan, LoanStatus
    from apps.members.models import Member, MemberFamilyMember

    today = date.today()
    previous = previous_equivalent(period)
    now = _snapshot(today)
    current = _period_figures(period)
    before = _period_figures(previous)

    kpis_today = [
        Kpi(_("Livres sortis"), fmt.number(now["on_loan"]),
            _("chez des usagers en ce moment"), "orange"),
        Kpi(_("Livres disponibles"), fmt.number(now["available"]),
            _("sur les rayons aujourd'hui"), "forest"),
        Kpi(_("Livres en retard"), fmt.number(now["overdue"]),
            _("à relancer"), "blush"),
        Kpi(_("Usagers inscrits"), fmt.number(now["members"]),
            _("dont %(n)s familles") % {"n": fmt.number(now["families"])}, "burgundy"),
        Kpi(_("Personnes touchées"), fmt.number(now["people"]),
            _("titulaires et personnes de leur foyer"), "sky"),
        Kpi(_("Livres au catalogue"), fmt.number(now["items"]),
            _("%(n)s titres différents") % {"n": fmt.number(now["records"])}, "olive"),
    ]

    kpis_period = [
        _compare(_("Prêts"), current["loans"], before["loans"], previous.label),
        _compare(_("Nouveaux livres"), current["new_items"], before["new_items"], previous.label),
        _compare(_("Nouveaux usagers"), current["new_members"], before["new_members"],
                 previous.label),
        _compare(_("Présences aux animations"), current["attendance"], before["attendance"],
                 previous.label),
        _compare(_("Heures de travail"), current["hours"], before["hours"], previous.label,
                 decimal=True),
        Kpi(_("Argent encaissé"), fmt.money(current["cashed"]),
            _("%(label)s : %(v)s") % {"label": previous.label,
                                      "v": fmt.money(before["cashed"])}, "forest"),
    ]

    blocks = [
        _loans_chart(period),
        _availability_chart(period),
        _collection_chart(),
        _summary_table(now, current, before, previous, period),
    ]

    return ReportPage(
        slug="overview",
        title=_("Vue d'ensemble"),
        subtitle=_("Les chiffres importants de la bibliothèque, sur une page."),
        kpis=kpis_today + kpis_period,
        blocks=blocks,
        period=period,
        note=_("Les six premiers chiffres décrivent aujourd'hui ; les six suivants, la période choisie."),
    )


def _compare(label: str, value, reference, reference_label: str, decimal: bool = False) -> Kpi:
    """Un compteur de période, avec le même chiffre sur la période d'avant.

    Sans point de comparaison, « 412 prêts » ne dit ni bien ni mal. La couleur
    suit le sens de l'évolution, mais le chiffre précédent reste écrit : une
    flèche seule se lit de travers.
    """
    shown = fmt.ratio(value) if decimal else fmt.number(value)
    former = fmt.ratio(reference) if decimal else fmt.number(reference)
    if reference and value > reference:
        color = "forest"
    elif reference and value < reference:
        color = "orange"
    else:
        color = "burgundy"
    return Kpi(
        label, shown,
        _("%(label)s : %(v)s") % {"label": reference_label, "v": former},
        color,
    )


def _snapshot(today: date) -> dict:
    from apps.catalog.models import BibliographicRecord, Item, ItemStatus
    from apps.loans.models import Loan, LoanStatus
    from apps.members.models import Member, MemberFamilyMember

    items = Item.objects.all()
    return {
        "items": items.count(),
        "records": BibliographicRecord.objects.count(),
        "available": items.filter(status=ItemStatus.AVAILABLE).count(),
        "on_loan": items.filter(status=ItemStatus.ON_LOAN).count(),
        "overdue": Loan.objects.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE], due_date__lt=today
        ).count(),
        "members": Member.objects.count(),
        "families": Member.objects.filter(family__isnull=False).distinct().count(),
        "people": Member.objects.count() + MemberFamilyMember.objects.count(),
    }


def _period_figures(period) -> dict:
    from apps.catalog.models import Item
    from apps.closing.models import ActivityEntry, AnimationAttendance, AnimationSession
    from apps.finance.models import Payment
    from apps.loans.models import Loan
    from apps.members.models import Member

    sessions = AnimationSession.objects.filter(
        occurred_on__gte=period.start, occurred_on__lte=period.end
    )
    non_members = sessions.aggregate(
        n=Sum("non_member_adults") + Sum("non_member_children")
    )["n"] or 0
    minutes = ActivityEntry.objects.filter(
        occurred_on__gte=period.start, occurred_on__lte=period.end
    ).aggregate(n=Sum("minutes"))["n"] or 0

    return {
        "loans": Loan.objects.filter(
            loan_date__date__gte=period.start, loan_date__date__lte=period.end
        ).count(),
        "new_items": Item.objects.filter(
            created_at__date__gte=period.start, created_at__date__lte=period.end
        ).count(),
        "new_members": Member.objects.filter(
            registration_date__gte=period.start, registration_date__lte=period.end
        ).count(),
        "attendance": AnimationAttendance.objects.filter(
            session__in=sessions
        ).count() + non_members,
        "hours": minutes / 60,
        "cashed": Payment.objects.filter(
            paid_on__gte=period.start, paid_on__lte=period.end
        ).aggregate(n=Sum("amount"))["n"] or Decimal("0"),
    }


def _loans_chart(period) -> Chart:
    from apps.loans.models import Loan

    labels, values = [], []
    for start, end, label in months_between(period):
        labels.append(label)
        values.append(
            Loan.objects.filter(
                loan_date__date__gte=start, loan_date__date__lte=end
            ).count()
        )
    return Chart(
        title=_("Les prêts mois par mois"), kind="bar",
        labels=labels, values=values, unit=_("prêts"),
    )


def _availability_chart(period) -> Chart:
    """Combien de livres étaient sortis à la fin de chaque mois.

    Reconstitué depuis `Loan` : un prêt était en cours à une date s'il avait
    commencé avant et n'était pas encore rendu. Aucun instantané n'est stocké,
    ce qui permet de remonter aussi loin que le journal des prêts.
    """
    from apps.loans.models import Loan

    labels, values = [], []
    for _start, end, label in months_between(period):
        labels.append(label)
        values.append(
            Loan.objects.filter(loan_date__date__lte=end)
            .filter(Q(return_date__isnull=True) | Q(return_date__date__gt=end))
            .count()
        )
    return Chart(
        title=_("Les livres sortis à la fin de chaque mois"), kind="bar",
        labels=labels, values=values, unit=_("livres"),
        note=_("Nombre de livres qui n'étaient pas rentrés le dernier jour du mois."),
    )


def _collection_chart() -> Chart:
    from apps.catalog.models import Item
    from django.db.models import Count

    rows = (
        Item.objects.values("record__category__name")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    return Chart(
        title=_("Le fonds par rayon"), kind="pie",
        labels=[row["record__category__name"] or _("Sans rayon") for row in rows],
        values=[row["n"] for row in rows], unit=_("livres"),
    )


def _summary_table(now, current, before, previous, period) -> Table:
    """Le bilan en un tableau — l'équivalent du « Bilan annuel » du logiciel de
    ludothèque, placé en fin d'écran parce que c'est un livrable, pas la lecture
    du matin.

    **Deux colonnes** : la période choisie, et la période de comparaison —
    la même un an plus tôt pour un mois ou une année nommés, le bloc de même
    durée qui précède pour une période libre (cf. `periods.previous_equivalent`).

    Les huit premiers chiffres décrivent **aujourd'hui** : ils ne dépendent
    d'aucune période, et leur colonne de comparaison reste vide plutôt que de
    répéter la même valeur deux fois.

    Pas de graphe ici (demande Val) : quatorze grandeurs hétérogènes — des
    livres, des heures, de l'argent — ne se lisent pas sur un axe commun.
    """
    rows = [
        [_("Livres au catalogue"), fmt.number(now["items"]), ""],
        [_("Titres différents"), fmt.number(now["records"]), ""],
        [_("Livres disponibles"), fmt.number(now["available"]), ""],
        [_("Livres sortis"), fmt.number(now["on_loan"]), ""],
        [_("Livres en retard"), fmt.number(now["overdue"]), ""],
        [_("Usagers inscrits"), fmt.number(now["members"]), ""],
        [_("Familles"), fmt.number(now["families"]), ""],
        [_("Personnes touchées"), fmt.number(now["people"]), ""],
        [_("Prêts"), fmt.number(current["loans"]), fmt.number(before["loans"])],
        [_("Livres entrés"), fmt.number(current["new_items"]),
         fmt.number(before["new_items"])],
        [_("Nouveaux usagers"), fmt.number(current["new_members"]),
         fmt.number(before["new_members"])],
        [_("Présences aux animations"), fmt.number(current["attendance"]),
         fmt.number(before["attendance"])],
        [_("Heures de travail"), fmt.ratio(current["hours"]), fmt.ratio(before["hours"])],
        [_("Argent encaissé"), fmt.money(current["cashed"]), fmt.money(before["cashed"])],
    ]
    return Table(
        title=_("Le bilan en un tableau"),
        columns=[
            Column(_("Ce qu'on compte")),
            Column(period.label, "right"),
            Column(previous.label, "right"),
        ],
        rows=rows,
        note=_(
            "Les huit premières lignes décrivent la situation d'aujourd'hui : elles "
            "ne dépendent pas de la période choisie et n'ont donc rien à comparer. "
            "Les suivantes portent sur la période."
        ),
    )
