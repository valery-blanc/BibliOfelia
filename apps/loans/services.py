"""Logique métier prêts / retours / réservations. SPEC §6.3 et §6.4.

Toutes les règles (durée de prêt, limites, satisfaction des réservations) sont
ici, séparées des vues, pour être testables unitairement.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Item, ItemStatus
from apps.core.models import Setting
from apps.members.models import Member, MemberStatus

from .models import Loan, LoanStatus, Reservation, ReservationStatus

DEFAULT_LOAN_DAYS = 21
DEFAULT_MAX_RENEWALS = 2
DEFAULT_RESERVATION_EXPIRY_DAYS = 7
DEFAULT_PICKUP_HOLD_DAYS = 5

_OPEN_LOAN_STATUSES = (LoanStatus.ACTIVE, LoanStatus.OVERDUE)
_OPEN_RESERVATION_STATUSES = (
    ReservationStatus.PENDING,
    ReservationStatus.READY_FOR_PICKUP,
)


# --------------------------------------------------------------------------
# Paramètres
# --------------------------------------------------------------------------
def _setting_int(key: str, default: int) -> int:
    try:
        return int(Setting.get(key, default))
    except (TypeError, ValueError):
        return default


def compute_due_date(member: Member, record, today: date | None = None) -> date:
    """Durée de prêt : règle du type de document si définie, sinon catégorie
    d'usager, sinon `Setting.default_loan_days` (FEAT-035), sinon constante."""
    today = today or date.today()
    days = None
    if record.category_id and record.category.default_loan_duration_days:
        days = record.category.default_loan_duration_days
    if not days:
        days = member.category.default_loan_duration_days
    if not days:
        days = _setting_int("default_loan_days", DEFAULT_LOAN_DAYS)
    return today + timedelta(days=days)


# --------------------------------------------------------------------------
# Vérifications de prêt
# --------------------------------------------------------------------------
@dataclass
class LoanCheck:
    ok: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def active_loan_count(member: Member) -> int:
    return member.loans.filter(status__in=_OPEN_LOAN_STATUSES).count()


def _ready_reservation_for_item(item: Item) -> Reservation | None:
    return (
        Reservation.objects.filter(
            fulfilled_by_item=item, status=ReservationStatus.READY_FOR_PICKUP
        )
        .select_related("member")
        .first()
    )


def check_item_loanable(item: Item, member: Member, basket_count: int = 0) -> LoanCheck:
    """Contrôles SPEC §6.3 étape 5. `basket_count` = exemplaires déjà dans le
    panier de prêt en cours (comptés dans la limite)."""
    check = LoanCheck()
    record = item.record

    if member.status != MemberStatus.ACTIVE:
        check.ok = False
        check.errors.append(
            _("Usager %(status)s : prêt impossible.") % {"status": member.get_status_display()}
        )
        return check

    # Vérité de la table Loan, pas du cache `item.status` : un exemplaire déjà
    # prêté ne peut pas l'être une 2e fois même si son statut a divergé (prêt
    # créé hors du service, ex. via /admin/).
    if Loan.objects.filter(item=item, status__in=_OPEN_LOAN_STATUSES).exists():
        check.ok = False
        check.errors.append(_("Cet ouvrage est déjà prêté."))
        return check

    if item.status == ItemStatus.RESERVED_FOR_PICKUP:
        ready = _ready_reservation_for_item(item)
        if ready and ready.member_id != member.pk:
            check.ok = False
            check.errors.append(_("Exemplaire mis de côté pour un autre usager."))
            return check
    elif item.status != ItemStatus.AVAILABLE:
        check.ok = False
        check.errors.append(_("Exemplaire non disponible au prêt."))
        return check

    if not member.category.allows_document_type(record.document_type):
        check.ok = False
        check.errors.append(
            _("Ce type de document n'est pas autorisé pour cet usager.")
        )

    limit = member.category.max_concurrent_loans
    if active_loan_count(member) + basket_count >= limit:
        check.ok = False
        check.errors.append(
            _("Limite de prêts atteinte (%(limit)s) pour cet usager.")
            % {"limit": limit}
        )

    other_reservation = (
        Reservation.objects.filter(record=record, status__in=_OPEN_RESERVATION_STATUSES)
        .exclude(member=member)
        .exists()
    )
    if other_reservation and item.status == ItemStatus.AVAILABLE:
        check.warnings.append(
            _("Une réservation d'un autre usager existe sur cette notice.")
        )
    return check


# --------------------------------------------------------------------------
# Création de prêt
# --------------------------------------------------------------------------
@transaction.atomic
def create_loan(item: Item, member: Member, librarian, notes: str = "") -> Loan:
    loan = Loan.objects.create(
        item=item,
        member=member,
        due_date=compute_due_date(member, item.record),
        librarian=librarian,
        notes=notes,
    )
    item.status = ItemStatus.ON_LOAN
    item.save(update_fields=["status"])
    _fulfil_reservation_on_loan(item, member, loan)
    return loan


