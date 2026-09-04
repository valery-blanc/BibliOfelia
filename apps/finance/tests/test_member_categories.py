"""FEAT-089 — catégories d'usagers gérées depuis la page tarifs."""
from __future__ import annotations

from decimal import Decimal

import pytest
from django.urls import reverse

from apps.members.models import Member, MemberCategory

pytestmark = pytest.mark.django_db


def _payload(**overrides):
    data = {
        "code": "SENIOR",
        "name_fr": "Senior",
        "name_en": "Senior",
        "name_es": "Mayor",
        "name_mg": "Antitra",
        "membership_fee": "15.00",
        "card_validity_months": "12",
        "max_concurrent_loans": "4",
        "default_loan_duration_days": "21",
    }
    data.update(overrides)
    return data


def test_tariff_page_lists_categories_and_renames_the_title(
    client, superadmin, paying_category
):
    client.force_login(superadmin)
    resp = client.get(reverse("finance:tariff_list"))
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Tarifs et Catégories d'usagers" in body
    assert paying_category.code in body
    assert "Nouvelle catégorie" in body
    assert "administration des catégories d'usager" not in body.lower()


def test_librarian_cannot_manage_member_categories(client, librarian, paying_category):
    client.force_login(librarian)
    assert client.get(reverse("finance:tariff_list")).status_code == 403
    assert client.get(reverse("finance:member_category_create")).status_code == 403
    assert (
        client.get(
            reverse("finance:member_category_edit", args=[paying_category.pk])
        ).status_code
        == 403
    )


def test_create_member_category_from_the_tariff_page(client, superadmin):
    client.force_login(superadmin)
    resp = client.post(reverse("finance:member_category_create"), _payload())
    assert resp.status_code == 302
    cat = MemberCategory.objects.get(code="SENIOR")
    assert cat.name_fr == "Senior"
    assert cat.name_en == "Senior"
    assert cat.name_es == "Mayor"
    assert cat.name_mg == "Antitra"
    assert cat.name == "Senior"
    assert cat.membership_fee == Decimal("15.00")
    assert cat.max_concurrent_loans == 4
    assert cat.allowed_document_types == []


def test_create_normalizes_code_and_stores_document_types(client, superadmin):
    client.force_login(superadmin)
    resp = client.post(
        reverse("finance:member_category_create"),
        _payload(code="  ado-plus  ", allowed_document_types=["book", "comic"]),
    )
    assert resp.status_code == 302
    cat = MemberCategory.objects.get(code="ADO-PLUS")
    assert set(cat.allowed_document_types) == {"book", "comic"}


def test_code_with_spaces_is_rejected(client, superadmin):
    client.force_login(superadmin)
    resp = client.post(
        reverse("finance:member_category_create"),
        _payload(code="A B"),
    )
    assert resp.status_code == 200
    assert not MemberCategory.objects.filter(code="A B").exists()


def test_edit_membership_fee(client, superadmin, paying_category):
    client.force_login(superadmin)
    client.post(
        reverse("finance:member_category_edit", args=[paying_category.pk]),
        _payload(
            code=paying_category.code,
            name_fr="Adulte",
            membership_fee="40.00",
        ),
    )
    paying_category.refresh_from_db()
    assert paying_category.membership_fee == Decimal("40.00")
    assert paying_category.name_fr == "Adulte"


def test_cannot_delete_a_category_that_still_has_members(
    client, superadmin, member, paying_category
):
    client.force_login(superadmin)
    url = reverse("finance:member_category_delete", args=[paying_category.pk])
    resp = client.get(url)
    assert resp.status_code == 200
    assert "Réaffectez" in resp.content.decode()
    client.post(url)
    assert MemberCategory.objects.filter(pk=paying_category.pk).exists()
    assert Member.objects.filter(pk=member.pk).exists()


def test_empty_category_can_be_deleted(client, superadmin, free_category):
    client.force_login(superadmin)
    url = reverse("finance:member_category_delete", args=[free_category.pk])
    resp = client.post(url)
    assert resp.status_code == 302
    assert not MemberCategory.objects.filter(pk=free_category.pk).exists()


def test_advanced_page_uses_the_new_label(client, superadmin):
    client.force_login(superadmin)
    resp = client.get(reverse("core:advanced"))
    assert resp.status_code == 200
    assert "Tarifs et Catégories d'usagers" in resp.content.decode()
