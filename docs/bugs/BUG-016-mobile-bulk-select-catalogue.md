# BUG-016 — Pas de sélection multiple en version mobile (catalogue)

**Status :** IN PROGRESS
**Date :** 2026-05-27
**Sprint :** 13 (cleanup post-FEAT-041)

## Symptôme

Sur `/catalog/` en version mobile (largeur ≤ 599 px), la sélection multiple
de notices n'est pas disponible : pas de cases à cocher, pas de barre
d'action — donc impossible de supprimer en masse (FEAT-026) ni d'affecter
en masse une catégorie ou un emplacement (FEAT-041) depuis un smartphone.

Note : Val mentionne également « ou membre ». Il n'y a actuellement
**aucune sélection multiple** côté `members` (pas de feature). On ne
traite ici que la version catalogue. Si Val veut une sélection multiple
membres, il faudra une FEAT dédiée.

## Reproduction

1. Ouvrir `/bibliofelia/fr/catalog/` sur Android Firefox (ou DevTools mobile).
2. Constater : pas de checkbox sur les cartes ; barre d'action de FEAT-041
   absente.

## Cause racine

`templates/catalog/record_list.html` rend deux vues alternatives :
- **Desktop** (`.hide-sm`) : tableau HTML avec checkboxes wrappées dans le
  `<form>` FEAT-026/041.
- **Mobile** (`.only-sm`) : liste de `<a class="list-row">` — pas de form,
  pas de checkbox.

Le mobile est purement navigationnel.

## Fix appliqué

- Refonte de `record_list.html` : un seul `<form>` enveloppe les **deux**
  vues. Mobile reçoit pour chaque notice une carte avec :
  - Une case à cocher leading (`<input type="checkbox" name="ids">`).
  - Le reste de la carte (icône + titre + auteurs + compteur) reste un
    `<a>` qui mène à la fiche notice.
- La barre d'action Alpine devient visible sur les deux vues (n'est plus
  marquée `.hide-sm`).
- La barre s'adapte en flex-wrap : les boutons descendent en colonne sur
  mobile.

## Spec section impactée

`SPEC §6.1` — paragraphe « Actions en masse » (FEAT-041) précise désormais
que la sélection est disponible **desktop ET mobile**.
