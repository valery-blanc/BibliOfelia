# FEAT-026 — Suppression en masse d'ouvrages depuis le catalogue

**Status :** DONE
**Date :** 2026-05-23
**Sprint :** 9
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.1

---

## Contexte

`record_delete` permet aujourd'hui de supprimer une notice à la fois.
Cas d'usage principal : nettoyage post-install (notices saisies en doublon
ou héritées des démos non couvertes par `remove_demo`).

Cible utilisateur : **superadmin uniquement**.

---

## Comportement

1. La liste `catalog:record_list` affiche pour les superadmins une **case à
   cocher** par ligne + une case « tout cocher » dans l'en-tête (script
   Alpine léger sur la page).
2. Une **barre d'action** apparaît dès qu'au moins une case est cochée :
   « Supprimer la sélection » → POST `catalog:record_bulk_delete_confirm`.
3. Page de confirmation listant les notices à supprimer, avec le détail
   par notice (N exemplaires dont N en cours de prêt / N en réservation).
   **Aucun blocage** : prêts en cours seront passés en `LOST` automatiquement
   (cas du vol — `LoanStatus.LOST` existe depuis FEAT-002), réservations
   actives passeront en `CANCELLED`.
4. POST `catalog:record_bulk_delete` (transaction atomique) :
   - Pour chaque notice : `Loan.objects.filter(item__record=record, status__in=ACTIVE).update(status=LOST, return_date=now, notes+=...)`
   - `Reservation.objects.filter(record=record, status__in=ACTIVE).update(status=CANCELLED)`
   - `Loan.objects.filter(item__record=record).delete()` (CASCADE manuel pour contourner Loan.item=PROTECT)
   - `InHouseConsultation.objects.filter(item__record=record).delete()`
   - `record.delete()` (CASCADE supprime les exemplaires via Item.record=CASCADE)
5. Message flash : « N notice(s) supprimée(s). »

Note : `Reservation.record` est déjà `CASCADE`, donc le DELETE de la notice
supprime les réservations en passant. On les marque `CANCELLED` avant pour
laisser une trace dans l'auditlog au cas où.

---

## Spec technique

### URLs

```python
path("bulk-delete/", views.record_bulk_delete_confirm, name="record_bulk_delete_confirm"),
path("bulk-delete/apply/", views.record_bulk_delete, name="record_bulk_delete"),
```

### Vues

Voir `apps/catalog/views.py:record_bulk_delete_confirm` et `record_bulk_delete`.

### Template `record_list.html`

Wrapper le tableau dans `<form method="post" action="…confirm">` (superadmin
uniquement). Colonne checkbox, en-tête « tout cocher ». Bandeau sticky avec
le bouton « Supprimer la sélection » dès qu'une case est cochée (Alpine).

### Template `record_bulk_delete.html` (nouveau)

Récap des notices et de leurs impacts (prêts/résa actifs qui passeront en
LOST/CANCELLED). Bouton « Confirmer la suppression ».

---

## Impact sur l'existant

- `apps/catalog/views.py` : +2 vues + 1 helper `_summarize_for_bulk_delete`.
- `apps/catalog/urls.py` : +2 routes.
- `templates/catalog/record_list.html` : colonne checkbox + form (zone superadmin).
- `templates/catalog/record_bulk_delete.html` : nouveau.

Pas de migration.

---

## Tests (`apps/catalog/tests/test_bulk_delete.py`)

- `test_confirm_requires_superadmin` : librarian → 403.
- `test_confirm_shows_active_loan_impact` : notice avec exemplaire prêté →
  la page de confirmation mentionne le prêt qui sera passé en LOST.
- `test_apply_deletes_all_selected` : 3 notices sélectionnées → toutes
  supprimées.
- `test_apply_marks_active_loans_as_lost` : exemplaire prêté → après
  suppression, le Loan existe avec status=LOST… non : on cascade ensuite.
  Vérifier que l'auditlog enregistre la transition (le record est gone, le
  loan aussi, mais l'auditlog reste).
- `test_apply_cancels_active_reservations` : pareil.
- `test_apply_empty_selection_is_noop` : pas d'IDs → 0 supprimés.
