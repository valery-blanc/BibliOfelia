# FEAT-092 — Remplacer / renouveler la carte depuis l'édition de la fiche

**Status:** DONE
**Date:** 2026-09-05

## Contexte

Les boutons **Remplacer la carte** et **Renouveler la carte** étaient
parmi les actions de la fiche usager, au même rang que Modifier et
Imprimer. Val : trop faciles à déclencher (Sprint 30, point ouvert).

## Comportement

Ils quittent la fiche (`/members/<pk>/`) et rejoignent
**Modifier** (`/members/<pk>/edit/`) :

- En haut du formulaire : **n° de carte** en lecture seule, bouton
  **Remplacer la carte** à côté. Le clic affiche
  « Attention le numéro de carte va être invalidé et remplacé. Il
  faudra ré-imprimer une nouvelle carte pour l'usager ».
- À côté de la **date d'expiration** : **Renouveler la carte**.
  Pose aujourd'hui + 1 an (durée de la catégorie), message
  « Nouvelle date d'expiration : jj/mm/aaaa », reste sur Modifier.
  Plus grisé. `can_renew` et `CardStillValid` sont **supprimés**.
- Le panneau **Options avancées** est **ouvert par défaut** sur cette
  page (la date d'expiration y vit).

Les URLs POST `replace-card/` et `renew/` ne changent pas. La fiche
garde Modifier, Historique, Imprimer 62 mm, Désactiver, Supprimer.

## Impact

`templates/members/member_form.html`, `member_detail.html`,
`apps/members/views.py`, `apps/members/services.py` (`renew_card`
ancre sur aujourd'hui).
