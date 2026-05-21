"""Tests audit log : enregistrement automatique sur les modèles sensibles. SPEC §9.6."""
import pytest
from auditlog.models import LogEntry

from apps.accounts.models import Role, User
from apps.catalog.models import BibliographicRecord
from apps.core.models import Setting
from apps.members.models import Member, MemberCategory


@pytest.mark.django_db
class TestAuditLog:
    def test_member_creation_is_audited(self):
        cat = MemberCategory.objects.create(code="X", name="X")
        m = Member.objects.create(first_name="J", last_name="T", category=cat)
        entries = LogEntry.objects.get_for_object(m)
        assert entries.filter(action=LogEntry.Action.CREATE).exists()

    def test_bibliographic_record_update_is_audited(self):
        r = BibliographicRecord.objects.create(title="Avant")
        r.title = "Après"
        r.save()
        entries = LogEntry.objects.get_for_object(r)
        assert entries.filter(action=LogEntry.Action.UPDATE).exists()

    def test_setting_change_is_audited(self):
        Setting.set("test_key", "value1")
        Setting.set("test_key", "value2")
        s = Setting.objects.get(pk="test_key")
        entries = LogEntry.objects.get_for_object(s)
        # Au moins 1 CREATE (premier set) + 1 UPDATE (deuxième set)
        assert entries.filter(action=LogEntry.Action.CREATE).exists()
        assert entries.filter(action=LogEntry.Action.UPDATE).exists()

    def test_user_creation_is_audited(self):
        u = User.objects.create_user(username="audited", password="x", role=Role.LIBRARIAN)
        entries = LogEntry.objects.get_for_object(u)
        assert entries.filter(action=LogEntry.Action.CREATE).exists()
