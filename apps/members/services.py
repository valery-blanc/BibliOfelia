"""Logique métier usagers : remplacement de carte, renouvellement,
expiration. SPEC §6.2.
"""
from __future__ import annotations

from datetime import date, timedelta

from dateutil.relativedelta import relativedelta

from apps.core.ean import build_ean13
from apps.core.models import Setting

from .models import MEMBER_EAN13_PREFIX, Member, MemberStatus

# Les cartes initiales utilisent une séquence = pk (petits entiers). Les cartes
# de remplacement puisent dans une plage haute dédiée pour éviter toute
# collision (SPEC §6.2 — remplacement de carte).
_REPLACEMENT_SEQ_KEY = "next_replacement_card_seq"
_REPLACEMENT_SEQ_START = 900_000_000

EXPIRY_WARNING_DAYS = 30


def replace_card(member: Member) -> str:
    """Génère un nouveau numéro de carte, archive l'ancien. Retourne le neuf."""
    seq = int(Setting.get(_REPLACEMENT_SEQ_KEY, _REPLACEMENT_SEQ_START))
    new_number = build_ean13(MEMBER_EAN13_PREFIX, seq)
    Setting.set(
        _REPLACEMENT_SEQ_KEY,
        seq + 1,
        description="Compteur de séquence des cartes de remplacement.",
    )
    member.replaces_card_number = member.card_number
    member.card_number = new_number
    member.save(update_fields=["card_number", "replaces_card_number"])
    return new_number


def renew_card(member: Member, *, user=None, invoice: bool = True):
    """Pose `expiration_date` à aujourd'hui + durée de la catégorie.

    Ancrer sur l'ancienne date empilait les années (BUG-041). Ancrer sur
    aujourd'hui : un second clic le même jour ne change rien. La facture
    de cotisation (FEAT-084) n'est émise que si la date change vraiment.

    Renvoie `(nouvelle_date, facture)`.
    """
    months = member.category.card_validity_months or 12
    new_date = date.today() + relativedelta(months=months)
    date_changed = member.expiration_date != new_date
    member.expiration_date = new_date
    if member.status == MemberStatus.EXPIRED:
        member.status = MemberStatus.ACTIVE
    member.save(update_fields=["expiration_date", "status"])
    membership_invoice = None
    if invoice and date_changed:
        from apps.finance.services import create_membership_invoice

        membership_invoice = create_membership_invoice(member, user=user)
    return member.expiration_date, membership_invoice


def days_until_expiration(member: Member) -> int | None:
    if member.expiration_date is None:
        return None
    return (member.expiration_date - date.today()).days


def is_expiring_soon(member: Member) -> bool:
    days = days_until_expiration(member)
    return days is not None and 0 <= days <= EXPIRY_WARNING_DAYS


def mark_expired_members() -> int:
    """Passe en statut `expired` les cartes échues. Tâche django-q2 quotidienne
    (SPEC §6.2). Retourne le nombre de cartes mises à jour."""
    return Member.objects.filter(
        status=MemberStatus.ACTIVE,
        expiration_date__lt=date.today(),
    ).update(status=MemberStatus.EXPIRED)


def card_expiry_anchor() -> date:
    """Petit utilitaire de test : date d'expiration limite déjà dépassée."""
    return date.today() - timedelta(days=1)
