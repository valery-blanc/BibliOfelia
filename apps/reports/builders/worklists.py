"""Les trois listes de travail. FEAT-093.

Retards, réservations à retirer, inactifs. Elles décrivent *aujourd'hui* : pas
de période, un seul réglage, et un bouton principal **Imprimer** — ce sont des
listes qu'on emporte au comptoir pour téléphoner, pas des tableaux qu'on
analyse. D'où le téléphone en colonne visible : sans lui, la liste des retards
oblige à rouvrir chaque fiche.
"""
from __future__ import annotations

from datetime import date, timedelta

from django.utils.translation import gettext as _

from .. import format as fmt
from ..pages import Column, Kpi, ReportPage, Table

# Les seuils proposés en boutons, plutôt qu'un champ à taper (avis Grok).
OVERDUE_THRESHOLDS = [0, 7, 14, 30]
INACTIVE_THRESHOLDS = [180, 365, 730]


def _int_param(params, name: str, default: int, allowed: list[int]) -> int:
    try:
        value = int(params.get(name, default))
    except (TypeError, ValueError):
        return default
    return value if value in allowed else default


# ── Les retards ────────────────────────────────────────────────────────────


def count_overdue() -> int:
    from apps.loans.models import Loan, LoanStatus

    return Loan.objects.filter(
        status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE], due_date__lt=date.today()
    ).count()


def build_overdue(period, params) -> ReportPage:
    from apps.loans.models import Loan, LoanStatus

    threshold = _int_param(params, "threshold", 7, OVERDUE_THRESHOLDS)
    today = date.today()
    cutoff = today - timedelta(days=threshold)
    loans = list(
        Loan.objects.filter(
            status__in=[LoanStatus.ACTIVE, LoanStatus.OVERDUE], due_date__lt=cutoff
        )
        .select_related("item__record", "member")
        .order_by("due_date")
    )

    rows = []
    for loan in loans:
        rows.append([
            f"{loan.member.last_name} {loan.member.first_name}".strip(),
            fmt.blank(loan.member.contact_phone),
            loan.item.record.title,
            loan.item.internal_id,
            fmt.day(loan.due_date),
            fmt.number((today - loan.due_date).days),
        ])

    worst = max((today - loan.due_date).days for loan in loans) if loans else 0
    page = ReportPage(
        slug="overdue",
        title=_("Les retards"),
        subtitle=_("Livres non rendus dont l'échéance est passée de plus de %(n)s jours.")
        % {"n": threshold}
        if threshold
        else _("Tous les livres non rendus dont l'échéance est passée."),
        kpis=[
            Kpi(_("Livres en retard"), fmt.number(len(loans)),
                _("à relancer aujourd'hui"), "burgundy"),
            Kpi(_("Le plus ancien"), fmt.days(worst),
                _("de retard"), "orange"),
        ],
        blocks=[
            Table(
                title=_("À rappeler"),
                columns=[
                    Column(_("Usager")),
                    Column(_("Téléphone")),
                    Column(_("Livre")),
                    Column(_("N° du livre")),
                    Column(_("À rendre le")),
                    Column(_("Jours de retard"), "right"),
                ],
                rows=rows,
                empty_text=_("Aucun retard. Tout est rentré."),
            )
        ],
    )
    page.filters = {"threshold": threshold, "thresholds": OVERDUE_THRESHOLDS}
    return page


# ── Les réservations à retirer ─────────────────────────────────────────────


def count_pickup() -> int:
    from apps.loans.models import Reservation, ReservationStatus

    return Reservation.objects.filter(status=ReservationStatus.READY_FOR_PICKUP).count()


