"""Bouclement de la journée. FEAT-086."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from apps.accounts.models import Role
from apps.closing import services
from apps.closing.models import ActivityEntry, ActivityType, DayClosing
from apps.core.models import Setting
from apps.finance import services as finance_services
from apps.finance.models import FeeKind, Invoice, OutboundEmail
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
def member():
    category = MemberCategory.objects.create(code="AD", name="Adulte")
    return Member.objects.create(
        first_name="Marie", last_name="Curie", category=category,
        email="marie@example.org",
    )


def test_closing_page_renders(client, librarian):
    client.force_login(librarian)
    resp = client.get("/fr/closing/")
    assert resp.status_code == 200


def test_one_closing_per_day_and_per_user(client, librarian):
    """Un employé qui finit à midi boucle, un autre reboucle le soir."""
    client.force_login(librarian)
    client.get("/fr/closing/")
    client.get("/fr/closing/")
    assert DayClosing.objects.filter(user=librarian, closing_date=date.today()).count() == 1


def test_closing_marks_activities_done(client, librarian):
    activity = ActivityType.objects.create(label="Accueil")
    ActivityEntry.objects.create(
        user=librarian, activity_type=activity, minutes=45
    )
    client.force_login(librarian)
    client.get("/fr/closing/")
    assert DayClosing.objects.get(user=librarian).activities_done is True


def test_backup_step_records_its_result(client, librarian, monkeypatch, tmp_path):
    from apps.tasks import backup as backup_module

    class _Result:
        status = "ok"
        db_path = str(tmp_path / "db.sqlite3")
        error = ""

    monkeypatch.setattr(backup_module, "run_backup", lambda **kw: _Result())
    client.force_login(librarian)
    resp = client.post("/fr/closing/", {"step": "backup"})
    assert resp.status_code == 302
    closing = DayClosing.objects.get(user=librarian)
    assert closing.backup_status == "ok"


def test_email_step_queues_when_offline(client, librarian, member, monkeypatch):
    """Demande explicite de Val : hors ligne, rien ne se perd."""
    Setting.set("is_box", True)
    Setting.set("email_config", {"enabled": True, "host": "smtp.invalid"})
    monkeypatch.setattr(finance_services, "is_online", lambda force=False: False)
    finance_services.create_invoice(member, [
        {"kind": FeeKind.MEMBERSHIP, "label": "Cotisation", "amount": Decimal("30")},
    ])
    client.force_login(librarian)
    client.post("/fr/closing/", {"step": "emails"})
    assert OutboundEmail.objects.count() == 1
    closing = DayClosing.objects.get(user=librarian)
    assert closing.emails_queued == 1
    assert closing.emails_sent == 0


def test_hosted_closing_does_not_talk_about_the_box(client, librarian):
    """BUG-043 : Grand-Saconnex n'est pas la Box."""
    Setting.set("is_box", False)
    Setting.set("email_config", {"enabled": False, "host": ""})
    client.force_login(librarian)
    body = client.get("/fr/closing/").content.decode()
    assert "La Box n'est pas en ligne" not in body
    assert "Mettre en file d'attente" not in body
    assert "Envoyer maintenant" in body
    assert "Email non configuré" in body


def test_box_offline_closing_mentions_the_phone(client, librarian, monkeypatch):
    Setting.set("is_box", True)
    Setting.set("email_config", {"enabled": True, "host": "smtp.invalid"})
    monkeypatch.setattr(finance_services, "is_online", lambda force=False: False)
    client.force_login(librarian)
    body = client.get("/fr/closing/").content.decode()
    assert "Hors ligne" in body
    assert "téléphone" in body
    assert "Mettre en file d'attente" in body


def test_email_step_lists_reminders_due(client, librarian, member, monkeypatch):
    monkeypatch.setattr(finance_services, "is_online", lambda force=False: False)
    invoice = finance_services.create_invoice(member, [
        {"kind": FeeKind.FINE, "label": "Amende", "amount": Decimal("5")},
    ])
    Invoice.objects.filter(pk=invoice.pk).update(
        due_date=date.today() - timedelta(days=5),
        emailed_at=None,
    )
    client.force_login(librarian)
    resp = client.get("/fr/closing/")
    assert resp.status_code == 200
    assert invoice.number.encode() in resp.content


# ----------------------------------------------------------------------
# Extinction (arbitrage Val : seulement sur la Box)
# ----------------------------------------------------------------------
def test_shutdown_step_hidden_on_a_hosted_instance(client, superadmin):
    Setting.set("is_box", False)
    client.force_login(superadmin)
    resp = client.get("/fr/closing/")
    assert "Éteindre la Box".encode() not in resp.content


def test_shutdown_step_visible_on_the_box(client, superadmin):
    Setting.set("is_box", True)
    client.force_login(superadmin)
    resp = client.get("/fr/closing/")
    assert "Éteindre la Box".encode() in resp.content


def test_shutdown_requires_superadmin(client, librarian, settings, tmp_path):
    Setting.set("is_box", True)
    settings.BOX_SHUTDOWN_FLAG = str(tmp_path / "shutdown.request")
    client.force_login(librarian)
    client.post("/fr/closing/", {"step": "shutdown"})
    assert not (tmp_path / "shutdown.request").exists()


def test_shutdown_writes_the_flag_file(client, superadmin, settings, tmp_path):
    Setting.set("is_box", True)
    flag = tmp_path / "shutdown.request"
    settings.BOX_SHUTDOWN_FLAG = str(flag)
    client.force_login(superadmin)
    client.post("/fr/closing/", {"step": "shutdown"})
    assert flag.exists()
    assert flag.read_text(encoding="utf-8")
    assert DayClosing.objects.get(user=superadmin).shutdown_requested is True


def test_shutdown_refused_off_the_box(client, superadmin, settings, tmp_path):
    Setting.set("is_box", False)
    flag = tmp_path / "shutdown.request"
    settings.BOX_SHUTDOWN_FLAG = str(flag)
    client.force_login(superadmin)
    client.post("/fr/closing/", {"step": "shutdown"})
    assert not flag.exists()


def test_is_box_defaults_to_false():
    assert services.is_box() is False
