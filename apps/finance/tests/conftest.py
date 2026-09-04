"""Fixtures partagées des tests de caisse. FEAT-084."""
from __future__ import annotations

from decimal import Decimal

import pytest

from apps.accounts.models import Role
from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def superadmin(django_user_model):
    return django_user_model.objects.create_user(
        username="chef", password="motdepasse123", role=Role.SUPERADMIN
    )


@pytest.fixture
def readonly(django_user_model):
    return django_user_model.objects.create_user(
        username="lecteur", password="motdepasse123", role=Role.READONLY
    )


@pytest.fixture
def paying_category():
    return MemberCategory.objects.create(
        code="AD", name="Adulte", membership_fee=Decimal("30.00")
    )


@pytest.fixture
def free_category():
    return MemberCategory.objects.create(code="EN", name="Enfant")


@pytest.fixture
def member(paying_category):
    return Member.objects.create(
        first_name="Marie",
        last_name="Curie",
        category=paying_category,
        email="marie@example.org",
        address_street="12 rue des Lilas",
        address_postal_code="1218",
        address_city="Le Grand-Saconnex",
        address_country="Suisse",
    )
