"""Écrans de caisse, PDF de facture et file d'emails. FEAT-084."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.core.models import Setting
from apps.finance import services
from apps.finance.models import (
    EmailKind,
    EmailStatus,
    FeeKind,
    Invoice,
    OutboundEmail,
)

pytestmark = pytest.mark.django_db


def _invoice(member, amount="10.00", **kwargs):
    return services.create_invoice(
        member,
        [{"kind": FeeKind.FINE, "label": "Livre abîmé", "amount": Decimal(amount)}],
        **kwargs,
    )


# ----------------------------------------------------------------------
# Écrans
# ----------------------------------------------------------------------
def test_cash_index_renders(client, librarian):
    client.force_login(librarian)
    resp = client.get("/fr/finance/")
    assert resp.status_code == 200


def test_invoice_detail_renders(client, librarian, member):
    invoice = _invoice(member)
    client.force_login(librarian)
    resp = client.get(f"/fr/finance/invoices/{invoice.pk}/")
    assert resp.status_code == 200
    assert invoice.number.encode() in resp.content


def test_readonly_cannot_record_a_payment(client, readonly, member):
    invoice = _invoice(member)
    client.force_login(readonly)
    resp = client.post(f"/fr/finance/invoices/{invoice.pk}/pay/", {
        "amount": "10.00", "method": "cash", "paid_on": date.today().isoformat(),
    })
    assert resp.status_code == 403
    invoice.refresh_from_db()
    assert invoice.amount_paid == Decimal("0")


def test_payment_view_records_and_redirects(client, librarian, member):
    invoice = _invoice(member, "10.00")
    client.force_login(librarian)
    resp = client.post(f"/fr/finance/invoices/{invoice.pk}/pay/", {
        "amount": "10.00", "method": "cash", "paid_on": date.today().isoformat(),
        "note": "",
    })
    assert resp.status_code == 302
    invoice.refresh_from_db()
    assert invoice.amount_paid == Decimal("10.00")


def test_payment_above_the_balance_is_refused(client, librarian, member):
    invoice = _invoice(member, "10.00")
    client.force_login(librarian)
    client.post(f"/fr/finance/invoices/{invoice.pk}/pay/", {
        "amount": "99.00", "method": "cash", "paid_on": date.today().isoformat(),
    })
    invoice.refresh_from_db()
    assert invoice.amount_paid == Decimal("0")


def test_paid_invoice_cannot_be_cancelled(client, librarian, member):
    invoice = _invoice(member, "10.00")
    services.register_payment(invoice, Decimal("10.00"), user=librarian)
    client.force_login(librarian)
    client.post(f"/fr/finance/invoices/{invoice.pk}/cancel/")
    invoice.refresh_from_db()
    assert invoice.status != "cancelled"


def test_fee_form_creates_a_single_line_invoice(client, librarian, member):
    client.force_login(librarian)
    resp = client.post(f"/fr/finance/members/{member.pk}/fee/fine/", {
        "label": "Couverture déchirée", "amount": "8.00",
    })
    assert resp.status_code == 302
    invoice = Invoice.objects.get()
    assert invoice.lines.first().kind == FeeKind.FINE
    assert invoice.total_amount == Decimal("8.00")


def test_invoice_creation_requires_at_least_one_line(client, librarian, member):
    client.force_login(librarian)
    resp = client.post(f"/fr/finance/members/{member.pk}/invoice/new/", {
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "note": "",
        "lines-TOTAL_FORMS": "1", "lines-INITIAL_FORMS": "0",
        "lines-MIN_NUM_FORMS": "0", "lines-MAX_NUM_FORMS": "1000",
        "lines-0-kind": "fine", "lines-0-label": "", "lines-0-amount": "",
        "lines-0-quantity": "1",
    })
    assert resp.status_code == 200
    assert Invoice.objects.count() == 0


def test_tariff_referential_is_superadmin_only(client, librarian, superadmin):
    client.force_login(librarian)
    assert client.get("/fr/finance/tariffs/").status_code == 403
    client.force_login(superadmin)
    assert client.get("/fr/finance/tariffs/").status_code == 200


def test_member_detail_shows_the_account_box(client, librarian, member):
    invoice = _invoice(member, "10.00")
    Invoice.objects.filter(pk=invoice.pk).update(
        due_date=date.today() - timedelta(days=5)
    )
    client.force_login(librarian)
    resp = client.get(f"/fr/members/{member.pk}/")
    assert resp.status_code == 200
    assert b"En retard de paiement" in resp.content


# ----------------------------------------------------------------------
# PDF
# ----------------------------------------------------------------------
def test_invoice_pdf_is_a_pdf(client, librarian, member):
    invoice = _invoice(member)
    client.force_login(librarian)
    resp = client.get(f"/fr/finance/invoices/{invoice.pk}/pdf/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"


def test_invoice_pdf_works_without_an_address(client, librarian, free_category):
    """Une fiche sans adresse ne doit pas casser la génération."""
    from apps.members.models import Member

    bare = Member.objects.create(
        first_name="Sans", last_name="Adresse", category=free_category
    )
    invoice = _invoice(bare)
    client.force_login(librarian)
    resp = client.get(f"/fr/finance/invoices/{invoice.pk}/pdf/")
    assert resp.status_code == 200
    assert resp.content[:4] == b"%PDF"


# ----------------------------------------------------------------------
# File d'emails
# ----------------------------------------------------------------------
def test_queue_skips_a_member_without_email(free_category):
    from apps.members.models import Member

    bare = Member.objects.create(
        first_name="Sans", last_name="Email", category=free_category
    )
    invoice = _invoice(bare)
    assert services.queue_invoice_email(invoice) is None
    assert OutboundEmail.objects.count() == 0


def test_reminder_only_after_more_than_one_day(member):
    invoice = _invoice(member)
    Invoice.objects.filter(pk=invoice.pk).update(due_date=date.today())
    assert services.reminders_to_send().count() == 0
    Invoice.objects.filter(pk=invoice.pk).update(
        due_date=date.today() - timedelta(days=3)
    )
    assert services.reminders_to_send().count() == 1


def test_a_reminder_is_sent_only_once(member):
    invoice = _invoice(member)
    Invoice.objects.filter(pk=invoice.pk).update(
        due_date=date.today() - timedelta(days=5)
    )
    services.queue_pending_invoice_emails()
    assert services.reminders_to_send().count() == 0
    # Le but est de prévenir, pas de harceler.
    counts = services.queue_pending_invoice_emails()
    assert counts["reminders"] == 0


def test_offline_box_keeps_the_queue(member, monkeypatch):
    """Demande explicite de Val : hors ligne, on liste sans rien perdre."""
    Setting.set("is_box", True)
    Setting.set("email_config", {"enabled": True, "host": "smtp.invalid", "port": 587})
    monkeypatch.setattr(services, "is_online", lambda force=False: False)
    invoice = _invoice(member)
    services.queue_invoice_email(invoice, kind=EmailKind.INVOICE)
    result = services.flush_outbox()
    assert result["sent"] == 0
    assert result["skipped"] == 1
    assert result["skip_reason"] == "offline"
    assert OutboundEmail.objects.get().status == EmailStatus.PENDING


def test_hosted_instance_does_not_skip_flush_as_if_the_box_were_offline(
    member, monkeypatch
):
    """BUG-043 : Grand-Saconnex n'est pas la Box. is_online faux ne doit pas
    bloquer l'envoi derrière un message « la Box n'est pas en ligne »."""
    Setting.set("is_box", False)
    Setting.set("email_config", {
        "enabled": True, "host": "smtp.example.org", "port": 587,
        "from_address": "biblio@example.org",
    })
    monkeypatch.setattr(services, "is_online", lambda force=False: False)

    class _Conn:
        def send_messages(self, messages):
            return len(messages)

    monkeypatch.setattr(
        "django.core.mail.get_connection",
        lambda **kw: _Conn(),
    )
    invoice = _invoice(member)
    services.queue_invoice_email(invoice, kind=EmailKind.REMINDER)
    result = services.flush_outbox()
    assert result["skipped"] == 0
    assert result["sent"] == 1
    assert OutboundEmail.objects.get().status == EmailStatus.SENT


def test_unconfigured_smtp_explains_itself(member):
    Setting.set("is_box", False)
    Setting.set("email_config", {"enabled": False, "host": ""})
    invoice = _invoice(member)
    services.queue_invoice_email(invoice, kind=EmailKind.INVOICE)
    result = services.flush_outbox()
    assert result["skipped"] == 1
    assert result["skip_reason"] == "not_configured"
    text = " ".join(msg for _lvl, msg in services.flush_user_messages(result))
    assert "Box" not in text
    assert "Email" in text


def test_is_online_is_false_when_email_is_disabled():
    Setting.set("email_config", {"enabled": False, "host": "smtp.example.org"})
    assert services.is_online(force=True) is False


def test_outbox_flush_is_superadmin_only(client, librarian, superadmin):
    client.force_login(librarian)
    assert client.post("/fr/finance/outbox/flush/").status_code == 403
    client.force_login(superadmin)
    resp = client.post("/fr/finance/outbox/flush/")
    assert resp.status_code == 302
    assert resp["Location"].endswith("/finance/outbox/")


def test_outbox_flush_can_return_to_the_outbox(client, superadmin):
    client.force_login(superadmin)
    resp = client.post("/fr/finance/outbox/flush/", {"next": "outbox"})
    assert resp.status_code == 302
    assert resp["Location"].endswith("/finance/outbox/")


def test_cash_screens_are_reachable_from_the_top_nav(client, librarian):
    """Signalé par Val (2026-09-01) : la caisse n'était atteignable que depuis
    l'accueil. Elle a maintenant son chip dans la barre de sections."""
    client.force_login(librarian)
    for url in ("/fr/catalog/", "/fr/members/", "/fr/closing/", "/fr/finance/"):
        html = client.get(url).content.decode("utf-8")
        assert "/fr/finance/" in html, url


def test_the_caisse_chip_is_marked_active_on_finance_screens(client, librarian, member):
    invoice = _invoice(member)
    client.force_login(librarian)
    for url in ("/fr/finance/", "/fr/finance/invoices/",
                f"/fr/finance/invoices/{invoice.pk}/", "/fr/finance/outbox/"):
        html = client.get(url).content.decode("utf-8")
        assert "chip--amber is-active" in html, url
