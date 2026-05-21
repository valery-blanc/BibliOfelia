"""Définition des permissions Django par rôle. SPEC §9.2.

Mapping `Role → [(app_label, codename), ...]` consommé par la commande
`setup_roles` qui crée/met à jour les `Group` Django et assigne les permissions
correspondantes.

`superadmin` n'a pas de permissions explicites : Django bypasse `has_perm()`
quand `is_superuser=True`. Le groupe est tout de même créé pour cohérence.
"""
from __future__ import annotations

from .models import Role


def _crud(app_label: str, *models: str) -> list[tuple[str, str]]:
    """Toutes les perms (add, change, delete, view) pour les modèles donnés."""
    return [
        (app_label, f"{action}_{m}")
        for m in models
        for action in ("add", "change", "delete", "view")
    ]


def _cv(app_label: str, *models: str) -> list[tuple[str, str]]:
    """add, change, view (pas de delete — pour préserver l'historique)."""
    return [
        (app_label, f"{action}_{m}")
        for m in models
        for action in ("add", "change", "view")
    ]


def _view(app_label: str, *models: str) -> list[tuple[str, str]]:
    return [(app_label, f"view_{m}") for m in models]


_CATALOG_MODELS = ("author", "category", "tag", "location", "bibliographicrecord", "item")
_MEMBERS_MODELS = ("membercategory", "member")
_LOANS_MODELS = ("loan", "inhouseconsultation", "reservation")


ROLE_PERMS: dict[str, list[tuple[str, str]]] = {
    # Superadmin : permissions vides — is_superuser=True bypasse les checks
    Role.SUPERADMIN: [],
    # Librarian : CRUD sur catalog/members/loans (sans delete sur les modèles
    # qui portent l'historique : BibliographicRecord, Member, Loan).
    # Pas d'accès Setting/User/auditlog.
    Role.LIBRARIAN: [
        *_crud("catalog", "author", "category", "tag", "location", "item"),
        *_cv("catalog", "bibliographicrecord"),
        *_cv("members", "member"),
        *_view("members", "membercategory"),
        *_cv("loans", *_LOANS_MODELS),
    ],
    # Contributor API (OfeliaScan) : ajoute des notices et exemplaires depuis le mobile,
    # peut lire mais pas modifier ni supprimer.
    Role.CONTRIBUTOR_API: [
        ("catalog", "add_bibliographicrecord"),
        ("catalog", "view_bibliographicrecord"),
        ("catalog", "add_item"),
        ("catalog", "view_item"),
        ("catalog", "add_author"),
        ("catalog", "view_author"),
        ("catalog", "view_category"),
        ("catalog", "view_tag"),
        ("catalog", "view_location"),
    ],
    # Readonly : lecture seule sur tout le domaine, rien sur Setting/User.
    Role.READONLY: [
        *_view("catalog", *_CATALOG_MODELS),
        *_view("members", *_MEMBERS_MODELS),
        *_view("loans", *_LOANS_MODELS),
    ],
}
