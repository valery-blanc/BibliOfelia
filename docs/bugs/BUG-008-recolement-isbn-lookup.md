# BUG-008 — Récolement OfeliaScan : 100 % d'ouvrages manquants

Statut : **FIXED** (2026-05-22)

## Symptôme

Envoi d'une session de récolement depuis OfeliaScan (livres déjà présents dans
le catalogue) → résultat affiché : tous les ouvrages dans le scope indiqués
comme « manquants » (ex. 106/106).

## Reproduction

1. Créer une session récolement depuis OfeliaScan (`POST /inventory-sessions`).
2. Scanner des livres du catalogue et envoyer le batch
   (`POST /inventory-sessions/{id}/items` avec `scanned_value = isbn_commercial`).
3. Clore la session et ouvrir le rapport → toutes les lignes en « manquants ».

## Cause racine

`InventorySessionItemsView.post()` cherchait uniquement l'exemplaire par
`Item.ean13` (code interne Ofelia, préfixe `290…`). Or OfeliaScan envoie le
**code-barres commercial du livre** (ISBN `978…` ou ISBN-10), qui n'est pas
dans `Item.ean13` mais dans `BibliographicRecord.isbn_13 / isbn_10`.

Résultat : `item = None` pour chaque pointage → `InventoryScan.item_id = NULL`
→ `build_report` classe tous les scans en `unknown` → `scanned_item_ids = {}`
→ `missing = expected_ids - {} = tous`.

## Fix (`apps/api/views.py`)

Deux problèmes corrigés en une passe :

**1. Fallback ISBN** — priorité de lookup :
code interne Ofelia `290…` → `BibliographicRecord.isbn_13` → `isbn_10`.

**2. Multi-exemplaires** — pour les ISBN avec plusieurs copies :
au lieu de stocker l'ISBN brut dans `InventoryScan.ean13` (ce qui bloquait
le 2ᵉ scan du même ISBN en « doublon »), on stocke le **code interne de
l'exemplaire trouvé** et on exclut les EAN déjà dans `existing` pour trouver
le prochain exemplaire non encore pointé.

```python
item = Item.objects.filter(ean13=raw).first()
if item:
    storage_ean = raw                          # code Ofelia, déjà unique
else:
    item = (
        Item.objects.filter(record__isbn_13=raw).exclude(ean13__in=existing).first()
        or Item.objects.filter(record__isbn_10=raw).exclude(ean13__in=existing).first()
    )
    storage_ean = item.ean13 if item else raw  # EAN interne ou ISBN inconnu
```

Résultat : 3 exemplaires du même ISBN scannés → 3 `InventoryScan` distincts
→ 3 items présents dans le rapport. En pratique, le workflow normal est de
scanner les stickers `290…` (un par exemplaire, sans ambiguïté) ; le fallback
ISBN sert quand les étiquettes n'ont pas encore été collées.

## Section spec impactée

`SPEC §6.10` — récolement OfeliaScan, matching des scans.
