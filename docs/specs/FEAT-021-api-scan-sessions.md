# FEAT-021 — API OfeliaScan : sessions de scan et récolement (Task #20)

Statut : **EN COURS** (2026-05-22)
Sprint : 5
Task : #20 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.10 (sections « Sessions de scan » et « Récolement »)

## Contexte

L'API REST OfeliaScan v1 (Task #16, FEAT-016) couvre uniquement l'auth,
l'appairage, le lookup ISBN, le diagnostic. **L'envoi des listes de livres
par OfeliaScan** vers la box n'est pas implémenté → c'est l'objet de cette
feature. Test Val sur la Pi 2026-05-22 : pairing OK mais envoi des listes
échoue (404 sur les endpoints `scan-sessions` et `inventory-sessions`).

## Contrat figé par OfeliaScan (le client est déjà déployé)

La SPEC §6.10 initiale décrivait un schéma simplifié (`isbn`, `state`,
corps = tableau nu). En réalité, OfeliaScan envoie un schéma plus riche et
mieux nommé. **C'est le schéma OfeliaScan qui fait foi** ; SPEC §6.10 est
mise à jour pour refléter le vrai contrat.

### `POST /scan-sessions` — créer une session

Auth : JWT. Body : `{"label"?: string}`.

Réponse `201` :
```json
{
  "session_id": "uuid",
  "state": "open",
  "created_at": "2026-05-22T14:30:00Z"
}
```

### `POST /scan-sessions/{id}/items` — envoi de batch

Auth : JWT. Body :
```json
{
  "items": [
    {
      "local_id": "string (unique par session, idempotency)",
      "scan_kind": "ean13" | "isbn" | "manual",
      "scanned_value": "string (l'ISBN ou l'EAN scanné, ou rien si manuel)",
      "metadata_title": "string",
      "metadata_authors": ["string", ...],
      "metadata_language": "fr|en|es|...",
      "metadata_publisher": "string",
      "metadata_year": 2024,
      "location_code": "A1",
      "item_state": "new|good|worn|damaged",
      "copy_count": 1,
      "scanned_at": "2026-05-22T14:30:00Z",
      "notes": "string"
    },
    ...
  ]
}
```

Tous les champs sauf `local_id`, `scan_kind`, `scanned_at` sont optionnels
(`null`/`""`/absents acceptés).

Réponse `200` :
```json
{
  "session_id": "uuid",
  "accepted": 12,
  "duplicates": 0,
  "rejected": [{"local_id": "...", "reason": "..."}]
}
```

