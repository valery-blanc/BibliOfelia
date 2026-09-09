"""L'argent. FEAT-093.

Les factures impayées ouvrent l'écran : c'est une liste de travail — on
téléphone — pas une statistique. Le reste (recettes, modes de paiement, caisse
jour par jour) répond au trésorier de l'association.

Tous les montants passent par `apps.finance.money.format_amount`, qui connaît
la devise de l'instance : ariary sur la Box de Madagascar, franc suisse au
Grand-Saconnex.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db.models import Count, Sum
from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Chart, Column, Kpi, ReportPage, Table
from ..periods import months_between


def build(period, params) -> ReportPage:
    from apps.finance.models import (
        CashDirection,
        CashMovement,
        FeeKind,
        Invoice,
        InvoiceLine,
        InvoiceStatus,
        Payment,
        PaymentMethod,
    )

    invoices = Invoice.objects.filter(
        issue_date__gte=period.start, issue_date__lte=period.end
    ).exclude(status=InvoiceStatus.CANCELLED)
    payments = Payment.objects.filter(paid_on__gte=period.start, paid_on__lte=period.end)
    movements = CashMovement.objects.filter(
        occurred_on__gte=period.start, occurred_on__lte=period.end
    )

    billed = invoices.aggregate(n=Sum("total_amount"))["n"] or Decimal("0")
    cashed = payments.aggregate(n=Sum("amount"))["n"] or Decimal("0")
    cash_in = movements.filter(direction=CashDirection.IN).aggregate(
        n=Sum("amount")
    )["n"] or Decimal("0")
    cash_out = movements.filter(direction=CashDirection.OUT).aggregate(
        n=Sum("amount")
    )["n"] or Decimal("0")

    # Le reste dû se lit sur **toutes** les factures ouvertes, pas seulement
    # celles de la période : une facture de l'an dernier toujours impayée est
    # de l'argent qui manque aujourd'hui.
    open_invoices = Invoice.objects.filter(status=InvoiceStatus.OPEN).select_related("member")
    outstanding = sum((invoice.balance for invoice in open_invoices), Decimal("0"))

    kpis = [
        Kpi(_("Facturé"), fmt.money(billed), _("sur la période"), "burgundy"),
        Kpi(_("Encaissé"), fmt.money(cashed), _("paiements reçus sur la période"), "forest"),
        Kpi(_("Reste dû"), fmt.money(outstanding),
            _("toutes factures ouvertes confondues"), "blush"),
        Kpi(_("Entrées de caisse"), fmt.money(cash_in), _("espèces reçues"), "sky"),
        Kpi(_("Sorties de caisse"), fmt.money(cash_out), _("dépenses saisies"), "orange"),
        Kpi(_("Solde de la caisse"), fmt.money(cash_in - cash_out),
            _("entrées moins sorties sur la période"), "olive"),
    ]

    blocks = [
        _unpaid(open_invoices),
        _by_kind_chart(period, FeeKind, InvoiceLine),
        _monthly_chart(period),
        _by_kind_table(period, FeeKind, InvoiceLine),
        _by_method(payments, PaymentMethod, cashed),
        _daily(payments, movements, CashDirection),
        _movements(movements),
    ]

    return ReportPage(
        slug="money",
        title=_("L'argent"),
        subtitle=_("Ce qui a été facturé, ce qui a été encaissé, ce qui reste dû."),
        kpis=kpis,
        blocks=blocks,
        period=period,
    )


def _unpaid(open_invoices) -> Table:
    today = date.today()
    rows = []
    for invoice in open_invoices.order_by("due_date"):
        rows.append([
            f"{invoice.member.last_name} {invoice.member.first_name}".strip(),
            invoice.number,
            fmt.day(invoice.issue_date),
            fmt.money(invoice.total_amount),
            fmt.money(invoice.balance),
            fmt.number((today - invoice.due_date).days) if invoice.due_date < today else "—",
        ])
    return Table(
        title=_("Les factures à encaisser"),
        columns=[
            Column(_("Usager")), Column(_("N° de facture")), Column(_("Émise le")),
            Column(_("Total"), "right"), Column(_("Reste dû"), "right"),
            Column(_("Jours de retard"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucune facture en attente de paiement."),
        note=_("Toutes les factures ouvertes, y compris celles émises avant la période."),
    )


def _kind_totals(period, InvoiceLine) -> dict[str, Decimal]:
    from django.db.models import F

    rows = (
        InvoiceLine.objects.filter(
            invoice__issue_date__gte=period.start,
            invoice__issue_date__lte=period.end,
        )
        .exclude(invoice__status="cancelled")
        .values("kind")
        .annotate(total=Sum(F("amount") * F("quantity")))
    )
    return {row["kind"]: row["total"] or Decimal("0") for row in rows}


def _by_kind_chart(period, FeeKind, InvoiceLine) -> Chart:
    totals = _kind_totals(period, InvoiceLine)
    labels, values = [], []
    for value, label in FeeKind.choices:
        if totals.get(value):
            labels.append(str(label))
            values.append(float(totals[value]))
    return Chart(
        title=_("D'où vient l'argent"), kind="pie",
        labels=labels, values=values, unit=_("montant"),
    )


def _by_kind_table(period, FeeKind, InvoiceLine) -> Table:
    totals = _kind_totals(period, InvoiceLine)
    grand = sum(totals.values(), Decimal("0"))
    rows = [
        [str(label), fmt.money(totals.get(value, 0)),
         fmt.percent(float(totals.get(value, 0)), float(grand))]
        for value, label in FeeKind.choices
        if totals.get(value)
    ]
    return Table(
        title=_("Les recettes par nature"),
        columns=[Column(_("Nature")), Column(_("Montant"), "right"), Column(_("Part"), "right")],
        rows=rows,
        total_row=[_("Total"), fmt.money(grand), "100 %"] if rows else None,
        empty_text=_("Aucune facture émise sur cette période."),
    )


def _monthly_chart(period) -> Chart:
    from apps.finance.models import Payment

    labels, values = [], []
    for start, end, label in months_between(period):
        total = Payment.objects.filter(paid_on__gte=start, paid_on__lte=end).aggregate(
            n=Sum("amount")
        )["n"] or Decimal("0")
        labels.append(label)
        values.append(float(total))
    return Chart(
        title=_("Les encaissements mois par mois"), kind="bar",
        labels=labels, values=values, unit=_("montant"),
    )


def _by_method(payments, PaymentMethod, cashed) -> Table:
    totals = {
        row["method"]: row["total"] or Decimal("0")
        for row in payments.values("method").annotate(total=Sum("amount"), n=Count("id"))
    }
    counts = {row["method"]: row["n"] for row in payments.values("method").annotate(n=Count("id"))}
    rows = [
        [str(label), fmt.number(counts.get(value, 0)), fmt.money(totals.get(value, 0)),
         fmt.percent(float(totals.get(value, 0)), float(cashed))]
        for value, label in PaymentMethod.choices
        if totals.get(value)
    ]
    return Table(
        title=_("Comment les gens paient"),
        columns=[
            Column(_("Mode de paiement")), Column(_("Paiements"), "right"),
            Column(_("Montant"), "right"), Column(_("Part"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucun paiement sur cette période."),
    )


def _daily(payments, movements, CashDirection) -> Table:
    """La caisse jour par jour — l'équivalent de la « Caisse journalière »,
    replié sur la période plutôt qu'imprimé un jour à la fois."""
    days: dict[date, list[Decimal]] = {}

    def bucket(day: date) -> list[Decimal]:
        return days.setdefault(day, [Decimal("0"), Decimal("0"), Decimal("0")])

    for paid_on, amount, method in payments.values_list("paid_on", "amount", "method"):
        slot = bucket(paid_on)
        if method == "cash":
            slot[0] += amount
        else:
            slot[1] += amount
    for occurred_on, amount, direction in movements.values_list(
        "occurred_on", "amount", "direction"
    ):
        if direction == CashDirection.OUT:
            bucket(occurred_on)[2] += amount

    rows = [
        [
            fmt.day(day),
            fmt.money(values[0]),
            fmt.money(values[1]),
            fmt.money(values[2]),
            fmt.money(values[0] - values[2]),
        ]
        for day, values in sorted(days.items())
    ]
    return Table(
        title=_("La caisse jour par jour"),
        columns=[
            Column(_("Jour")), Column(_("Espèces"), "right"),
            Column(_("Autres paiements"), "right"), Column(_("Sorties"), "right"),
            Column(_("Solde espèces du jour"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucun mouvement d'argent sur cette période."),
    )


def _movements(movements) -> Table:
    rows = [
        [
            fmt.day(movement.occurred_on),
            movement.get_direction_display(),
            movement.label,
            fmt.money(movement.amount),
        ]
        for movement in movements.order_by("occurred_on", "id")
    ]
    return Table(
        title=_("Le détail de la caisse"),
        columns=[
            Column(_("Jour")), Column(_("Sens")), Column(_("Motif")),
            Column(_("Montant"), "right"),
        ],
        rows=rows,
        empty_text=_("Aucun mouvement de caisse sur cette période."),
    )
