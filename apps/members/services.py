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


class CardStillValid(Exception):
    """BUG-041 : renouvellement refusé, la carte est encore valable."""

    def __init__(self, expiration_date):
        self.expiration_date = expiration_date
        super().__init__(f"Carte valable jusqu'au {expiration_date}")


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


def can_renew(member: Member) -> bool:
    """BUG-041 : le renouvellement n'a de sens qu'en fin de validité.

    Le bouton ancrait la nouvelle échéance sur l'ancienne (`max(today,
    expiration_date)`) : trois clics ajoutaient trois ans, sans le moindre
    avertissement. Une carte encore valable pour plus de 30 jours ne se
    renouvelle donc plus — ni par le bouton, grisé, ni par un POST direct.
    """
    if member.expiration_date is None:
        return True
    return (member.expiration_date - date.today()).days <= EXPIRY_WARNING_DAYS


def renew_card(member: Member, *, user=None, invoice: bool = True):
    """Repousse `expiration_date` d'une période de validité.

    Renvoie `(nouvelle_date, facture)` — la facture de cotisation (FEAT-084) est
    émise à chaque renouvellement, ou None si la catégorie est gratuite.
    Lève `CardStillValid` si la carte n'est pas près d'expirer (BUG-041).
    """
    if not can_renew(member):
        raise CardStillValid(member.expiration_date)
    months = member.category.card_validity_months or 12
    anchor = max(date.today(), member.expiration_date or date.today())
    member.expiration_date = anchor + relativedelta(months=months)
    if member.status == MemberStatus.EXPIRED:
        member.status = MemberStatus.ACTIVE
    member.save(update_fields=["expiration_date", "status"])
    membership_invoice = None
    if invoice:
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
