# BUG-012 — Item.internal_id collision (UNIQUE constraint)

**Status :** FIXED
**Date :** 2026-05-24
**Sprint :** 9 (hotfix)
**Spec section :** SPEC §5.2 (Item.\_assign\_codes), §6.10 (finalize_scan_session)

---

## Symptôme

Un envoi de session OfeliaScan vers `/api/v1/scan-sessions/<id>/finalize`
plantait avec, pour chaque item :

```
UNIQUE constraint failed: catalog_item.internal_id
```

Conséquence : la session était finalisée mais aucun exemplaire n'était créé.
Les notices étaient créées (orphelines, 0 exemplaires) → état dégradé visible
dans le catalogue.

`summary` du `ScanSession` :
```
{'items_processed': 0, 'records_created': 0, 'copies_added': 0,
 'errors': [{'local_id': '…', 'error': 'UNIQUE constraint failed: catalog_item.internal_id'}, ...]}
```

## Reproduction

1. Catalog initial : items dont l'`internal_id` est `OFL-YYYYMMDD-0005, 0006,
   0009` (séquence avec trous — venait de sessions précédentes échouées ou de
   suppressions manuelles).
2. Envoyer une nouvelle session OfeliaScan le même jour avec ≥ 1 item.
3. `_assign_codes` calculait `seq = count() + 1 = 6` → assignait
   `OFL-YYYYMMDD-0006` → déjà pris → UNIQUE violation.

## Cause racine

```python
seq_today = Item.objects.filter(
    internal_id__startswith=f"OFL-{day_str}-"
).exclude(pk=self.pk).count() + 1
```

`count() + 1` ne tient pas compte des trous dans la séquence. Avec
`[0005, 0006, 0009]` → `count()=3` → seq=4 puis 5 puis 6 puis collision.

Origine probable des trous : sessions OfeliaScan précédemment échouées (même
bug, ou autre raison) qui ont laissé des items orphelins avec des IDs
discontinus.

## Fix

`apps/catalog/models.py:Item._assign_codes` — passage à `MAX(internal_id)+1` :

```python
from django.db.models import Max
max_id = Item.objects.filter(
    internal_id__startswith=f"OFL-{day_str}-"
).exclude(pk=self.pk).aggregate(m=Max("internal_id"))["m"]
max_seq = int(max_id.rsplit("-", 1)[-1]) if max_id else 0
self.internal_id = f"OFL-{day_str}-{max_seq + 1:04d}"
```

Comme les IDs sont zero-padded à 4 chiffres, le max alphabétique ==
max numérique : 1 query SQL aggregée, robuste aux trous.

## Nettoyage post-fix

17 notices orphelines (0 exemplaires, `metadata_source=scan_app`) supprimées
sur la Pi via shell Django :

```python
from django.db.models import Count
BibliographicRecord.objects.annotate(nb=Count("items")).filter(nb=0).delete()
```

## Tests

`apps/catalog/tests/test_item_codes.py` (3 cas) :
- `test_internal_id_uses_max_not_count_when_sequence_has_gaps` : seed `0005,
  0006, 0009` puis création d'un item → attendu `0010`, pas `0004`.
- `test_internal_id_sequential_creation_works` : 5 items consécutifs → 0001
  à 0005.
- `test_internal_id_first_of_day_is_0001` : premier item du jour.
