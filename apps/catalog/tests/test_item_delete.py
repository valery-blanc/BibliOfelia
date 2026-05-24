"""Tests FEAT-027 — Suppression définitive d'un exemplaire. Sprint 9."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.accounts.models import Role
from apps.catalog.models import (
    BibliographicRecord,
    Item,
    ItemStatus,
)
from apps.loans.models import (
    Loan,
    LoanStatus,
    Reservation,
    ReservationStatus,
)
from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="x", role=Role.LIBRARIAN
    )


@pytest.fixture
def readonly(django_user_model):
    return django_user_model.objects.create_user(
        username="lecteur", password="x", role=Role.READONLY
    )


@pytest.fixture
def category():
    return MemberCategory.objects.create(code="AD", name="Adulte")


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Marie", last_name="Curie", category=category
    )


@pytest.fixture
def record():
    return BibliographicRecord.objects.create(title="Test")


@pytest.fixture
def item(record):
    return Item.objects.create(record=record)


def test_delete_available_item(client, librarian, item):
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/items/{item.pk}/delete/")
    assert resp.status_code == 302
    assert not Item.objects.filter(pk=item.pk).exists()


def test_delete_on_loan_marks_loan_lost_then_deletes(
    client, librarian, item, member
):
    item.status = ItemStatus.ON_LOAN
    item.save()
    loan = Loan.objects.create(
        item=item, member=member,
        due_date=date.today() + timedelta(days=7),
        status=LoanStatus.ACTIVE,
    )
    client.force_login(librarian)
    client.post(f"/fr/catalog/items/{item.pk}/delete/")
    assert not Item.objects.filter(pk=item.pk).exists()
    assert not Loan.objects.filter(pk=loan.pk).exists()


def test_delete_reserved_cancels_reservation(
    client, librarian, item, record, member
):
    item.status = ItemStatus.RESERVED_FOR_PICKUP
    item.save()
    res = Reservation.objects.create(
        record=record, member=member,
        expires_at=date.today() + timedelta(days=7),
        fulfilled_by_item=item,
        status=ReservationStatus.READY_FOR_PICKUP,
    )
    client.force_login(librarian)
    client.post(f"/fr/catalog/items/{item.pk}/delete/")
    res.refresh_from_db()
    assert res.status == ReservationStatus.CANCELLED
    assert not Item.objects.filter(pk=item.pk).exists()


def test_delete_with_past_loans_cascades(
    client, librarian, item, member
):
    Loan.objects.create(
        item=item, member=member,
        due_date=date.today() - timedelta(days=30),
        status=LoanStatus.RETURNED,
    )
    Loan.objects.create(
        item=item, member=member,
        due_date=date.today() - timedelta(days=10),
        status=LoanStatus.RETURNED,
    )
    client.force_login(librarian)
    client.post(f"/fr/catalog/items/{item.pk}/delete/")
    assert not Item.objects.filter(pk=item.pk).exists()
    assert Loan.objects.count() == 0


def test_delete_requires_write_role(client, readonly, item):
    client.force_login(readonly)
    resp = client.post(f"/fr/catalog/items/{item.pk}/delete/")
    assert resp.status_code == 403
