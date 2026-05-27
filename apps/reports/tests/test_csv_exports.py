"""Tests FEAT-040 — exports CSV catalogue + prêts/résa en cours + inactifs."""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role
from apps.catalog.models import (
    Author,
    BibliographicRecord,
    Item,
    Location,
    Tag,
)
from apps.loans.models import Loan, LoanStatus, Reservation, ReservationStatus
from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="bib", password="x", role=Role.LIBRARIAN
    )


@pytest.fixture
def client_librarian(client, librarian):
    client.force_login(librarian)
    return client


@pytest.fixture
def mcat(db):
    return MemberCategory.objects.create(
        code="AD", name="Adulte", max_concurrent_loans=5, default_loan_duration_days=21
    )


@pytest.fixture
def member(mcat):
    return Member.objects.create(first_name="Ada", last_name="Lovelace", category=mcat)


@pytest.fixture
def record(db):
    rec = BibliographicRecord.objects.create(
        title="Fondation",
        subtitle="Tome 1",
        publisher="Denoël",
        publication_year=1951,
        language="fr",
        isbn_13="9782070361212",
        document_type="book",
    )
    a = Author.objects.create(full_name="Isaac Asimov")
    rec.authors.add(a)
    t = Tag.objects.create(name="SF")
    rec.tags.add(t)
    return rec


@pytest.fixture
def item(record):
    loc = Location.objects.create(code="A1")
    return Item.objects.create(record=record, location=loc)


def _parse_csv(response) -> list[list[str]]:
    content = response.content.decode("utf-8")
    return list(csv.reader(io.StringIO(content)))


# ─── catalog_csv ─────────────────────────────────────────────────────────


def test_catalog_csv_returns_one_line_per_item(client_librarian, item):
    Item.objects.create(record=item.record)  # 2e exemplaire
    resp = client_librarian.get(reverse("reports:catalog_csv"))
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/csv")
    rows = _parse_csv(resp)
    header, *data = rows
    assert "item_internal_id" in header
    assert "record_title" in header
    assert len(data) == 2
    assert any("Fondation" in r for r in data)
    assert any("Isaac Asimov" in r for r in data)


def test_catalog_csv_forbidden_for_anonymous(client):
    resp = client.get(reverse("reports:catalog_csv"))
    assert resp.status_code in (302, 403)


# ─── active_loans_reservations_csv ───────────────────────────────────────


def test_active_loans_reservations_csv_contains_both_sections(
    client_librarian, item, member, mcat
):
    Loan.objects.create(
        item=item, member=member, due_date=date.today() + timedelta(days=14)
    )
    other_record = BibliographicRecord.objects.create(title="Dune", document_type="book")
    Reservation.objects.create(
        record=other_record,
        member=member,
        status=ReservationStatus.PENDING,
        expires_at=date.today() + timedelta(days=7),
    )
    resp = client_librarian.get(reverse("reports:active_loans_reservations_csv"))
    assert resp.status_code == 200
    rows = _parse_csv(resp)
    header, *data = rows
    assert header[0] == "kind"
    kinds = {r[0] for r in data}
    assert kinds == {"loan", "reservation"}


def test_active_loans_csv_excludes_returned(client_librarian, item, member):
    Loan.objects.create(
        item=item,
        member=member,
        due_date=date.today() + timedelta(days=7),
        status=LoanStatus.RETURNED,
        return_date=timezone.now(),
    )
    resp = client_librarian.get(reverse("reports:active_loans_reservations_csv"))
    rows = _parse_csv(resp)
    data = rows[1:]
    assert not any(r[0] == "loan" for r in data)


# ─── inactive_members / inactive_items CSV + last_activity ──────────────


def test_inactive_members_csv_marks_never_borrowed(client_librarian, mcat):
    Member.objects.create(first_name="Test", last_name="User", category=mcat)
    resp = client_librarian.get(reverse("reports:inactive_members_csv") + "?days=30")
    assert resp.status_code == 200
    rows = _parse_csv(resp)
    assert "last_activity" in rows[0]
    assert any("Aucune activité" in r[-1] for r in rows[1:])


def test_inactive_members_csv_shows_last_loan_date(client_librarian, item, member):
    loan = Loan.objects.create(
        item=item,
        member=member,
        due_date=date.today() - timedelta(days=400),
        status=LoanStatus.RETURNED,
        return_date=timezone.now() - timedelta(days=400),
    )
    Loan.objects.filter(pk=loan.pk).update(
        loan_date=timezone.now() - timedelta(days=400)
    )
    resp = client_librarian.get(reverse("reports:inactive_members_csv") + "?days=365")
    rows = _parse_csv(resp)
    member_row = next(r for r in rows[1:] if member.card_number in r[0])
    assert member_row[-1] != "Aucune activité"


def test_inactive_items_csv_includes_last_activity_column(client_librarian, item):
    resp = client_librarian.get(reverse("reports:inactive_items_csv") + "?days=30")
    assert resp.status_code == 200
    rows = _parse_csv(resp)
    assert "last_activity" in rows[0]
