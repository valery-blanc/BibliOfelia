# FEAT-027 — Suppression définitive d'un exemplaire

**Status :** DONE
**Date :** 2026-05-23
**Sprint :** 9
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.1

---

## Contexte

`item_discard` fait un soft-delete (status → DISCARDED). On veut une vraie
suppression en base pour les exemplaires erronés (doublon, EAN13 mal saisi)
ET pour les vols (exemplaire jamais retourné, on ne le récupérera pas).

Sémantiques :
- **Pilonner** (existant) : statut DISCARDED, exemplaire conservé en base
  avec historique. Cas : livre abîmé qui sort du fonds.
- **Supprimer définitivement** (FEAT-027) : DELETE hard. Pas de blocage —
  les prêts/réservations actifs sont automatiquement clôturés (LOST /
  CANCELLED) car ils correspondent au cas réel du vol ou de l'erreur de
  saisie.

---

## Comportement

1. Bouton **« Supprimer »** (rouge) sur `record_detail.html` à côté de
   « Pilonner », pour chaque exemplaire. Visible LIBRARIAN + SUPERADMIN.
2. Au clic : confirmation JS simple (`onsubmit="return confirm(...)"`).
3. POST `catalog:item_delete` (transaction atomique) :
   - Si `item.status == ON_LOAN` : le prêt actif passe à `LoanStatus.LOST`
     (`return_date=now`, notes : « Exemplaire supprimé — perdu/volé »).
   - Si `item.status == RESERVED_FOR_PICKUP` : la (ou les) réservation(s)
     qui pointaient via `fulfilled_by_item=item` sont annulées
     (status=CANCELLED).
   - Tous les `Loan` passés de cet item sont supprimés (cascade manuel car
     `Loan.item=PROTECT`).
   - Toutes les `InHouseConsultation` de cet item ont déjà
     `on_delete=SET_NULL`, donc OK.
   - `item.delete()`.
4. Redirect vers la fiche notice avec message « Exemplaire supprimé. »

---

## Spec technique

### URL

```python
path("items/<int:pk>/delete/", views.item_delete, name="item_delete"),
```

### Vue

```python
@require_POST
@require_role(*WRITE_ROLES)
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    record_pk = item.record_id
    with transaction.atomic():
        # Prêt actif → LOST
        active = item.loans.filter(status__in=(LoanStatus.ACTIVE, LoanStatus.OVERDUE))
        active.update(
            status=LoanStatus.LOST,
            return_date=timezone.now(),
        )
        # Réservations qui réservaient précisément cet item
        item.fulfilled_reservations.filter(
            status__in=(ReservationStatus.PENDING, ReservationStatus.READY_FOR_PICKUP)
        ).update(status=ReservationStatus.CANCELLED)
        # Cascade des loans (Loan.item=PROTECT empêche un delete direct)
        item.loans.all().delete()
        item.delete()
    messages.success(request, _("Exemplaire supprimé."))
    return redirect("catalog:record_detail", pk=record_pk)
```

### Template `record_detail.html`

Ajout d'un bouton form inline à côté du bouton « Pilonner » existant.

---

## Impact sur l'existant

- `apps/catalog/views.py` : +1 vue.
- `apps/catalog/urls.py` : +1 route.
- `templates/catalog/record_detail.html` : +1 bouton par exemplaire.

Pas de migration.

---

## Tests (`apps/catalog/tests/test_item_delete.py`)

- `test_delete_available_item` : item AVAILABLE → DELETE OK.
- `test_delete_on_loan_marks_loan_lost_then_deletes` : item ON_LOAN → loan
  initial supprimé (cascade) mais l'auditlog garde la trace LOST.
- `test_delete_reserved_cancels_reservation` : item RESERVED, résa pointant
  dessus → résa CANCELLED puis item supprimé.
- `test_delete_with_past_loans_cascades` : item AVAILABLE avec 2 loans
  RETURNED → tous supprimés, item supprimé.
- `test_delete_requires_write_role` : readonly → 403.
