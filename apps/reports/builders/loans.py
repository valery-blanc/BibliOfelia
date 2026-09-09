"""Les prêts. FEAT-093.

Contient les deux classements demandés par Val : les livres les plus empruntés
et **les moins empruntés**. Les seconds sont pris parmi ceux qui sont sortis au
moins une fois : sans cette restriction, « les moins empruntés » n'est qu'une
liste de zéros tirée au hasard dans le fonds, et la vraie question — les livres
qui ne sortent jamais — est déjà traitée par « Le fonds » et « Les inactifs ».
"""
from __future__ import annotations

from datetime import date
from statistics import median

from django.db.models import Count
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Table
from ..periods import months_between

TOP_SIZE = 20


def build(period, params) -> ReportPage:
    from apps.catalog.models import Category
    from apps.loans.models import Loan, LoanStatus

    category = (params.get("category") or "").strip()

    period_loans = Loan.objects.filter(
        loan_date__date__gte=period.start, loan_date__date__lte=period.end
    )
    if category:
        period_loans = period_loans.filter(item__record__category__code=category)

    total = period_loans.count()
    returned = period_loans.filter(return_date__isnull=False).count()
    renewals = sum(period_loans.values_list("renewal_count", flat=True))
    today = date.today()
    overdue_now = Loan.objects.filter(
        status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE], due_date__lt=today
    ).count()

    late_count, durations = _returned_stats(period_loans)

    kpis = [
        Kpi(_("Prêts"), fmt.number(total), _("pendant la période"), "burgundy"),
        Kpi(_("Retours"), fmt.number(returned), _("livres déjà rendus"), "forest"),
        Kpi(_("En retard aujourd'hui"), fmt.number(overdue_now),
            _("à relancer"), "orange"),
        Kpi(_("Rendus en retard"), fmt.percent(late_count, returned),
            _("des livres rendus, sur la période"), "blush"),
        Kpi(_("Durée d'un prêt"),
            fmt.days(median(durations)) if durations else "—",
            _("la moitié des prêts durent moins que cela"), "sky"),
        Kpi(_("Renouvellements"), fmt.number(renewals),
            _("prolongations accordées"), "olive"),
    ]

    blocks = [
        _monthly_chart(period, category),
        _by_book_category(period_loans),
        _by_member_category(period_loans),
        _top_books(period_loans, most=True),
        _top_books(period_loans, most=False),
        _never_loaned(category),
        _reservations(period),
        _by_open_day(period_loans, period),
        # Les données brutes, devenues sous-rapports de cet écran (demande Val).
        _active_detail(),
        _period_detail(period_loans),
    ]

    page = ReportPage(
        slug="loans",
        title=_("Les prêts"),
        subtitle=_("Combien de livres sont sortis, lesquels, et par qui."),
        kpis=kpis,
        blocks=[b for b in blocks if b is not None],
        period=period,
    )
    page.filters = {
        "category": category,
        "categories": list(Category.objects.order_by("code")),
    }
    return page


def _returned_stats(period_loans) -> tuple[int, list[int]]:
    """Nombre de retours en retard et durées de prêt, en une seule lecture.

    On préfère la **médiane** à la moyenne (revue Grok) : un seul livre rendu
    au bout de deux ans écrase une moyenne calculée sur trois cents prêts de
    trois semaines, et le chiffre affiché ne décrit alors plus aucun prêt réel.
    """
    late, durations = 0, []
    rows = period_loans.filter(return_date__isnull=False).values_list(
        "loan_date", "due_date", "return_date"
    )
    for loan_date, due_date, return_date in rows:
        returned_on = return_date.date()
        if due_date and returned_on > due_date:
            late += 1
        if loan_date:
            durations.append((returned_on - loan_date.date()).days)
    return late, durations


def _monthly_chart(period, category: str) -> Chart:
    from apps.loans.models import Loan

    labels, values = [], []
    for start, end, label in months_between(period):
        qs = Loan.objects.filter(loan_date__date__gte=start, loan_date__date__lte=end)
        if category:
            qs = qs.filter(item__record__category__code=category)
        labels.append(label)
        values.append(qs.count())
    return Chart(
        title=_("Les prêts mois par mois"), kind="bar",
        labels=labels, values=values, unit=_("prêts"),
    )


