"""Facturation, encaissement et compte de l'usager. FEAT-084."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.core.models import Setting
from apps.finance import services
from apps.finance.models import (
    CashDirection,
    CashMovement,
    FeeKind,
    Invoice,
    InvoiceStatus,
    PaymentMethod,
)
from apps.finance.money import format_amount

pytestmark = pytest.mark.django_db


def _invoice(member, amount="10.00", kind=FeeKind.FINE, **kwargs):
    return services.create_invoice(
        member,
        [{"kind": kind, "label": "Livre abîmé", "amount": Decimal(amount)}],
        **kwargs,
    )


# ----------------------------------------------------------------------
# Numérotation
# ----------------------------------------------------------------------
def test_invoice_numbers_are_sequential_per_year(member):
    first = _invoice(member, issue_date=date(2026, 3, 1))
    second = _invoice(member, issue_date=date(2026, 7, 1))
    assert first.number == "F-2026-0001"
    assert second.number == "F-2026-0002"


def test_invoice_sequence_restarts_each_year(member):
    _invoice(member, issue_date=date(2026, 12, 31))
    next_year = _invoice(member, issue_date=date(2027, 1, 2))
    assert next_year.number == "F-2027-0001"


def test_cancelled_invoice_keeps_its_number(member):
    invoice = _invoice(member)
    services.cancel_invoice(invoice, reason="Erreur de saisie")
    invoice.refresh_from_db()
    # Une facture annulée reste numérotée : un registre troué n'est plus un
    # registre.
    assert invoice.number == f"F-{date.today().year}-0001"
    assert invoice.status == InvoiceStatus.CANCELLED
    assert invoice.balance == Decimal("0")


# ----------------------------------------------------------------------
# Totaux et encaissement
# ----------------------------------------------------------------------
def test_total_is_quantity_times_amount(member):
    invoice = services.create_invoice(member, [
        {"kind": FeeKind.OTHER, "label": "Photocopies", "amount": Decimal("0.50"),
         "quantity": 8},
        {"kind": FeeKind.FINE, "label": "Retard", "amount": Decimal("5.00")},
    ])
    assert invoice.total_amount == Decimal("9.00")


def test_partial_payment_leaves_the_invoice_open(member, librarian):
    invoice = _invoice(member, "20.00")
    services.register_payment(invoice, Decimal("8.00"), user=librarian)
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.OPEN
    assert invoice.balance == Decimal("12.00")


def test_full_payment_closes_the_invoice(member, librarian):
    invoice = _invoice(member, "20.00")
    services.register_payment(invoice, Decimal("20.00"), user=librarian)
    invoice.refresh_from_db()
    assert invoice.status == InvoiceStatus.PAID
    assert invoice.balance == Decimal("0")


def test_cash_payment_creates_a_cash_movement(member, librarian):
    invoice = _invoice(member, "20.00")
    services.register_payment(invoice, Decimal("20.00"), user=librarian)
    movement = CashMovement.objects.get()
    assert movement.direction == CashDirection.IN
    assert movement.amount == Decimal("20.00")
    assert movement.payment.invoice_id == invoice.pk


def test_transfer_payment_does_not_touch_the_till(member, librarian):
    """Un virement n'entre pas dans la caisse — sinon le comptage physique
    du tiroir ne tomberait jamais juste."""
    invoice = _invoice(member, "20.00")
    services.register_payment(
        invoice, Decimal("20.00"), method=PaymentMethod.TRANSFER, user=librarian
    )
    assert CashMovement.objects.count() == 0


# ----------------------------------------------------------------------
# Cotisation automatique
# ----------------------------------------------------------------------
def test_membership_invoice_uses_the_category_fee(member, librarian):
    invoice = services.create_membership_invoice(member, user=librarian)
    assert invoice is not None
    assert invoice.total_amount == Decimal("30.00")
    assert invoice.lines.first().kind == FeeKind.MEMBERSHIP


def test_changing_to_a_free_category_cancels_unpaid_membership(
    member, paying_category, free_category, librarian
):
    """BUG-042 : Adulte 30 CHF → catégorie gratuite, plus rien à régler."""
    invoice = services.create_membership_invoice(member, user=librarian)
    assert invoice is not None
    member.category = free_category
    member.save(update_fields=["category"])
    result = services.reconcile_membership_invoices(member, user=librarian)
    invoice.refresh_from_db()
    assert invoice.status == "cancelled"
    assert result["created"] is None
    account = services.member_account(member)
    assert account.is_up_to_date
    assert "membership" not in account.by_kind


def test_changing_to_another_paying_category_reissues_the_fee(
    member, paying_category, librarian
):
    from apps.members.models import MemberCategory

    services.create_membership_invoice(member, user=librarian)
    cheaper = MemberCategory.objects.create(
        code="SEN", name="Senior", membership_fee=Decimal("15.00")
    )
    member.category = cheaper
    member.save(update_fields=["category"])
    result = services.reconcile_membership_invoices(member, user=librarian)
    assert len(result["cancelled"]) == 1
    assert result["created"].total_amount == Decimal("15.00")
    account = services.member_account(member)
    assert account.by_kind["membership"] == Decimal("15.00")


def test_paid_membership_is_not_refunded_on_category_change(
    member, free_category, librarian
):
    invoice = services.create_membership_invoice(member, user=librarian)
    services.register_payment(invoice, invoice.total_amount, user=librarian)
    member.category = free_category
    member.save(update_fields=["category"])
    result = services.reconcile_membership_invoices(member, user=librarian)
    invoice.refresh_from_db()
    assert result["cancelled"] == []
    assert invoice.status == "paid"


def test_a_fine_is_left_untouched_when_membership_is_reconciled(
    member, free_category, librarian
):
    services.create_membership_invoice(member, user=librarian)
    fine = services.create_invoice(
        member,
        [{"kind": FeeKind.FINE, "label": "Livre abîmé", "amount": Decimal("8.00")}],
        user=librarian,
    )
    member.category = free_category
    member.save(update_fields=["category"])
    services.reconcile_membership_invoices(member, user=librarian)
    fine.refresh_from_db()
    assert fine.status == "open"
    account = services.member_account(member)
    assert account.by_kind == {"fine": Decimal("8.00")}


def test_free_category_emits_nothing(free_category):
    from apps.members.models import Member

    member = Member.objects.create(
        first_name="Paul", last_name="Petit", category=free_category
    )
    assert services.create_membership_invoice(member) is None
    assert Invoice.objects.count() == 0


def test_member_creation_view_emits_the_membership_invoice(
    client, librarian, paying_category
):
    client.force_login(librarian)
    resp = client.post("/fr/members/new/", {
        "first_name": "Ada", "last_name": "Lovelace",
        "category": paying_category.pk,
        "registration_date": date.today().isoformat(),
        "family-TOTAL_FORMS": "0", "family-INITIAL_FORMS": "0",
        "family-MIN_NUM_FORMS": "0", "family-MAX_NUM_FORMS": "1000",
    })
    assert resp.status_code == 302
    invoice = Invoice.objects.get()
    assert invoice.member.last_name == "Lovelace"
    assert invoice.total_amount == Decimal("30.00")


# ----------------------------------------------------------------------
# Compte de l'usager
# ----------------------------------------------------------------------
def test_account_is_up_to_date_without_invoice(member):
    account = services.member_account(member)
    assert account.is_up_to_date
    assert not account.is_overdue


def test_account_reports_the_oldest_overdue_date(member):
    """« En retard depuis le … » doit désigner la PLUS ANCIENNE échéance."""
    old = _invoice(member, "10.00")
    Invoice.objects.filter(pk=old.pk).update(
        due_date=date.today() - timedelta(days=40)
    )
    recent = _invoice(member, "5.00")
    Invoice.objects.filter(pk=recent.pk).update(
        due_date=date.today() - timedelta(days=3)
    )
    account = services.member_account(member)
    assert account.is_overdue
    assert account.overdue_due == Decimal("15.00")
    assert account.overdue_since == date.today() - timedelta(days=40)


def test_account_details_by_kind(member):
    services.create_invoice(member, [
        {"kind": FeeKind.MEMBERSHIP, "label": "Cotisation", "amount": Decimal("30")},
        {"kind": FeeKind.FINE, "label": "Livre perdu", "amount": Decimal("12")},
    ])
    account = services.member_account(member)
    assert account.by_kind[FeeKind.MEMBERSHIP] == Decimal("30")
    assert account.by_kind[FeeKind.FINE] == Decimal("12")


def test_paid_invoice_leaves_the_account_up_to_date(member, librarian):
    invoice = _invoice(member, "10.00")
    services.register_payment(invoice, Decimal("10.00"), user=librarian)
    account = services.member_account(member)
    assert account.is_up_to_date


def test_not_yet_due_invoice_is_not_overdue(member):
    _invoice(member, "10.00")
    account = services.member_account(member)
    assert not account.is_overdue
    assert account.total_due == Decimal("10.00")
    assert account.next_due_date is not None


# ----------------------------------------------------------------------
# Caisse
# ----------------------------------------------------------------------
def test_cash_summary_separates_in_and_out(member, librarian):
    invoice = _invoice(member, "20.00")
    services.register_payment(invoice, Decimal("20.00"), user=librarian)
    CashMovement.objects.create(
        direction=CashDirection.OUT, amount=Decimal("7.50"), label="Ampoules"
    )
    summary = services.cash_summary(date.today(), date.today())
    assert summary.total_in == Decimal("20.00")
    assert summary.total_out == Decimal("7.50")
    assert summary.balance == Decimal("12.50")


def test_total_outstanding_ignores_cancelled_and_paid(member, librarian):
    open_invoice = _invoice(member, "10.00")
    paid = _invoice(member, "5.00")
    services.register_payment(paid, Decimal("5.00"), user=librarian)
    cancelled = _invoice(member, "99.00")
    services.cancel_invoice(cancelled)
    assert services.total_outstanding() == Decimal("10.00")
    assert open_invoice.balance == Decimal("10.00")


# ----------------------------------------------------------------------
# Devise
# ----------------------------------------------------------------------
def test_currency_is_per_instance():
    """Décision Val : `canaima` en bolívar, `grand-saconnex` en franc suisse."""
    Setting.set("finance_config", {"currency": "VES", "decimals": 2})
    assert format_amount(Decimal("1234.5")).endswith("VES")
    Setting.set("finance_config", {"currency": "CHF", "decimals": 2})
    assert format_amount(Decimal("1234.5")).endswith("CHF")


def test_decimals_follow_the_setting():
    Setting.set("finance_config", {"currency": "MGA", "decimals": 0})
    # Séparateur de milliers : espace fine insécable U+202F.
    assert format_amount(Decimal("1200.4"), with_currency=False) == "1 200"


def test_amounts_keep_two_decimals_in_storage(member):
    """Le réglage n'affecte que l'affichage : changer de devise ne doit pas
    effacer des centimes déjà saisis."""
    Setting.set("finance_config", {"currency": "MGA", "decimals": 0})
    invoice = _invoice(member, "12.34")
    invoice.refresh_from_db()
    assert invoice.total_amount == Decimal("12.34")


def test_default_due_date_follows_payment_terms():
    Setting.set("finance_config", {"currency": "CHF", "payment_terms_days": 14})
    assert services.default_due_date(date(2026, 1, 1)) == date(2026, 1, 15)