def _fulfil_reservation_on_loan(item: Item, member: Member, loan: Loan) -> None:
    """Si l'usager avait une réservation sur cette notice, elle est honorée."""
    reservation = (
        Reservation.objects.filter(
            record=item.record,
            member=member,
            status__in=_OPEN_RESERVATION_STATUSES,
        )
        .order_by("created_at")
        .first()
    )
    if reservation:
        reservation.status = ReservationStatus.FULFILLED
        reservation.fulfilled_by_item = item
        reservation.fulfilled_by_loan = loan
        reservation.save(
            update_fields=["status", "fulfilled_by_item", "fulfilled_by_loan"]
        )


# --------------------------------------------------------------------------
# Retour
# --------------------------------------------------------------------------
@dataclass
class ReturnResult:
    item: Item
    kind: str  # "returned" | "reintegrated" | "no_loan"
    was_overdue: bool = False
    reservation: Reservation | None = None


@transaction.atomic
def return_item(item: Item, librarian=None) -> ReturnResult:
    """Retour d'un exemplaire. Gère le retour normal, le retour différé d'un
    livre perdu (réintégration) et la satisfaction des réservations."""
    if item.status == ItemStatus.LOST:
        # Retour différé d'un livre déclaré perdu (SPEC §6.3).
        Loan.objects.filter(item=item, status=LoanStatus.LOST).update(
            return_date=timezone.now()
        )
        item.status = ItemStatus.AVAILABLE
        item.save(update_fields=["status"])
        reservation = satisfy_reservations_for_item(item)
        return ReturnResult(item=item, kind="reintegrated", reservation=reservation)

    loan = (
        Loan.objects.filter(item=item, status__in=_OPEN_LOAN_STATUSES)
        .order_by("-loan_date")
        .first()
    )
    if loan is None:
        return ReturnResult(item=item, kind="no_loan")

    was_overdue = loan.due_date < date.today()
    loan.return_date = timezone.now()
    loan.status = LoanStatus.RETURNED
    if was_overdue:
        loan.notes = (loan.notes + "\nRetour en retard.").strip()
    loan.save(update_fields=["return_date", "status", "notes"])

    item.status = ItemStatus.AVAILABLE
    item.save(update_fields=["status"])
    reservation = satisfy_reservations_for_item(item)
    return ReturnResult(
        item=item, kind="returned", was_overdue=was_overdue, reservation=reservation
    )


# --------------------------------------------------------------------------
# Renouvellement
# --------------------------------------------------------------------------
@dataclass
class RenewResult:
    ok: bool
    reason: str = ""
    new_due_date: date | None = None


def renew_loan(loan: Loan) -> RenewResult:
    """Renouvelle un prêt. SPEC §6.3 : max 2 par défaut, refusé si réservation
    en attente sur la notice."""
    if loan.status not in _OPEN_LOAN_STATUSES:
        return RenewResult(ok=False, reason=_("Ce prêt n'est pas renouvelable."))

    max_renewals = _setting_int("max_renewals", DEFAULT_MAX_RENEWALS)
    if loan.renewal_count >= max_renewals:
        return RenewResult(
            ok=False,
            reason=_("Nombre maximum de renouvellements atteint (%(n)s).")
            % {"n": max_renewals},
        )

    if Reservation.objects.filter(
        record=loan.item.record, status__in=_OPEN_RESERVATION_STATUSES
    ).exists():
        return RenewResult(
            ok=False, reason=_("Une réservation est en attente sur cette notice.")
        )

    loan.renewal_count += 1
    loan.due_date = compute_due_date(loan.member, loan.item.record)
    loan.status = LoanStatus.ACTIVE
    loan.save(update_fields=["renewal_count", "due_date", "status"])
    return RenewResult(ok=True, new_due_date=loan.due_date)


# --------------------------------------------------------------------------
# Livre perdu
# --------------------------------------------------------------------------
@transaction.atomic
def declare_lost(loan: Loan) -> None:
    """Déclare perdu un prêt actif (SPEC §6.3). Aucune facturation."""
    loan.status = LoanStatus.LOST
    loan.save(update_fields=["status"])
    item = loan.item
    item.status = ItemStatus.LOST
    item.save(update_fields=["status"])


# --------------------------------------------------------------------------
# Réservations (SPEC §6.4)
# --------------------------------------------------------------------------
def create_reservation(record, member: Member) -> Reservation:
    days = _setting_int("reservation_expiry_days", DEFAULT_RESERVATION_EXPIRY_DAYS)
    return Reservation.objects.create(
        record=record,
        member=member,
        expires_at=date.today() + timedelta(days=days),
    )


