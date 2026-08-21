"""Tests FEAT-028 (toggle active) + FEAT-029 (delete member). Sprint 9."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from apps.accounts.models import Role
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    Item,
    ItemStatus,
)
from apps.loans.models import (
    InHouseConsultation,
    Loan,
    LoanStatus,
    Reservation,
    ReservationStatus,
)
from apps.members.models import Member, MemberCategory, MemberStatus

pytestmark = pytest.mark.django_db


@pytest.fixture
def superadmin(django_user_model):
    return django_user_model.objects.create_user(
        username="admin", password="x", role=Role.SUPERADMIN, is_superuser=True
    )


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
    return MemberCategory.objects.create(
        code="AD", name="Adulte", card_validity_months=12
    )


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Marie", last_name="Curie", category=category
    )


@pytest.fixture
def record_with_item():
    record = BibliographicRecord.objects.create(title="Test")
    item = Item.objects.create(record=record)
    return record, item


# ------------------------------ FEAT-028 ------------------------------

def test_toggle_active_to_suspended(client, librarian, member):
    client.force_login(librarian)
    resp = client.post(f"/fr/members/{member.pk}/toggle-active/")
    assert resp.status_code == 302
    member.refresh_from_db()
    assert member.status == MemberStatus.SUSPENDED


def test_toggle_suspended_to_active(client, librarian, member):
    member.status = MemberStatus.SUSPENDED
    member.save()
    client.force_login(librarian)
    client.post(f"/fr/members/{member.pk}/toggle-active/")
    member.refresh_from_db()
    assert member.status == MemberStatus.ACTIVE


def test_toggle_expired_renews_expiration(client, librarian, member):
    member.status = MemberStatus.EXPIRED
    member.expiration_date = date.today() - timedelta(days=10)
    member.save()
    client.force_login(librarian)
    client.post(f"/fr/members/{member.pk}/toggle-active/")
    member.refresh_from_db()
    assert member.status == MemberStatus.ACTIVE
    assert member.expiration_date > date.today()


def test_toggle_requires_write_role(client, readonly, member):
    client.force_login(readonly)
    resp = client.post(f"/fr/members/{member.pk}/toggle-active/")
    assert resp.status_code == 403


def test_suspended_blocks_new_loan(member, record_with_item, librarian):
    from apps.loans.services import check_item_loanable
    _record, item = record_with_item
    member.status = MemberStatus.SUSPENDED
    member.save()
    check = check_item_loanable(item, member)
    assert not check.ok
    assert any("Suspendu" in e or "Usager" in e for e in check.errors)


# ------------------------------ FEAT-029 ------------------------------

def test_delete_requires_superadmin(client, librarian, member):
    client.force_login(librarian)
    resp = client.get(f"/fr/members/{member.pk}/delete/")
    assert resp.status_code == 403


def test_delete_simple_member(client, superadmin, member):
    client.force_login(superadmin)
    resp = client.post(f"/fr/members/{member.pk}/delete/")
    assert resp.status_code == 302
    assert not Member.objects.filter(pk=member.pk).exists()


def test_delete_confirms_via_get(client, superadmin, member):
    client.force_login(superadmin)
    resp = client.get(f"/fr/members/{member.pk}/delete/")
    assert resp.status_code == 200
    assert b"Curie" in resp.content


def test_delete_with_active_loans_force_returns(
    client, superadmin, member, record_with_item
):
    _record, item = record_with_item
    item.status = ItemStatus.ON_LOAN
    item.save()
    loan = Loan.objects.create(
        item=item, member=member, due_date=date.today() + timedelta(days=7),
        status=LoanStatus.ACTIVE,
    )
    client.force_login(superadmin)
    client.post(f"/fr/members/{member.pk}/delete/")
    assert not Member.objects.filter(pk=member.pk).exists()
    item.refresh_from_db()
    assert item.status == ItemStatus.AVAILABLE
    assert not Loan.objects.filter(pk=loan.pk).exists()


def test_delete_cancels_active_reservations(
    client, superadmin, member, record_with_item
):
    record, _item = record_with_item
    Reservation.objects.create(
        record=record, member=member,
        expires_at=date.today() + timedelta(days=7),
        status=ReservationStatus.PENDING,
    )
    client.force_login(superadmin)
    client.post(f"/fr/members/{member.pk}/delete/")
    assert not Reservation.objects.filter(member__isnull=False).exists()


def test_delete_removes_the_family(client, superadmin, member, category):
    """FEAT-072 : les fiches de famille ne survivent pas à l'usager (CASCADE)."""
    from apps.members.models import MemberFamilyMember

    MemberFamilyMember.objects.create(member=member, first_name="Pierre", birth_year=2019)
    client.force_login(superadmin)
    client.post(f"/fr/members/{member.pk}/delete/")
    assert not MemberFamilyMember.objects.exists()


def test_delete_cascades_past_loans(
    client, superadmin, member, record_with_item
):
    _record, item = record_with_item
    Loan.objects.create(
        item=item, member=member,
        due_date=date.today() - timedelta(days=10),
        status=LoanStatus.RETURNED,
    )
    client.force_login(superadmin)
    client.post(f"/fr/members/{member.pk}/delete/")
    assert Loan.objects.count() == 0


def test_delete_cascades_consultations(
    client, superadmin, member, record_with_item
):
    _record, item = record_with_item
    InHouseConsultation.objects.create(item=item, member=member)
    client.force_login(superadmin)
    client.post(f"/fr/members/{member.pk}/delete/")
    # Consultation conservée (Item SET_NULL côté member ne s'applique pas car
    # on cascade explicitement member.consultations.delete()) — vérifions
    assert InHouseConsultation.objects.filter(member__isnull=False).count() == 0
