"""Registre des écrans de rapport. FEAT-093.

Ajouter un écran = écrire un `build_…(period, params) -> ReportPage` et
l'inscrire ici. L'écran HTML, l'export PDF et l'export Excel suivent sans une
ligne de plus : c'est ce qui tient la règle « pas d'écran sans ses deux
exports, pas d'export sans son écran ».

Chaque écran porte sa couleur, reprise de la charte OFELIA comme sur la page
Avancé : le rouge alerte pour les retards, l'ambre pour ce qui attend, le vert
pour le fonds. Elle sert au hub et n'est écrite qu'ici.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from django.utils.translation import gettext_lazy as _

from . import attendance, collection, loans, members, money, overview, team, worklists

GROUP_WORK = "work"
GROUP_STATS = "stats"


@dataclass(frozen=True)
class ReportSpec:
    slug: str
    title: str
    description: str
    icon: str
    group: str
    builder: Callable
    tint_bg: str = "var(--forest-light)"
    tint_fg: str = "var(--forest)"
    needs_period: bool = True
    action_label: str = ""  # verbe affiché sur la carte du hub (listes de travail)
    counter: Callable | None = None  # chiffre affiché sur la carte du hub


REPORTS: list[ReportSpec] = [
    # ── Tous les jours : ce qui se fait, pas ce qui se montre ──
    ReportSpec(
        slug="overdue",
        title=_("Les retards"),
        description=_("Les livres qui auraient dû être rendus, du plus ancien au plus récent."),
        icon="triangle-alert",
        group=GROUP_WORK,
        builder=worklists.build_overdue,
        tint_bg="var(--blush-light)",
        tint_fg="#B83232",
        needs_period=False,
        action_label=_("Relancer les retards"),
        counter=worklists.count_overdue,
    ),
    ReportSpec(
        slug="pickup",
        title=_("Les réservations à retirer"),
        description=_("Les livres mis de côté et qui les attend."),
        icon="bookmark-check",
        group=GROUP_WORK,
        builder=worklists.build_pickup,
        tint_bg="var(--amber-light)",
        tint_fg="#946906",
        needs_period=False,
        action_label=_("Prévenir les usagers"),
        counter=worklists.count_pickup,
    ),
    ReportSpec(
        slug="inactive",
        title=_("Les inactifs"),
        description=_("Les usagers et les livres sans mouvement depuis longtemps."),
        icon="archive",
        group=GROUP_WORK,
        builder=worklists.build_inactive,
        tint_bg="var(--cream-dark)",
        tint_fg="#6B5A0E",
        needs_period=False,
        action_label=_("Voir les inactifs"),
        counter=worklists.count_inactive,
    ),
    # ── Comprendre la bibliothèque ──
    ReportSpec(
        slug="overview",
        title=_("Vue d'ensemble"),
        description=_("Tous les chiffres importants sur une page. À imprimer pour le comité."),
        icon="layout-dashboard",
        group=GROUP_STATS,
        builder=overview.build,
        tint_bg="var(--burgundy-light)",
        tint_fg="var(--burgundy)",
    ),
    ReportSpec(
        slug="collection",
        title=_("Le fonds"),
        description=_("Combien de livres, de quelle sorte, dans quel état, d'où ils viennent."),
        icon="library",
        group=GROUP_STATS,
        builder=collection.build,
        tint_bg="var(--forest-light)",
        tint_fg="var(--forest)",
    ),
    ReportSpec(
        slug="loans",
        title=_("Les prêts"),
        description=_("Combien de prêts, et les livres les plus et les moins empruntés."),
        icon="book-up",
        group=GROUP_STATS,
        builder=loans.build,
        tint_bg="var(--orange-light)",
        tint_fg="var(--orange)",
    ),
    ReportSpec(
        slug="members",
        title=_("Les usagers"),
        description=_("Combien de personnes, qui elles sont, qui arrive et qui part."),
        icon="users",
        group=GROUP_STATS,
        builder=members.build,
        tint_bg="var(--sky-light)",
        tint_fg="#1a4a80",
    ),
    ReportSpec(
        slug="attendance",
        title=_("La fréquentation"),
        description=_("Qui vient à la bibliothèque et aux animations, et de quel âge."),
        icon="calendar-check",
        group=GROUP_STATS,
        builder=attendance.build,
        tint_bg="var(--olive-light)",
        tint_fg="#6B5A0E",
    ),
    ReportSpec(
        slug="team",
        title=_("Le travail de l'équipe"),
        description=_("Les heures faites, par nature de travail et par personne."),
        icon="clock",
        group=GROUP_STATS,
        builder=team.build,
        tint_bg="var(--blush-light)",
        tint_fg="#B83232",
    ),
    ReportSpec(
        slug="money",
        title=_("L'argent"),
        description=_("Ce qui a été facturé, ce qui a été encaissé, ce qui reste dû."),
        icon="wallet",
        group=GROUP_STATS,
        builder=money.build,
        tint_bg="var(--amber-light)",
        tint_fg="#946906",
    ),
]

BY_SLUG = {spec.slug: spec for spec in REPORTS}


def get(slug: str) -> ReportSpec | None:
    return BY_SLUG.get(slug)


def in_group(group: str) -> list[ReportSpec]:
    return [spec for spec in REPORTS if spec.group == group]
