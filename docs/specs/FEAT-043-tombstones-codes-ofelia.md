# FEAT-043 — Tombstones des codes Ofelia (anti-réattribution)

**Status :** DONE
**Date :** 2026-05-28
**Sprint :** 14
**Spec parent :** `SPEC_BIBLIOFELIA.md` §5.2 (Item) / §6.1 (catalogue)
**Liens :** [[FEAT-026]] (bulk-delete), [[BUG-2026-05-24-internal-id-collision]]

---

## Contexte

Le code Ofelia d'un exemplaire (`Item.internal_id`, format `OFL-YYYYMMDD-NNNN`)
est **imprimé sur une étiquette physique** collée sur le livre (carte de prêt
+ code-barres EAN13 dérivé). Avant FEAT-043, l'attribution se faisait via
`MAX(internal_id) + 1` filtré sur le jour, ce qui exposait à une réutilisation
silencieuse dans plusieurs cas :

- suppression du **dernier** item du jour → son code revenait au prochain ajout ;
- suppression de **tous** les items du jour → la séquence repartait à `0001`,
  réutilisant l'intégralité des codes du jour.

Conséquence : une étiquette imprimée pouvait finir collée sur deux livres
différents au fil du temps, casser les rapprochements d'inventaire et
introduire des incohérences silencieuses dans les prêts.

Cible : tous rôles (impact transparent — aucune UI).

---

## Comportement

1. **Tombstone des codes** : un nouveau modèle `RetiredItemCode` conserve
   l'`internal_id` (PK), l'`ean13`, le titre de la notice snapshot, la date,
   l'utilisateur et la **raison** (`bulk_delete` | `item_delete`).
2. **Signal `pre_delete`** sur `Item` : à toute suppression (admin, unitaire,
   CASCADE depuis `BibliographicRecord.delete()`, queryset `.delete()`), une
   tombstone est créée via `get_or_create` (idempotent).
3. **Attribution** : `Item._assign_codes()` calcule désormais le `MAX` du jour
   en **union `Item ∪ RetiredItemCode`**, garantissant qu'aucun code retiré
   ne sera réattribué.
4. **Vue bulk-delete** : pré-crée les tombstones avec `reason=bulk_delete` et
   `retired_by=request.user` AVANT le `record.delete()` cascade. Le signal
   utilise `get_or_create` donc ne réécrira pas ces lignes plus précises.

---

## Implémentation

### Modèle (`apps/catalog/models.py`)

```python
class RetiredItemCode(models.Model):
    REASON_BULK_DELETE = "bulk_delete"
    REASON_ITEM_DELETE = "item_delete"
    internal_id = CharField(max_length=20, primary_key=True)
    ean13 = CharField(max_length=13, blank=True)
    record_title_snapshot = CharField(max_length=255, blank=True)
    retired_at = DateTimeField(auto_now_add=True)
    retired_by = ForeignKey(User, null=True, on_delete=SET_NULL)
    reason = CharField(choices=REASON_CHOICES, default=REASON_ITEM_DELETE)
```

### Signal (`apps/catalog/signals.py`)

`pre_delete` sur `Item` → `RetiredItemCode.objects.get_or_create(internal_id=...)`.
Connecté via `CatalogConfig.ready()`.

### `_assign_codes`

```python
max_item    = Item.objects.filter(internal_id__startswith=prefix)...
max_retired = RetiredItemCode.objects.filter(internal_id__startswith=prefix)...
top = max([v for v in (max_item, max_retired) if v])
self.internal_id = f"OFL-{day_str}-{int(top[-4:]) + 1:04d}"
```

### Migration

`0007_retired_item_codes.py` (CreateModel + index sur internal_id).

---

## Tests

`apps/catalog/tests/test_retired_codes.py` — 5 tests :
- tombstone créée sur `item.delete()`
- code du dernier item supprimé **non réutilisé**
- séquence ne repart pas à 0001 quand tous les items du jour sont supprimés
- CASCADE depuis `record.delete()` crée bien les tombstones
- vue `record_bulk_delete` utilise `reason=bulk_delete` + `retired_by`

Suite catalog + loans + members + inventory : 186 tests, tous verts.

---

## Impact

- **Aucun impact UI** (transparent).
- **Aucune migration de données** (table neuve, vide).
- Coût stockage : 1 ligne par item supprimé (~80 octets). Pour 100 000
  suppressions cumulées : ~8 MB. Négligeable.
- Audit utile : la table peut être consultée via `/admin/` (superadmin
  uniquement) pour retracer un code retiré.

---

## Liens connexes

- FEAT-026 — bulk-delete des notices (consommateur principal).
- BUG 2026-05-24 — `count()+1` → `MAX+1` (fix précédent sur la même fonction).
- FEAT-012 — impression étiquettes (raison principale du besoin).
