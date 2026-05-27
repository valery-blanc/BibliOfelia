# FEAT-041 — Affectation en masse Category + Location depuis le catalogue

**Status :** IN PROGRESS
**Date :** 2026-05-27
**Sprint :** 13
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.1 (catalogue)

---

## Contexte

La page `/catalog/` (FEAT-026) permet déjà la sélection multiple de notices
pour la **suppression en masse** (visible côté SUPERADMIN). Val veut étendre
cette UX à 2 actions courantes :

1. **Affecter une catégorie** à toutes les notices sélectionnées.
2. **Affecter un emplacement** à tous les exemplaires des notices sélectionnées.

Ces deux actions sont plus fréquentes que la suppression et doivent être
accessibles aux **librarians** (pas seulement aux superadmins).

## Comportement

### Sélection multiple

- La barre d'action existante (Alpine, visible si au moins 1 case cochée)
  affiche désormais 3 boutons :
  - « Affecter une catégorie » (librarian + superadmin)
  - « Affecter un emplacement » (librarian + superadmin)
  - « Supprimer la sélection » (superadmin uniquement, comportement actuel)
- Le tableau de sélection est rendu **dès que l'utilisateur est librarian ou
  superadmin** (aujourd'hui : superadmin seulement). L'option « supprimer »
  reste conditionnée par `user.is_superadmin`.

### Affectation de catégorie

- Bouton submit POST → `catalog:record_bulk_assign_category_confirm`.
- Page de confirmation : liste des notices ciblées + sélecteur de catégorie
  (toutes les `Category`).
- Submit → `catalog:record_bulk_assign_category` : `UPDATE BibliographicRecord
  SET category_id=... WHERE pk IN (ids)`.
- Message de succès : « N notices affectées à la catégorie X. ».

### Affectation d'emplacement

- Bouton submit POST → `catalog:record_bulk_assign_location_confirm`.
- Page de confirmation : compte des exemplaires totaux qui seront affectés
  (`Item.objects.filter(record_id__in=ids).count()`) + sélecteur de Location
  (toutes les `Location`, triées par code).
- Submit → `catalog:record_bulk_assign_location` : `Item.objects.filter(
  record_id__in=ids).update(location_id=...)`.
- Message de succès : « N exemplaires affectés à l'emplacement Y. ».

### Cas limites

- Aucune sélection → submit ne se déclenche pas (barre Alpine cachée).
- Catégorie/Location vide (none) acceptée → met `category_id=None` /
  `location_id=None` (cohérent avec le champ nullable côté modèle).
- Exemplaires DISCARDED/LOST : on ne les exclut pas (un superadmin peut vouloir
  les réorganiser ; aucune contrainte fonctionnelle).

## Technique

- 4 nouvelles vues dans `apps/catalog/views.py` :
  - `record_bulk_assign_category_confirm` (POST, librarian+superadmin)
  - `record_bulk_assign_category` (POST, librarian+superadmin)
  - `record_bulk_assign_location_confirm` (POST, librarian+superadmin)
  - `record_bulk_assign_location` (POST, librarian+superadmin)
- Routes ajoutées dans `apps/catalog/urls.py`.
- 2 nouveaux templates : `templates/catalog/record_bulk_assign_category.html`,
  `templates/catalog/record_bulk_assign_location.html`.
- Mise à jour `templates/catalog/record_list.html` :
  - tableau de sélection rendu pour `user.is_librarian or
    user.is_superadmin`,
  - bouton « Affecter catégorie » + bouton « Affecter emplacement » dans la
    barre Alpine, bouton « Supprimer » conditionné `user.is_superadmin`.

## Tests

- `apps/catalog/tests/test_bulk_assign.py`
  - Permissions : readonly KO, librarian OK pour assign/confirm,
    superadmin OK.
  - assign_category : update sur N notices, message correct.
  - assign_location : update sur tous les items des notices, message correct.
  - assign avec valeur vide → set NULL.
  - assign avec liste vide → no-op + warning.

## Impact

- `apps/catalog/views.py`, `urls.py`
- `templates/catalog/record_list.html` (+ 2 templates de confirmation)
- `apps/catalog/tests/`
- `docs/specs/SPEC_BIBLIOFELIA.md` §6.1 (paragraphe « Actions en masse »)