@transaction.atomic
def satisfy_reservations_for_item(item: Item) -> Reservation | None:
    """Au retour d'un exemplaire, met de côté la plus ancienne réservation
    `pending` (FIFO). SPEC §6.4."""
    if item.status != ItemStatus.AVAILABLE:
        return None
    reservation = (
        Reservation.objects.filter(
            record=item.record, status=ReservationStatus.PENDING
        )
        .order_by("created_at")
        .first()
    )
    if reservation is None:
        return None
    reservation.status = ReservationStatus.READY_FOR_PICKUP
    reservation.ready_since = date.today()
    reservation.fulfilled_by_item = item
    reservation.save(update_fields=["status", "ready_since", "fulfilled_by_item"])
    item.status = ItemStatus.RESERVED_FOR_PICKUP
    item.save(update_fields=["status"])
    return reservation


def mark_reservation_notified(reservation: Reservation) -> bool:
    """FEAT-036 : note l'instant où le bibliothécaire a contacté le membre.
    Idempotent : retourne True si nouveau, False si déjà notifié."""
    if reservation.notified_at is not None:
        return False
    reservation.notified_at = timezone.now()
    reservation.save(update_fields=["notified_at"])
    return True


def cancel_reservation(reservation: Reservation) -> None:
    """Annule une réservation et libère l'exemplaire mis de côté le cas échéant."""
    freed_item = (
        reservation.fulfilled_by_item
        if reservation.status == ReservationStatus.READY_FOR_PICKUP
        else None
    )
    reservation.status = ReservationStatus.CANCELLED
    reservation.save(update_fields=["status"])
    if freed_item:
        _release_held_item(freed_item)


def _release_held_item(item: Item) -> None:
    """Libère un exemplaire mis de côté : il passe à la réservation suivante,
    ou redevient disponible."""
    item.status = ItemStatus.AVAILABLE
    item.save(update_fields=["status"])
    satisfy_reservations_for_item(item)


def pickup_expiration_for(reservation: Reservation, today: date | None = None) -> date | None:
    """Date d'expiration d'une réservation `READY_FOR_PICKUP` (FEAT-034). None
    si la réservation n'est pas encore mise de côté."""
    if reservation.status != ReservationStatus.READY_FOR_PICKUP or reservation.ready_since is None:
        return None
    hold_days = _setting_int("pickup_hold_days", DEFAULT_PICKUP_HOLD_DAYS)
    return reservation.ready_since + timedelta(days=hold_days)


def reservations_due_soon(within_days: int = 2, today: date | None = None) -> list[dict]:
    """FEAT-034 : réservations `READY_FOR_PICKUP` dont la date limite de retrait
    est aujourd'hui+`within_days` ou déjà dépassée. Triées par expiration
    ascendante. Renvoie une liste de dicts `{reservation, expires_on, days_left}`
    pour éviter d'attacher des attributs au modèle côté template."""
    today = today or date.today()
    hold_days = _setting_int("pickup_hold_days", DEFAULT_PICKUP_HOLD_DAYS)
    threshold = today + timedelta(days=within_days)
    ready_deadline = threshold - timedelta(days=hold_days)
    qs = (
        Reservation.objects.filter(
            status=ReservationStatus.READY_FOR_PICKUP,
            ready_since__lte=ready_deadline,
        )
        .select_related("record", "member", "fulfilled_by_item")
        .order_by("ready_since")
    )
    result = []
    for reservation in qs:
        expires_on = reservation.ready_since + timedelta(days=hold_days)
        delta = (expires_on - today).days
        result.append({
            "reservation": reservation,
            "expires_on": expires_on,
            "days_left": delta,
            "days_overdue": -delta if delta < 0 else 0,
            "is_overdue": delta < 0,
            "is_today": delta == 0,
        })
    return result


@transaction.atomic
def expire_stale_reservations(today: date | None = None) -> dict[str, int]:
    """Tâche django-q2 quotidienne. Expire les réservations `pending` échues et
    les `ready_for_pickup` non retirées au-delà de `pickup_hold_days`."""
    today = today or date.today()
    hold_days = _setting_int("pickup_hold_days", DEFAULT_PICKUP_HOLD_DAYS)

    pending_expired = Reservation.objects.filter(
        status=ReservationStatus.PENDING, expires_at__lt=today
    ).update(status=ReservationStatus.EXPIRED)

    deadline = today - timedelta(days=hold_days)
    stale = list(
        Reservation.objects.filter(
            status=ReservationStatus.READY_FOR_PICKUP, ready_since__lt=deadline
        ).select_related("fulfilled_by_item")
    )
    for reservation in stale:
        reservation.status = ReservationStatus.EXPIRED
        reservation.save(update_fields=["status"])
        if reservation.fulfilled_by_item:
            _release_held_item(reservation.fulfilled_by_item)

    return {"pending_expired": pending_expired, "pickup_expired": len(stale)}
