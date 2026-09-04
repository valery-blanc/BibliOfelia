"""Tests logique usagers : carte, renouvellement, expiration. SPEC §6.2."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.core.ean import validate_ean13
from apps.members.models import Member, MemberCategory, MemberStatus
from apps.members.services import (
    CardStillValid,
    can_renew,
    is_expiring_soon,
    mark_expired_members,
    renew_card,
    replace_card,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def category():
    return MemberCategory.objects.create(
        code="AD", name="Adulte", card_validity_months=12
    )


def _member(category, **kwargs):
    defaults = {"first_name": "Jean", "last_name": "Dupont", "category": category}
    defaults.update(kwargs)
    return Member.objects.create(**defaults)


def test_replace_card_archives_old_number(category):
    member = _member(category)
    old = member.card_number
    new = replace_card(member)
    assert new != old
    assert member.replaces_card_number == old
    assert member.card_number == new
    assert validate_ean13(new)
    assert new.startswith("291")


def test_replace_card_numbers_are_unique(category):
    m1, m2 = _member(category), _member(category)
    assert replace_card(m1) != replace_card(m2)


def test_renew_card_extends_expiration(category):
    member = _member(category, expiration_date=date.today() - timedelta(days=5))
    member.status = MemberStatus.EXPIRED
    member.save()
    # BUG-041 : `renew_card` renvoie désormais (date, facture de cotisation).
    new_date, invoice = renew_card(member)
    assert new_date > date.today()
    assert member.status == MemberStatus.ACTIVE
    # Catégorie de test sans cotisation → aucune facture émise (FEAT-084).
    assert invoice is None


def test_renew_card_refuses_a_card_still_valid(category):
    """BUG-041 : trois clics ne doivent pas ajouter trois ans."""
    member = _member(category, expiration_date=date.today() + timedelta(days=200))
    assert can_renew(member) is False
    with pytest.raises(CardStillValid):
        renew_card(member)
    member.refresh_from_db()
    assert member.expiration_date == date.today() + timedelta(days=200)


def test_renew_card_allowed_near_expiry(category):
    member = _member(category, expiration_date=date.today() + timedelta(days=10))
    assert can_renew(member) is True
    new_date, _invoice = renew_card(member)
    assert new_date > date.today() + timedelta(days=10)


def test_renew_card_emits_membership_invoice(category):
    """FEAT-084 : la cotisation est facturée à chaque renouvellement."""
    category.membership_fee = Decimal("25.00")
    category.save(update_fields=["membership_fee"])
    member = _member(category, expiration_date=date.today() - timedelta(days=1))
    _new_date, invoice = renew_card(member)
    assert invoice is not None
    assert invoice.total_amount == Decimal("25.00")
    assert invoice.lines.count() == 1
    assert invoice.lines.first().kind == "membership"


def test_mark_expired_members(category):
    stale = _member(category, expiration_date=date.today() - timedelta(days=1))
    fresh = _member(category, expiration_date=date.today() + timedelta(days=30))
    count = mark_expired_members()
    stale.refresh_from_db()
    fresh.refresh_from_db()
    assert count == 1
    assert stale.status == MemberStatus.EXPIRED
    assert fresh.status == MemberStatus.ACTIVE


def test_is_expiring_soon(category):
    soon = _member(category, expiration_date=date.today() + timedelta(days=10))
    far = _member(category, expiration_date=date.today() + timedelta(days=90))
    assert is_expiring_soon(soon) is True
    assert is_expiring_soon(far) is False
