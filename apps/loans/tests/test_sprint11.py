"""Tests Sprint 11 — FEAT-034 + FEAT-035."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.catalog.models import ItemStatus
from apps.core.models import Setting
from apps.loans.models import Reservation, ReservationStatus
from apps.loans.services import (
    compute_due_date,
    create_loan,
    create_reservation,
    pickup_expiration_for,
    reservations_due_soon,
    return_item,
    satisfy_reservations_for_item,
)
from apps.members.models import MemberCategory

pytestmark = pytest.mark.django_db


# --- FEAT-035 : durée de prêt paramétrable globalement -------------------
def test_compute_due_date_falls_back_to_setting_when_no_category_duration(record, member):
    """Si ni la catégorie de document ni la catégorie membre n'ont de durée
    explicite (0 = absente), le Setting `default_loan_days` est utilisé."""
    member.category.default_loan_duration_days = 0
    member.category.save()
    Setting.set("default_loan_days", 14)

    due = compute_due_date(member, record, today=date(2026, 5, 1))
    assert due == date(2026, 5, 15)


def test_compute_due_date_constant_fallback_when_no_setting(record, member):
    """Si aucun Setting et aucune catégorie n'a de durée, fallback constante 21."""
    member.category.default_loan_duration_days = 0
    member.category.save()
    Setting.objects.filter(pk="default_loan_days").delete()

    due = compute_due_date(member, record, today=date(2026, 5, 1))
    assert due == date(2026, 5, 22)


def test_member_category_duration_takes_priority_over_setting(record, member):
    Setting.set("default_loan_days", 7)
    member.category.default_loan_duration_days = 30
    member.category.save()

    due = compute_due_date(member, record, today=date(2026, 5, 1))
    assert due == date(2026, 5, 31)


# --- FEAT-034 : helpers de réservation ---------------------------------
def test_pickup_expiration_for_pending_reservation_returns_none(record, member):
    res = create_reservation(record, member)
    assert pickup_expiration_for(res) is None


def test_pickup_expiration_for_ready_uses_setting(item, member, librarian, other_member):
    Setting.set("pickup_hold_days", 5)
    loan = create_loan(item, member, librarian)
    reservation = create_reservation(item.record, other_member)
    return_item(item, librarian)
    reservation.refresh_from_db()
    expected = reservation.ready_since + timedelta(days=5)
    assert pickup_expiration_for(reservation) == expected


def test_reservations_due_soon_finds_expiring(item, member, librarian, other_member):
    Setting.set("pickup_hold_days", 5)
    create_loan(item, member, librarian)
    create_reservation(item.record, other_member)
    return_item(item, librarian)
    res = Reservation.objects.get(member=other_member)
    res.ready_since = date.today() - timedelta(days=4)  # expire dans 1 jour
    res.save(update_fields=["ready_since"])

    due = reservations_due_soon(within_days=2)
    assert len(due) == 1
    entry = due[0]
    assert entry["reservation"].pk == res.pk
    assert entry["days_left"] == 1
    assert entry["is_overdue"] is False


def test_reservations_due_soon_marks_overdue(item, member, librarian, other_member):
    Setting.set("pickup_hold_days", 5)
    create_loan(item, member, librarian)
    create_reservation(item.record, other_member)
    return_item(item, librarian)
    res = Reservation.objects.get(member=other_member)
    res.ready_since = date.today() - timedelta(days=8)  # 3 jours de retard
    res.save(update_fields=["ready_since"])

    due = reservations_due_soon(within_days=2)
    assert len(due) == 1
    entry = due[0]
    assert entry["is_overdue"] is True
    assert entry["days_overdue"] == 3


def test_reservations_due_soon_ignores_pending(record, member):
    create_reservation(record, member)  # status=PENDING
    assert reservations_due_soon(within_days=2) == []


# --- FEAT-036 : flag notified_at ---------------------------------------
def test_mark_reservation_notified_sets_timestamp(record, member):
    from apps.loans.services import mark_reservation_notified

    res = create_reservation(record, member)
    assert res.notified_at is None
    assert mark_reservation_notified(res) is True
    res.refresh_from_db()
    assert res.notified_at is not None


def test_mark_reservation_notified_idempotent(record, member):
    from apps.loans.services import mark_reservation_notified

    res = create_reservation(record, member)
    mark_reservation_notified(res)
    first = res.notified_at
    assert mark_reservation_notified(res) is False
    res.refresh_from_db()
    assert res.notified_at == first  # pas écrasé


def test_reservation_notify_view(client, librarian, item, member, other_member):
    """POST /reservations/<pk>/notify/ coche notified_at."""
    create_loan(item, member, librarian)
    create_reservation(item.record, other_member)
    return_item(item, librarian)
    res = Reservation.objects.get(member=other_member)
    assert res.status == ReservationStatus.READY_FOR_PICKUP
    client.force_login(librarian)
    resp = client.post(f"/fr/loans/reservations/{res.pk}/notify/")
    assert resp.status_code == 302
    res.refresh_from_db()
    assert res.notified_at is not None


def test_dashboard_shows_notifications_pending(client, librarian, item, member, other_member):
    """FEAT-036 : le dashboard affiche le cadre quand une réservation est
    prête sans avoir été notifiée."""
    create_loan(item, member, librarian)
    create_reservation(item.record, other_member)
    return_item(item, librarian)
    client.force_login(librarian)
    resp = client.get("/fr/")
    body = resp.content.decode()
    assert "Notifications" in body
    assert other_member.full_name in body
