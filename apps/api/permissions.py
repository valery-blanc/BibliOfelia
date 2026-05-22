"""Helpers de permission pour l'API OfeliaScan. SPEC §6.10 / FEAT-021.

Les `contributor_api` ne voient et n'agissent que sur **leurs propres
sessions** ; les librarian/superadmin voient tout. On utilise 404 (et non
403) pour les sessions des autres → pas de fuite d'existence.
"""
from __future__ import annotations

from django.shortcuts import get_object_or_404

from apps.accounts.models import Role


def _is_privileged(user) -> bool:
    return user.is_authenticated and user.role in (Role.SUPERADMIN, Role.LIBRARIAN)


def get_session_for_user(model, *, session_id, user):
    """Récupère une session (Scan ou Inventory) accessible à `user`.

    404 si la session n'existe pas ou si l'user n'a pas le droit (sauf
    librarian/superadmin qui voient tout). Le filtre porte sur le champ
    `session_id` (UUID public exposé dans l'API), pas sur `pk`.
    """
    qs = model.objects.all()
    if not _is_privileged(user):
        qs = qs.filter(created_by=user)
    return get_object_or_404(qs, session_id=session_id)
