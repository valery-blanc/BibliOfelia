"""Tests FEAT-026 — Suppression en masse de notices. Sprint 9."""
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
def member():
    cat = MemberCategory.objects.create(code="AD", name="Adulte")
    return Member.objects.create(
        first_name="X", last_name="Y", category=cat
    )


def _make_record(title="T", with_item=True):
    rec = BibliographicRecord.objects.create(title=title)
    item = None
    if with_item:
        item = Item.objects.create(record=rec)
    return rec, item


def test_confirm_requires_superadmin(client, librarian):
    rec, _ = _make_record()
    client.force_login(librarian)
    resp = client.post(
        "/fr/catalog/bulk-delete/", {"ids": [str(rec.pk)]}
    )
    assert resp.status_code == 403


def test_confirm_renders_summaries(client, superadmin):
    rec1, _ = _make_record("Alpha")
    rec2, _ = _make_record("Beta")
    client.force_login(superadmin)
    resp = client.post(
        "/fr/catalog/bulk-delete/",
        {"ids": [str(rec1.pk), str(rec2.pk)]},
    )
    assert resp.status_code == 200
    assert b"Alpha" in resp.content
    assert b"Beta" in resp.content


def test_apply_deletes_all_selected(client, superadmin):
    rec1, _ = _make_record("A")
    rec2, _ = _make_record("B")
    client.force_login(superadmin)
    resp = client.post(
        "/fr/catalog/bulk-delete/apply/",
        {"ids": [str(rec1.pk), str(rec2.pk)]},
    )
    assert resp.status_code == 302
    assert BibliographicRecord.objects.count() == 0


def test_apply_marks_active_loans_as_lost(client, superadmin, member):
    rec, item = _make_record()
    item.status = ItemStatus.ON_LOAN
    item.save()
    Loan.objects.create(
        item=item, member=member,
        due_date=date.today() + timedelta(days=7),
        status=LoanStatus.ACTIVE,
    )
    client.force_login(superadmin)
    client.post(
        "/fr/catalog/bulk-delete/apply/", {"ids": [str(rec.pk)]}
    )
    assert not BibliographicRecord.objects.filter(pk=rec.pk).exists()
    # Items et loans cascadent
    assert Item.objects.count() == 0
    assert Loan.objects.count() == 0


def test_apply_cancels_active_reservations(client, superadmin, member):
    rec, _ = _make_record()
    res = Reservation.objects.create(
        record=rec, member=member,
        expires_at=date.today() + timedelta(days=7),
        status=ReservationStatus.PENDING,
    )
    client.force_login(superadmin)
    client.post(
        "/fr/catalog/bulk-delete/apply/", {"ids": [str(rec.pk)]}
    )
    # Reservation.record = CASCADE, donc supprimée
    assert not Reservation.objects.filter(pk=res.pk).exists()


def test_apply_empty_selection_noop(client, superadmin):
    _make_record()
    client.force_login(superadmin)
    resp = client.post("/fr/catalog/bulk-delete/apply/", {"ids": []})
    assert resp.status_code == 302
    assert BibliographicRecord.objects.count() == 1
