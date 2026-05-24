# FEAT-033 — Réassignation automatique des exemplaires au récolement

**Status :** DONE
**Date :** 2026-05-24
**Sprint :** 10
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.5 (récolement) + §6.10 (API)

---

## Contexte

Le récolement (FEAT-010, FEAT-021) permet de scanner physiquement les
exemplaires pour vérifier ce qui est encore présent dans le fonds. Une session
peut être **scoped** sur une `Location` (`scope_type=location`, champ
`scope_location` FK) : on récole alors uniquement « ce qui est censé être
rangé en A1 ».

Aujourd'hui, le `scope_location_code` envoyé par OfeliaScan ne sert qu'au
**filtrage** du périmètre attendu (`apps/inventory/services.py:26`) : il
permet de calculer les manquants et les mal-rangés. Mais il ne **modifie
pas** la `location` des exemplaires scannés.

**Insight de Val (2026-05-24) :** quand un bibliothécaire récole l'emplacement
A1 et scanne un livre, ce livre EST physiquement en A1 (puisqu'il le tient en
main, à cet endroit). Si le catalogue dit que ce livre est en B2, c'est le
catalogue qui se trompe. La source de vérité, c'est le scan terrain.

Donc : **profiter du récolement pour corriger automatiquement la `location`**
de tout exemplaire scanné, sans étape manuelle.

Décisions validées par Val (2026-05-24) :
- Réassignation **systématique** dès que `scope_type=location` et
  `scope_location` est défini. Pas de toggle, pas de flag OfeliaScan.
  Logique : si tu fais l'effort de scoper un récolement sur un emplacement,
  c'est que tu veux qu'il devienne authoritative.
- **Aucune action** sur les exemplaires non-scannés : le catalogue les laisse
  en l'état (cf. mémoire `feedback_small_library_simplicity` — pas de nouveau
  champ `missing` sur Item v1, le rapport de session suffit).
- Pas de réassignation pour `scope_type=all` ou `scope_type=category` (pas de
  location-cible définie).

---

## Comportement

### 1. Au pointage (chaque scan)

Note d'implémentation : `_maybe_relocate` a été renommé en `maybe_relocate`
(public) pour pouvoir être importé proprement depuis `apps/api/views.py`
sans accéder à un nom privé. La vue API `InventorySessionItemsView` n'utilise
pas `record_scan` (logique BUG-008 spécifique multi-exemplaires ISBN) et
appelle directement `maybe_relocate(item, session)` après le
`InventoryScan.objects.create(...)` du batch.

Modifier `apps/inventory/services.py:33-42` (`record_scan`) :

```python
def record_scan(session: InventorySession, raw_ean: str, device: str = ""):
    ean = normalize_code(raw_ean)
    item = Item.objects.filter(ean13=ean).first()
    scan, created = InventoryScan.objects.get_or_create(
        session=session,
        ean13=ean,
        defaults={"item": item, "device": device},
    )
    # FEAT-033 : réassignation auto si session scoped sur une location
    _maybe_relocate(item, session)
    return scan, created


def _maybe_relocate(item: Item | None, session: InventorySession) -> bool:
    """Si la session est scopée sur une location et que l'exemplaire
    appartient à une autre, on le déplace. Retourne True si déplacé."""
    if item is None:
        return False
    if session.scope_type != InventoryScope.LOCATION:
        return False
    if not session.scope_location_id:
        return False
    if item.location_id == session.scope_location_id:
        return False
    item.location_id = session.scope_location_id
    item.save(update_fields=["location"])
    return True
```

Effet : à chaque scan « positif » (EAN13 matche un Item du catalogue), si la
session a un scope location et que l'item est ailleurs (ou nulle part), on
force `item.location = session.scope_location`.

Conséquences immédiates :
- Les **mal-rangés** (`misplaced`) du rapport disparaissent : un livre scanné
  en A1 alors qu'il était catalogué en B2 devient un *présent* en A1 (et
  manquant en B2 si une session future est faite sur B2).
- Les exemplaires **sans emplacement** (`location=None`) reçoivent
  automatiquement une location au passage. Effet bonus : un récolement A1
  permet de « baptiser » les exemplaires non rangés.

### 2. Au rapport de session

Le rapport (`build_report`, `apps/inventory/services.py:45`) reste inchangé :
il calcule présents / manquants / mal-rangés / inconnus à partir de l'état
**actuel** du catalogue. Comme la réassignation se fait *au moment du scan*,
le rapport reflète déjà la nouvelle réalité — la rubrique « mal-rangés » sera
typiquement vide en mode location, c'est attendu.

Ajout dans le résumé de session : compteur `items_relocated` (nombre de
scans qui ont effectivement déplacé un Item). Affiché dans
`templates/inventory/session_report.html` sous la forme :

```
N exemplaires déplacés vers <code location> pendant cette session.
```

