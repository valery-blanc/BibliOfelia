"""Tests vues prêts / retours / réservations. SPEC §6.3, §6.4."""
from __future__ import annotations

from datetime import date

import pytest

from apps.catalog.models import ItemStatus
from apps.loans.models import (
    InHouseConsultation,
    Loan,
    LoanStatus,
    Reservation,
    ReservationStatus,
)
from apps.loans.services import create_loan

pytestmark = pytest.mark.django_db


def test_lend_full_workflow(client, librarian, member, item):
    client.force_login(librarian)
    client.post("/fr/loans/lend/", {"action": "set_member", "card": member.card_number})
    assert client.session["lend_member"] == member.pk
    client.post("/fr/loans/lend/", {"action": "add_item", "ean": item.ean13})
    assert client.session["lend_basket"] == [item.pk]
    resp = client.post("/fr/loans/lend/", {"action": "validate", "notes": ""})
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.status == ItemStatus.ON_LOAN
    assert Loan.objects.filter(item=item, member=member).count() == 1


def test_lend_unknown_card_sets_no_member(client, librarian):
    client.force_login(librarian)
    client.post("/fr/loans/lend/", {"action": "set_member", "card": "0000000000000"})
    assert "lend_member" not in client.session


def test_lend_add_unavailable_item_rejected(client, librarian, member, item):
    item.status = ItemStatus.IN_REPAIR
    item.save()
    client.force_login(librarian)
    client.post("/fr/loans/lend/", {"action": "set_member", "card": member.card_number})
    client.post("/fr/loans/lend/", {"action": "add_item", "ean": item.ean13})
    assert client.session.get("lend_basket", []) == []


def test_return_view_processes_return(client, librarian, member, item):
    create_loan(item, member, librarian)
    client.force_login(librarian)
    resp = client.post("/fr/loans/return/", {"action": "add_item", "ean": item.ean13})
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.status == ItemStatus.AVAILABLE


def test_renew_loan_view(client, librarian, member, item):
    loan = create_loan(item, member, librarian)
    client.force_login(librarian)
    resp = client.post(f"/fr/loans/renew/{loan.pk}/")
    assert resp.status_code == 302
    loan.refresh_from_db()
    assert loan.renewal_count == 1


def test_mark_lost_view(client, librarian, member, item):
    loan = create_loan(item, member, librarian)
    client.force_login(librarian)
    assert client.get(f"/fr/loans/lost/{loan.pk}/").status_code == 200
    resp = client.post(f"/fr/loans/lost/{loan.pk}/")
    assert resp.status_code == 302
    loan.refresh_from_db()
    assert loan.status == LoanStatus.LOST


def test_consultation_view(client, librarian):
    client.force_login(librarian)
    resp = client.post(
        "/fr/loans/consultation/", {"count": 3, "date": date.today().isoformat()}
    )
    assert resp.status_code == 302
    assert InHouseConsultation.objects.filter(count=3).exists()


def test_reservation_create_view(client, librarian, member, record):
    client.force_login(librarian)
    resp = client.post(
        f"/fr/loans/reservations/new/{record.pk}/", {"member": member.pk}
    )
    assert resp.status_code == 302
    assert Reservation.objects.filter(record=record, member=member).exists()


def test_reservation_list_view(client, librarian):
    client.force_login(librarian)
    assert client.get("/fr/loans/reservations/").status_code == 200


def test_reservation_cancel_view(client, librarian, member, record):
    from apps.loans.services import create_reservation

    reservation = create_reservation(record, member)
    client.force_login(librarian)
    resp = client.post(f"/fr/loans/reservations/{reservation.pk}/cancel/")
    assert resp.status_code == 302
    reservation.refresh_from_db()
    assert reservation.status == ReservationStatus.CANCELLED