def build_pickup(period, params) -> ReportPage:
    from apps.loans.models import Reservation, ReservationStatus
    from apps.loans.services import pickup_expiration_for

    reservations = list(
        Reservation.objects.filter(status=ReservationStatus.READY_FOR_PICKUP)
        .select_related("record", "member", "fulfilled_by_item")
        .order_by("ready_since")
    )

    rows, to_call = [], 0
    for res in reservations:
        if res.notified_at is None:
            to_call += 1
        rows.append([
            f"{res.member.last_name} {res.member.first_name}".strip(),
            fmt.blank(res.member.contact_phone),
            res.record.title,
            res.fulfilled_by_item.internal_id if res.fulfilled_by_item else "—",
            fmt.day(res.ready_since),
            fmt.day(pickup_expiration_for(res)),
            _("Non") if res.notified_at is None else _("Oui"),
        ])

    return ReportPage(
        slug="pickup",
        title=_("Les réservations à retirer"),
        subtitle=_("Livres mis de côté qui attendent leur usager."),
        kpis=[
            Kpi(_("Livres mis de côté"), fmt.number(len(reservations)),
                _("à garder au comptoir"), "amber"),
            Kpi(_("Usagers à prévenir"), fmt.number(to_call),
                _("pas encore appelés"), "burgundy"),
        ],
        blocks=[
            Table(
                title=_("À prévenir et à remettre"),
                columns=[
                    Column(_("Usager")),
                    Column(_("Téléphone")),
                    Column(_("Livre")),
                    Column(_("N° du livre")),
                    Column(_("Mis de côté le")),
                    Column(_("À retirer avant le")),
                    Column(_("Prévenu ?")),
                ],
                rows=rows,
                empty_text=_("Aucun livre en attente de retrait."),
            )
        ],
    )


# ── Les inactifs ───────────────────────────────────────────────────────────


def count_inactive() -> int:
    from ..services import inactive_members

    return inactive_members(days=365).count()


def build_inactive(period, params) -> ReportPage:
    """Usagers et exemplaires sans mouvement, **triables par catégorie**.

    Le tri par catégorie est une demande explicite de Val : sans lui, la liste
    des exemplaires dormants mélange les albums pour enfants et les romans, et
    ne dit pas quel rayon ne tourne pas.
    """
    from apps.catalog.models import Category
    from apps.members.models import MemberCategory

    from ..services import inactive_items, inactive_members

    days = _int_param(params, "days", 365, INACTIVE_THRESHOLDS)
    item_category = (params.get("category") or "").strip()
    member_category = (params.get("member_category") or "").strip()

    members = inactive_members(days=days).select_related("category")
    if member_category:
        members = members.filter(category__code=member_category)
    items = inactive_items(days=days).select_related("record__category")
    if item_category:
        items = items.filter(record__category__code=item_category)

    members = list(members)
    items = list(items)

    member_rows = [
        [
            f"{m.last_name} {m.first_name}".strip(),
            m.card_number,
            m.category.name if m.category else "—",
            fmt.blank(m.contact_phone),
            fmt.day(m.registration_date),
            fmt.day(m.last_activity.date()) if m.last_activity else _("jamais"),
        ]
        for m in members
    ]
    item_rows = [
        [
            it.record.title,
            it.internal_id,
            it.record.category.name if it.record.category else "—",
            fmt.day(it.acquisition_date),
            fmt.day(it.last_activity.date()) if it.last_activity else _("jamais"),
        ]
        for it in items
    ]

    page = ReportPage(
        slug="inactive",
        title=_("Les inactifs"),
        subtitle=_("Usagers et livres sans aucun prêt depuis %(n)s jours.") % {"n": days},
        kpis=[
            Kpi(_("Usagers sans prêt"), fmt.number(len(members)),
                _("depuis %(n)s jours") % {"n": days}, "amber"),
            Kpi(_("Livres jamais sortis"), fmt.number(len(items)),
                _("depuis %(n)s jours") % {"n": days}, "olive"),
        ],
        blocks=[
            Table(
                title=_("Usagers sans prêt"),
                columns=[
                    Column(_("Usager")),
                    Column(_("N° de carte")),
                    Column(_("Catégorie")),
                    Column(_("Téléphone")),
                    Column(_("Inscrit le")),
                    Column(_("Dernier prêt")),
                ],
                rows=member_rows,
                empty_text=_("Tous les usagers ont emprunté récemment."),
            ),
            Table(
                title=_("Livres qui ne sortent pas"),
                columns=[
                    Column(_("Livre")),
                    Column(_("N° du livre")),
                    Column(_("Classification")),
                    Column(_("Acquis le")),
                    Column(_("Dernier prêt")),
                ],
                rows=item_rows,
                empty_text=_("Tous les livres ont été empruntés récemment."),
            ),
        ],
    )
    page.filters = {
        "days": days,
        "thresholds": INACTIVE_THRESHOLDS,
        "category": item_category,
        "categories": list(Category.objects.order_by("code")),
        "member_category": member_category,
        "member_categories": list(MemberCategory.objects.order_by("code")),
    }
    return page