Idempotency : envoyer 2× le même `local_id` dans la même session ne crée
pas de doublon (le 2ᵉ POST renvoie `duplicates += 1`, jamais d'erreur).
La session doit être `open` ; sinon `409 session_closed`.

### `POST /scan-sessions/{id}/finalize` — clôt et traite

Auth : JWT. Body vide.

Traitement (**synchrone, v1**) — transaction atomique :

1. Pour chaque `ScanItem` non-traité de la session :
   - Si `scan_kind ∈ {ean13, isbn}` et `scanned_value` non vide → tentative
     de lookup d'un `BibliographicRecord` existant par `isbn_13` ou
     `isbn_10` (la valeur scannée est normalisée).
   - **Si trouvé** : `+copy_count` `Item`s ajoutés au record existant
     (location si reconnue par `code`, state si valide).
   - **Si non trouvé** : nouveau `BibliographicRecord` créé avec les
     `metadata_*` reçus + `+copy_count` `Item`s.
   - Cas `manual` ou `scanned_value` vide : même règle, mais lookup ignoré
     → toujours un nouveau record (titre = `metadata_title` ou « Sans
     titre — session X »).
   - Le marqueur `metadata_source=scan_app` et un suffixe `[ScanSession:UUID]`
     dans `notes` permettent au librarian de retrouver l'origine.
2. La session passe `state=finalized`, `finalized_at=now()`,
   `processing_summary` JSON stocké pour rappel.

Réponse `200` :
```json
{
  "session_id": "uuid",
  "state": "finalized",
  "finalized_at": "2026-05-22T14:35:00Z",
  "summary": {
    "items_processed": 12,
    "records_created": 8,
    "records_matched": 4,
    "copies_added": 14,
    "errors": []
  }
}
```

### `POST /inventory-sessions` — créer une session de récolement

Auth : JWT. Body : `{"label"?: string, "scope_type"?: "all"|"location"|"category", "scope_location_code"?: "A1", "scope_category_code"?: "ROM"}`.

Réponse `201` :
```json
{
  "session_id": "uuid",
  "state": "open",
  "started_at": "2026-05-22T14:30:00Z"
}
```

Le flag `mobile_created=True` est positionné sur l'`InventorySession` pour
la distinguer dans l'UI librarian.

### `POST /inventory-sessions/{id}/items` — envoi de batch

Auth : JWT. Body :
```json
{
  "items": [
    {"scanned_value": "2900000000017", "scanned_at": "2026-05-22T14:30:00Z"},
    ...
  ]
}
```

Réponse `200` :
```json
{
  "session_id": "uuid",
  "accepted": 25,
  "duplicates": 2,
  "rejected": []
}
```

Chaque `scanned_value` est normalisé puis enregistré comme `InventoryScan`
(contrainte UNIQUE `(session, ean13)` côté DB ; doublon = `duplicates += 1`).
La session doit être `open` ; sinon `409 session_closed`.

### `POST /inventory-sessions/{id}/close` — clôture

Auth : JWT. Body vide.

Réponse `200` : `{session_id, state: "closed", closed_at, scans_count}`.

Pas de génération de rapport ici — la validation (rapport, traitement des
divergences) reste un workflow librarian côté web (FEAT-010).

## Modèles

### `apps/catalog/models.py` (ajout)

```python
class ScanSessionState(TextChoices):
    OPEN      = "open",      _("Ouverte")
    FINALIZED = "finalized", _("Validée")

class ScanSession(Model):
    session_id          = UUIDField(default=uuid4, unique=True, editable=False)
    label               = CharField(max_length=120, blank=True)
    state               = CharField(choices=ScanSessionState, default=OPEN)
    started_at          = DateTimeField(default=timezone.now)
    finalized_at        = DateTimeField(null=True, blank=True)
    created_by          = FK(User, on_delete=SET_NULL, null=True)
    processing_summary  = JSONField(default=dict, blank=True)

class ScanItem(Model):
    session             = FK(ScanSession, related_name="items", on_delete=CASCADE)
    local_id            = CharField(max_length=120)
    scan_kind           = CharField(max_length=10)  # ean13|isbn|manual
    scanned_value       = CharField(max_length=32, blank=True)
    metadata_title      = CharField(max_length=300, blank=True)
    metadata_authors    = JSONField(default=list, blank=True)
    metadata_language   = CharField(max_length=10, blank=True)
    metadata_publisher  = CharField(max_length=200, blank=True)
    metadata_year       = IntegerField(null=True, blank=True)
    location_code       = CharField(max_length=20, blank=True)
    item_state          = CharField(max_length=10, blank=True)
    copy_count          = PositiveIntegerField(default=1)
    scanned_at          = DateTimeField()
    notes               = TextField(blank=True)
    processed           = BooleanField(default=False)
    processing_result   = JSONField(default=dict, blank=True)
    class Meta:
        constraints = [UniqueConstraint(fields=["session", "local_id"], name="scanitem_unique_local")]
```

### `apps/inventory/models.py` (modification)

```python
class InventorySession(Model):
    # ... existant ...
    mobile_created = BooleanField(default=False)
```

### Migrations

- `apps/catalog/migrations/0005_scan_sessions.py` (manuelle, comme `0002_fts5`)
- `apps/inventory/migrations/0002_mobile_created.py` (manuelle)

## Permissions

| Rôle | scan-sessions | inventory-sessions |
|---|---|---|
| `superadmin`, `librarian` | voient toutes, agissent sur toutes | idem |
| `contributor_api` | voient/agissent **uniquement sur les siennes** (`created_by=request.user`) | idem |
| autre / anonyme | 401 / 403 | idem |

Implémentation : `permission_classes = [IsAuthenticated]` + filtre
ownership dans `get_object()` (404 = même réponse que ressource inexistante,
ne fuit pas l'existence des sessions des autres).

## Throttling

- Scope `scan` (60/min) sur tous les endpoints de cette feature
  (déjà configuré dans `settings/base.py`).

## Tests

- `apps/api/tests/test_scan_sessions.py` :
  create / items batch / idempotency local_id / finalize crée records /
  finalize matche ISBN existant / 409 si session closed / ownership 404.
- `apps/api/tests/test_inventory_api.py` :
  create / items batch / scope_location_code / close / ownership 404.

## Doc

- `SPEC_BIBLIOFELIA.md` §6.10 : sections « Sessions de scan » et
  « Récolement » réécrites pour refléter le vrai contrat OfeliaScan.
- Version SPEC incrémentée.
