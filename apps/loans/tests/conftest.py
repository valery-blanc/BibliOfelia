"""Fixtures partagées des tests de l'app loans."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item
from apps.members.models import Member, MemberCategory


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def category(db):
    return MemberCategory.objects.create(
        code="AD", name="Adulte", max_concurrent_loans=3, default_loan_duration_days=21
    )


@pytest.fixture
def member(category):
    return Member.objects.create(
        first_name="Ada", last_name="Lovelace", category=category
    )


@pytest.fixture
def other_member(category):
    return Member.objects.create(
        first_name="Grace", last_name="Hopper", category=category
    )


@pytest.fixture
def record(db):
    return BibliographicRecord.objects.create(title="Fondation", document_type="book")


@pytest.fixture
def item(record):
    return Item.objects.create(record=record)
