"""Helpers d'autorisation : décorateur vue Django + permission DRF.

SPEC §9.2.
"""
from __future__ import annotations

from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission


def require_role(*roles: str):
    """Décorateur de vue : exige user authentifié + l'un des `roles`.

    `is_superuser=True` bypasse la vérification (équivalent SUPERADMIN).
    Usage::

        @require_role(Role.LIBRARIAN, Role.SUPERADMIN)
        def my_view(request): ...
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapper(request, *args, **kwargs):
            user = request.user
            if not (user.is_superuser or getattr(user, "role", None) in roles):
                raise PermissionDenied(
                    "Rôle requis : " + ", ".join(roles)
                )
            return view_func(request, *args, **kwargs)

        return _wrapper

    return decorator


class HasRole(BasePermission):
    """Permission DRF. À déclarer via `view.required_roles = (Role.X, ...)`."""

    message = "Rôle insuffisant."

    def has_permission(self, request, view) -> bool:
        required = getattr(view, "required_roles", None)
        if not required:
            return True
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        return user.is_superuser or getattr(user, "role", None) in required