def _by_book_category(period_loans) -> Chart:
    rows = (
        period_loans.values("item__record__category__name")
        .annotate(n=Count("id"))
        .order_by("-n")
    )
    labels = [row["item__record__category__name"] or _("Sans rayon") for row in rows]
    return Chart(
        title=_("Ce qui se prête, par rayon"), kind="pie",
        labels=labels, values=[row["n"] for row in rows], unit=_("prêts"),
    )


def _by_member_category(period_loans) -> Chart:
    rows = (
        period_loans.values("member__category__name").annotate(n=Count("id")).order_by("-n")
    )
    labels = [row["member__category__name"] or _("Sans catégorie") for row in rows]
    return Chart(
        title=_("Qui emprunte, par catégorie d'usager"), kind="pie",
        labels=labels, values=[row["n"] for row in rows], unit=_("prêts"),
    )


def _top_books(period_loans, most: bool) -> Table:
    order = "-n" if most else "n"
    rows_qs = (
        period_loans.values(
            "item__record_id", "item__record__title", "item__record__category__name"
        )
        .annotate(n=Count("id"))
        .order_by(order, "item__record__title")[:TOP_SIZE]
    )
    rows = [
        [
            row["item__record__title"],
            row["item__record__category__name"] or "—",
            fmt.number(row["n"]),
        ]
        for row in rows_qs
    ]
    if most:
        title = _("Les livres les plus empruntés")
        note = _("Les %(n)s titres les plus sortis pendant la période.") % {"n": TOP_SIZE}
    else:
        title = _("Les livres les moins empruntés")
        note = _(
            "Les %(n)s titres les moins sortis parmi ceux qui sont sortis au moins "
            "une fois. Les livres jamais empruntés sont comptés séparément."
        ) % {"n": TOP_SIZE}
    return Table(
        title=title,
        columns=[Column(_("Livre")), Column(_("Rayon")), Column(_("Prêts"), "right")],
        rows=rows,
        empty_text=_("Aucun prêt pendant cette période."),
        note=note,
    )


def _never_loaned(category: str) -> Table:
    """Combien de livres n'ont jamais été empruntés, par rayon."""
    from apps.catalog.models import Item

    # `loans__isnull=True` plutôt qu'un `Count(...) == 0` : le regroupement par
    # rayon qui suit rouvrirait un HAVING sur l'annotation et fausserait le
    # décompte. La jointure gauche, elle, se compose sans piège.
    qs = Item.objects.filter(loans__isnull=True)
    if category:
        qs = qs.filter(record__category__code=category)
    rows_qs = qs.values("record__category__name").annotate(n=Count("id")).order_by("-n")
    rows = [
        [row["record__category__name"] or _("Sans rayon"), fmt.number(row["n"])]
        for row in rows_qs
    ]
    return Table(
        title=_("Les livres jamais empruntés"),
        columns=[Column(_("Rayon")), Column(_("Livres"), "right")],
        rows=rows,
        empty_text=_("Tous les livres du fonds sont sortis au moins une fois."),
        note=_("Depuis leur entrée au catalogue, pas seulement sur la période."),
    )


def _reservations(period) -> Table:
    """Ce que deviennent les réservations : honorées, expirées, abandonnées."""
    from apps.loans.models import Reservation, ReservationStatus

    rows_qs = (
        Reservation.objects.filter(
            created_at__date__gte=period.start, created_at__date__lte=period.end
        )
        .values("status")
        .annotate(n=Count("id"))
    )
    counts = {row["status"]: row["n"] for row in rows_qs}
    total = sum(counts.values())
    rows = [
        [str(label), fmt.number(counts.get(value, 0)), fmt.percent(counts.get(value, 0), total)]
        for value, label in ReservationStatus.choices
        if counts.get(value)
    ]
    return Table(
        title=_("Les réservations de la période"),
        columns=[Column(_("Ce qu'elles sont devenues")), Column(_("Nombre"), "right"),
                 Column(_("Part"), "right")],
        rows=rows,
        empty_text=_("Aucune réservation pendant cette période."),
    )


