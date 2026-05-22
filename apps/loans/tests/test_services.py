"""Tests logique métier prêts / retours / réservations. SPEC §6.3, §6.4."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.catalog.models import Item, ItemStatus
from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus
from apps.loans.services import (
    cancel_reservation,
    check_item_loanable,
    compute_due_date,
    create_loan,
    create_reservation,
    declare_lost,
    expire_stale_reservations,
    renew_loan,
    return_item,
    satisfy_reservations_for_item,
)

pytestmark = pytest.mark.django_db


# --- Durée de prêt -------------------------------------------------------
def test_compute_due_date_uses_member_category(member, record):
    due = compute_due_date(member, record, today=date(2026, 5, 1))
    assert due == date(2026, 5, 22)  # 21 jours


# --- Vérifications de prêt ----------------------------------------------
def test_check_ok_for_available_item(item, member):
    assert check_item_loanable(item, member).ok is True


def test_check_rejects_unavailable_item(item, member):
    item.status = ItemStatus.IN_REPAIR
    assert check_item_loanable(item, member).ok is False


def test_check_rejects_disallowed_document_type(item, member):
    member.category.allowed_document_types = ["comic"]
    member.category.save()
    check = check_item_loanable(item, member)
    assert check.ok is False


def test_check_rejects_when_loan_limit_reached(item, member):
    member.category.max_concurrent_loans = 1
    member.category.save()
    create_loan(item, member, librarian=None)
    other = Item.objects.create(record=item.record)
    assert check_item_loanable(other, member).ok is False


def test_check_warns_on_other_member_reservation(item, member, other_member):
    create_reservation(item.record, other_member)
    check = check_item_loanable(item, member)
    assert check.ok is True
    assert check.warnings


def test_check_rejects_item_with_existing_active_loan(item, member, other_member):
    """Un exemplaire déjà prêté est refusé même si `item.status` a divergé
    (prêt créé hors service, cache resté « disponible »)."""
    Loan.objects.create(
        item=item, member=other_member, due_date=date.today() + timedelta(days=21)
    )
    assert item.status == ItemStatus.AVAILABLE  # cache volontairement divergent
    assert check_item_loanable(item, member).ok is False


# --- Création de prêt ----------------------------------------------------
def test_create_loan_sets_item_on_loan(item, member, librarian):
    loan = create_loan(item, member, librarian)
    item.refresh_from_db()
    assert item.status == ItemStatus.ON_LOAN
    assert loan.status == LoanStatus.ACTIVE


def test_create_loan_fulfils_member_reservation(item, member, librarian):
    reservation = create_reservation(item.record, member)
    create_loan(item, member, librarian)
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.FULFILLED


# --- Retour --------------------------------------------------------------
def test_return_item_normal(item, member, librarian):
    create_loan(item, member, librarian)
    result = return_item(item)
    item.refresh_from_db()
    assert result.kind == "returned"
    assert item.status == ItemStatus.AVAILABLE


def test_return_item_overdue_flagged(item, member, librarian):
    loan = create_loan(item, member, librarian)
    Loan.objects.filter(pk=loan.pk).update(due_date=date.today() - timedelta(days=3))
    result = return_item(item)
    assert result.was_overdue is True


def test_return_item_no_active_loan(item):
    result = return_item(item)
    assert result.kind == "no_loan"


def test_return_lost_item_reintegrates(item, member, librarian):
    loan = create_loan(item, member, librarian)
    declare_lost(loan)
    result = return_item(item)
    item.refresh_from_db()
    assert result.kind == "reintegrated"
    assert item.status == ItemStatus.AVAILABLE
    loan.refresh_from_db()
    assert loan.status == LoanStatus.LOST  # le prêt reste « perdu »


# --- Renouvellement ------------------------------------------------------
def test_renew_loan_ok(item, member, librarian):
    loan = create_loan(item, member, librarian)
    result = renew_loan(loan)
    assert result.ok is True
    assert loan.renewal_count == 1


def test_renew_loan_blocked_at_max(item, member, librarian):
    loan = create_loan(item, member, librarian)
    assert renew_loan(loan).ok is True
    assert renew_loan(loan).ok is True
    assert renew_loan(loan).ok is False  # 3e refusé (max 2)


def test_renew_loan_blocked_by_reservation(item, member, other_member, librarian):
    loan = create_loan(item, member, librarian)
    create_reservation(item.record, other_member)
    assert renew_loan(loan).ok is False


# --- Livre perdu ---------------------------------------------------------
def test_declare_lost(item, member, librarian):
    loan = create_loan(item, member, librarian)
    declare_lost(loan)
    item.refresh_from_db()
    assert loan.status == LoanStatus.LOST
    assert item.status == ItemStatus.LOST


# --- Réservations --------------------------------------------------------
def test_create_reservation_pending(record, member):
    reservation = create_reservation(record, member)
    assert reservation.status == ReservationStatus.PENDING
    assert reservation.expires_at > date.today()


def test_satisfy_reservation_fifo(item, member, other_member, librarian):
    first = create_reservation(item.record, member)
    create_reservation(item.record, other_member)
    create_loan(item, member, librarian)  # consomme la réservation de `member`
    first.refresh_from_db()
    assert first.status == ReservationStatus.FULFILLED
    # un autre exemplaire revient → la 2e réservation est servie
    second_item = Item.objects.create(record=item.record)
    reservation = satisfy_reservations_for_item(second_item)
    assert reservation.member_id == other_member.pk
    second_item.refresh_from_db()
    assert second_item.status == ItemStatus.RESERVED_FOR_PICKUP


def test_return_satisfies_waiting_reservation(item, member, other_member, librarian):
    create_loan(item, member, librarian)
    create_reservation(item.record, other_member)
    result = return_item(item)
    item.refresh_from_db()
    assert item.status == ItemStatus.RESERVED_FOR_PICKUP
    assert result.reservation.member_id == other_member.pk


def test_cancel_ready_reservation_frees_item(item, member, librarian):
    create_loan(item, member, librarian)
    other_reservation = create_reservation(item.record, member)
    return_item(item)  # met de côté pour `member`
    other_reservation.refresh_from_db()
    cancel_reservation(other_reservation)
    item.refresh_from_db()
    assert item.status == ItemStatus.AVAILABLE


def test_expire_stale_reservations(record, member):
    stale = create_reservation(record, member)
    Reservation.objects.filter(pk=stale.pk).update(
        expires_at=date.today() - timedelta(days=1)
    )
    result = expire_stale_reservations()
    stale.refresh_from_db()
    assert stale.status == ReservationStatus.EXPIRED
    assert result["pending_expired"] == 1
