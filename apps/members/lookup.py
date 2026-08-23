"""FEAT-081 : résolution d'un numéro de carte d'usager saisi ou scanné.

Un usager peut être désigné par deux numéros : celui de sa **carte courante** et
celui de l'**ancienne carte** qu'elle remplace (`replaces_card_number`, posé par
`services.replace_card`). Une carte réimprimée met du temps à circuler — la
précédente traîne dans une poche ou sur une fiche papier, et elle doit continuer
à retrouver son usager.

L'écran de prêt acceptait déjà les deux ; la recherche de l'accueil et la liste
des usagers, non. Le même code rendait donc un résultat différent selon l'écran.
Tout passe désormais par `find_member` : le jour où un troisième numéro apparaît,
il n'y a qu'un endroit à changer — c'est le pendant de
`apps.catalog.lookup.find_item` pour les exemplaires.
"""
from __future__ import annotations

from apps.core.search import normalize_code

from .models import Member


def find_member(raw: str, queryset=None) -> Member | None:
    """Usager désigné par le numéro `raw`, ou None.

    La carte **courante** est essayée en premier : si un numéro se retrouvait à
    la fois comme carte d'un usager et comme ancienne carte d'un autre, c'est le
    porteur actuel qui gagne.
    """
    code = normalize_code(raw)
    if not code:
        return None
    qs = Member.objects.all() if queryset is None else queryset
    return (
        qs.filter(card_number=code).first()
        or qs.filter(replaces_card_number=code).first()
    )


def is_replaced_card(member: Member, raw: str) -> bool:
    """Vrai si `raw` est l'ancienne carte de `member`, pas la courante.

    Sert à prévenir le bibliothécaire : la carte qu'il a en main est périmée,
    l'usager en a une neuve. Sans ce signal, une carte remplacée continuerait de
    fonctionner sans que personne ne s'aperçoive qu'elle n'aurait plus dû être
    en circulation.
    """
    code = normalize_code(raw)
    return bool(code) and member.card_number != code