def _by_open_day(period_loans, period) -> Table:
    """Un jour par ligne, mais seulement les jours où il s'est passé quelque
    chose : la bibliothèque n'ouvre pas tous les jours, et une ligne à zéro par
    jour de fermeture noierait le tableau."""
    from apps.loans.models import Loan

    out: dict[date, list[int]] = {}
    for loan_date in period_loans.values_list("loan_date", flat=True):
        day = loan_date.date()
        out.setdefault(day, [0, 0])[0] += 1
    returns = Loan.objects.filter(
        return_date__date__gte=period.start, return_date__date__lte=period.end
    ).values_list("return_date", flat=True)
    for return_date in returns:
        day = return_date.date()
        out.setdefault(day, [0, 0])[1] += 1

    rows = [
        [fmt.day(day), fmt.number(counts[0]), fmt.number(counts[1])]
        for day, counts in sorted(out.items())
    ]
    return Table(
        title=_("Jour par jour"),
        columns=[Column(_("Jour")), Column(_("Prêts"), "right"), Column(_("Retours"), "right")],
        rows=rows,
        total_row=[
            _("Total"),
            fmt.number(sum(c[0] for c in out.values())),
            fmt.number(sum(c[1] for c in out.values())),
        ] if rows else None,
        empty_text=_("Aucun mouvement pendant cette période."),
        note=_("Seuls les jours où la bibliothèque a prêté ou reçu un livre sont listés."),
    )


def _active_detail() -> Table:
    """Prêts et réservations en cours, ligne par ligne. FEAT-093 (retour Val).

    C'est l'ancien export « Prêts et réservations en cours (CSV) » du hub,
    devenu un sous-rapport : il a maintenant un écran, et donc ses exports PDF
    et Excel. Les deux natures sont dans le même tableau, distinguées par une
    colonne — séparées, on perdrait de vue que le même livre peut être prêté à
    l'un et attendu par l'autre.
    """
    from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus
    from apps.loans.services import pickup_expiration_for

    rows = []
    for loan in (
        Loan.objects.filter(status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE])
        .select_related("item__record", "member")
        .order_by("due_date")
    ):
        rows.append([
            _("Prêt"),
            f"{loan.member.last_name} {loan.member.first_name}".strip(),
            loan.item.record.title,
            loan.item.internal_id,
            loan.get_status_display(),
            fmt.day(loan.due_date),
        ])
    for res in (
        Reservation.objects.filter(
            status__in=[ReservationStatus.PENDING, ReservationStatus.READY_FOR_PICKUP]
        )
        .select_related("record", "member", "fulfilled_by_item")
        .order_by("created_at")
    ):
        deadline = (
            pickup_expiration_for(res)
            if res.status == ReservationStatus.READY_FOR_PICKUP
            else res.expires_at
        )
        rows.append([
            _("Réservation"),
            f"{res.member.last_name} {res.member.first_name}".strip(),
            res.record.title,
            res.fulfilled_by_item.internal_id if res.fulfilled_by_item else "—",
            res.get_status_display(),
            fmt.day(deadline),
        ])
    return Table(
        title=_("Prêts et réservations en cours"),
        columns=[
            Column(_("Nature")), Column(_("Usager")), Column(_("Livre")),
            Column(_("N° du livre")), Column(_("Situation")),
            Column(_("Échéance")),
        ],
        rows=rows,
        empty_text=_("Aucun prêt ni réservation en cours."),
        note=_("Situation d'aujourd'hui : ce tableau ne dépend pas de la période choisie."),
    )


def _period_detail(period_loans) -> Table:
    """Tous les prêts de la période, ligne par ligne — l'ancien export CSV."""
    rows = [
        [
            fmt.day(loan.loan_date.date()) if loan.loan_date else "—",
            f"{loan.member.last_name} {loan.member.first_name}".strip(),
            loan.item.record.title,
            loan.item.internal_id,
            fmt.day(loan.due_date),
            fmt.day(loan.return_date.date()) if loan.return_date else _("pas rendu"),
            loan.get_status_display(),
        ]
        for loan in period_loans.select_related("item__record", "member").order_by("loan_date")
    ]
    return Table(
        title=_("Le détail des prêts de la période"),
        columns=[
            Column(_("Prêté le")), Column(_("Usager")), Column(_("Livre")),
            Column(_("N° du livre")), Column(_("À rendre le")),
            Column(_("Rendu le")), Column(_("Situation")),
        ],
        rows=rows,
        empty_text=_("Aucun prêt pendant cette période."),
    )
