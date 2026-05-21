"""Tests du décorateur require_role et de HasRole DRF. SPEC §9.2."""
import pytest
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory

from apps.accounts.models import Role, User
from apps.accounts.permissions import HasRole, require_role


@pytest.mark.django_db
class TestRequireRoleDecorator:
    def _make_view(self, *roles):
        @require_role(*roles)
        def view(request):
            return HttpResponse("ok")

        return view

    def test_anonymous_redirected_to_login(self):
        view = self._make_view(Role.LIBRARIAN)
        rf = RequestFactory()
        req = rf.get("/protected/")
        from django.contrib.auth.models import AnonymousUser

        req.user = AnonymousUser()
        resp = view(req)
        assert resp.status_code == 302  # login_required redirect

    def test_user_with_wrong_role_raises_permission_denied(self):
        view = self._make_view(Role.LIBRARIAN)
        rf = RequestFactory()
        req = rf.get("/protected/")
        req.user = User.objects.create_user(username="ro", password="x", role=Role.READONLY)
        with pytest.raises(PermissionDenied):
            view(req)

    def test_user_with_correct_role_passes(self):
        view = self._make_view(Role.LIBRARIAN)
        rf = RequestFactory()
        req = rf.get("/protected/")
        req.user = User.objects.create_user(username="lib", password="x", role=Role.LIBRARIAN)
        resp = view(req)
        assert resp.status_code == 200

    def test_superuser_always_passes(self):
        view = self._make_view(Role.LIBRARIAN)
        rf = RequestFactory()
        req = rf.get("/protected/")
        req.user = User.objects.create_superuser(
            username="su", email="s@s.fr", password="superSuper1!"
        )
        resp = view(req)
        assert resp.status_code == 200


@pytest.mark.django_db
class TestHasRoleDRF:
    def test_denies_anonymous(self):
        from django.contrib.auth.models import AnonymousUser

        class V:
            required_roles = (Role.LIBRARIAN,)

        req = type("R", (), {"user": AnonymousUser()})()
        assert HasRole().has_permission(req, V()) is False

    def test_denies_wrong_role(self):
        u = User.objects.create_user(username="ro", password="x", role=Role.READONLY)

        class V:
            required_roles = (Role.LIBRARIAN,)

        req = type("R", (), {"user": u})()
        assert HasRole().has_permission(req, V()) is False

    def test_allows_correct_role(self):
        u = User.objects.create_user(username="lib", password="x", role=Role.LIBRARIAN)

        class V:
            required_roles = (Role.LIBRARIAN,)

        req = type("R", (), {"user": u})()
        assert HasRole().has_permission(req, V()) is True

    def test_no_required_roles_means_open(self):
        u = User.objects.create_user(username="any", password="x", role=Role.READONLY)

        class V:
            pass

        req = type("R", (), {"user": u})()
        assert HasRole().has_permission(req, V()) is True