Stockage : `InventorySession` n'a pas aujourd'hui de `processing_summary`
JSON (contrairement à `ScanSession`). Deux options :

- **Option A** : ajouter un champ `relocate_count = IntegerField(default=0)`
  incrémenté à chaque `_maybe_relocate(...) == True`. Nécessite une
  migration triviale.
- **Option B** : calculer à la volée au rapport via une comparaison
  `InventoryScan.item.location != session.scope_location` après-coup. Mais
  comme on a déjà réassigné, l'info est perdue.

**Choix : Option A** (champ `relocate_count`).

### 3. Comportement côté API OfeliaScan

Endpoint `POST /api/inventory-sessions/<uuid>/items` (FEAT-021) : aucune
modification de contrat. Le client envoie toujours `{"items": [{"scanned_value":
"291…", "scanned_at": "..."}]}`. La réassignation est un effet de bord
serveur, transparent pour OfeliaScan.

Optionnel : enrichir la réponse de finalisation `POST /api/inventory-sessions/
<uuid>/finalize` (déjà retourne un summary) avec `"relocated": <n>`. À
décider en implémentation.

### 4. Comportement côté UI web

Identique : un récolement lancé depuis l'UI web (`/inventory/<uuid>/`)
bénéficie de la même réassignation. Aucun changement de template requis,
seulement l'ajout du compteur dans le rapport.

---

## Spec technique

### Migration

`apps/inventory/migrations/00XX_inventorysession_relocate_count.py` :
```python
operations = [
    migrations.AddField(
        model_name="inventorysession",
        name="relocate_count",
        field=models.PositiveIntegerField(default=0),
    ),
]
```

### Service

`apps/inventory/services.py` :
- Ajout `_maybe_relocate(item, session) -> bool`
- Modif `record_scan` : appel + incrément `session.relocate_count` si déplacé
  (en `update_fields=["relocate_count"]` pour éviter le full-save)
- Pas de modif `build_report`, juste exposer `session.relocate_count` au
  template

### Tests

`apps/inventory/tests/test_relocate.py` :
- Item en B2 + session scopée A1 + scan de l'item → `item.location.code == "A1"` après scan, `session.relocate_count == 1`
- Item sans location + session scopée A1 + scan → location ← A1
- Item déjà en A1 + scan → pas de save (location inchangée), `relocate_count == 0`
- Session `scope_type=all` + scan → pas de relocate
- Session `scope_type=category` + scan → pas de relocate
- Scan d'un EAN13 inconnu (Item=None) + scope location → pas de crash, pas de relocate

`apps/api/tests/test_inventory_api.py` :
- Étendre les tests existants pour vérifier qu'après un `POST /items` avec
  des codes valides, les items ont leur `location` mise à jour.

### Template

`templates/inventory/session_report.html` :
- Si `session.relocate_count > 0` et `session.scope_type == "location"` :
  bandeau d'info `<div class="callout">{N} exemplaires déplacés vers
  {scope_location.code} pendant cette session.</div>`

---

## Impact sur l'existant

- `apps/inventory/models.py` : +1 champ `relocate_count`
- `apps/inventory/migrations/` : +1 migration triviale
- `apps/inventory/services.py` : +1 fonction `_maybe_relocate`, +modif
  `record_scan`
- `templates/inventory/session_report.html` : +1 bandeau conditionnel
- `apps/inventory/tests/test_relocate.py` : nouveau fichier
- `apps/api/tests/test_inventory_api.py` : étendu
- `SPEC_BIBLIOFELIA.md` : §6.5 (paragraphe « Réassignation automatique »)

Pas de changement de contrat API. Pas de modification OfeliaScan requise.

---

## Hors scope

- Réassignation pour `scope_type=category` ou `scope_type=all` (pas de
  location-cible évidente).
- Annulation / rollback d'une réassignation (le rapport est l'audit).
- Nouveau statut `missing` sur Item pour les non-scannés (cf. décision Val :
  statu quo).
- Notification UI au bibliothécaire pendant le scan (« 12 exemplaires
  déplacés ») — c'est le rapport final qui le dit.

---

## Risques et notes

- **Effet de bord important** : un récolement scoped A1 *écrit* dans la base
  catalogue. Si un bibliothécaire scanne par erreur des livres qu'il rapporte
  d'un autre rayon vers A1 « pour les ranger plus tard », la base le suivra.
  Acceptable car c'est exactement le comportement souhaité dans 95 % des cas.
- **Concurrence** : `record_scan` est appelé par scan, séquentiellement par
  session ; pas de risque de race condition sur `relocate_count` côté UI web.
  Côté API, le batch `POST /items` traite les items en série dans la même
  vue → idem.
- **Idempotence** : un scan rejoué (même EAN, même session) → `get_or_create`
  retourne `created=False`, mais `_maybe_relocate` est appelé quand même. Si
  l'item est déjà à la bonne location → no-op. Sûr.
