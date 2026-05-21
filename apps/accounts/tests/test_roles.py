"""Tests rôles, groupes et permissions. SPEC §9.2."""
import pytest
from django.core.management import call_command

from apps.accounts.models import Role, User


@pytest.fixture
def roles_ready(db):
    """Crée les Groups + permissions avant chaque test."""
    call_command("setup_roles")


@pytest.mark.django_db
class TestRoleSignal:
    def test_librarian_user_gets_librarian_group(self, roles_ready):
        u = User.objects.create_user(username="alice", password="x", role=Role.LIBRARIAN)
        assert u.groups.filter(name=Role.LIBRARIAN).exists()
        assert not u.groups.filter(name=Role.SUPERADMIN).exists()
        assert u.is_staff is False

    def test_create_superuser_forces_superadmin_role_and_staff(self, roles_ready):
        u = User.objects.create_superuser(
            username="root", email="r@r.fr", password="rootRootRoot1!"
        )
        u.refresh_from_db()
        assert u.role == Role.SUPERADMIN
        assert u.is_staff is True
        assert u.is_superuser is True
        assert u.groups.filter(name=Role.SUPERADMIN).exists()

    def test_role_change_replaces_group(self, roles_ready):
        u = User.objects.create_user(username="bob", password="x", role=Role.READONLY)
        assert u.groups.filter(name=Role.READONLY).exists()
        u.role = Role.LIBRARIAN
        u.save()
        assert u.groups.filter(name=Role.LIBRARIAN).exists()
        assert not u.groups.filter(name=Role.READONLY).exists()

    def test_setup_roles_after_existing_users_syncs_them(self, db):
        # Crée un user AVANT setup_roles
        u = User.objects.create_user(username="early", password="x", role=Role.LIBRARIAN)
        assert not u.groups.exists()  # pas de Group créé encore
        call_command("setup_roles")
        u.refresh_from_db()
        assert u.groups.filter(name=Role.LIBRARIAN).exists()


@pytest.mark.django_db
class TestRolePermissions:
    def test_librarian_has_catalog_and_loans_perms(self, roles_ready):
        u = User.objects.create_user(username="lib", password="x", role=Role.LIBRARIAN)
        assert u.has_perm("catalog.add_item")
        assert u.has_perm("catalog.change_bibliographicrecord")
        assert u.has_perm("members.add_member")
        assert u.has_perm("loans.add_loan")

    def test_librarian_cannot_touch_setting_or_user(self, roles_ready):
        u = User.objects.create_user(username="lib2", password="x", role=Role.LIBRARIAN)
        assert not u.has_perm("core.change_setting")
        assert not u.has_perm("accounts.add_user")

    def test_librarian_cannot_delete_bibliographic_record(self, roles_ready):
        u = User.objects.create_user(username="lib3", password="x", role=Role.LIBRARIAN)
        assert u.has_perm("catalog.change_bibliographicrecord")
        assert not u.has_perm("catalog.delete_bibliographicrecord")

    def test_contributor_api_can_add_record_and_item_only(self, roles_ready):
        u = User.objects.create_user(username="api", password="x", role=Role.CONTRIBUTOR_API)
        assert u.has_perm("catalog.add_bibliographicrecord")
        assert u.has_perm("catalog.add_item")
        assert not u.has_perm("catalog.change_bibliographicrecord")
        assert not u.has_perm("members.add_member")
        assert not u.has_perm("loans.add_loan")

    def test_readonly_only_views(self, roles_ready):
        u = User.objects.create_user(username="ro", password="x", role=Role.READONLY)
        assert u.has_perm("catalog.view_item")
        assert u.has_perm("members.view_member")
        assert not u.has_perm("catalog.add_item")
        assert not u.has_perm("members.add_member")

    def test_superadmin_bypass(self, roles_ready):
        u = User.objects.create_superuser(
            username="sa", email="s@s.fr", password="superSuperSuper1!"
        )
        # is_superuser=True bypasse has_perm()
        assert u.has_perm("core.change_setting")
        assert u.has_perm("catalog.delete_bibliographicrecord")
