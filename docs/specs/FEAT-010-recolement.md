# FEAT-010 — Récolement (inventaire)

Statut : **DONE — tests écrits, non exécutés** (2026-05-21)
Sprint : 2
Task : #10 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.5

## Périmètre

### Modèles (`apps/inventory/models.py` + migration `0001_initial`)

- `InventorySession` — campagne de pointage : `session_id` (UUID donné à
  OfeliaScan), périmètre (`scope_type` = tout / emplacement / catégorie),
  statut (`open` → `closed` → `finalized`), dates.
- `InventoryScan` — un EAN13 pointé (résolu en `Item` si connu), horodaté,
  appareil. Unicité `(session, ean13)`.

> La migration `0001_initial.py` a été **rédigée à la main** (makemigrations
> indisponible dans l'environnement au moment de l'écriture). À vérifier :
> `python manage.py makemigrations --check inventory`.

### Logique (`apps/inventory/services.py`)

- `scope_items` — exemplaires attendus dans le périmètre (hors `discarded`).
- `record_scan` — enregistre un pointage (déduplication via la contrainte).
- `build_report` — rapport de divergences (SPEC §6.5) :
  - **présents** : pointés ∩ attendus ;
  - **manquants** : attendus non pointés ;
  - **hors périmètre** : pointés existants hors du scope ;
  - **inconnus** : EAN13 pointés sans `Item` correspondant.
- `close` / `reopen` / `finalize` — transitions de statut (réversible jusqu'à
  validation finale).

### Vues (`apps/inventory/views.py`)

Liste + historique, création de session, détail (avancement temps réel +
pointage manuel web), clôture, réouverture, validation, rapport, et action de
divergence : marquer un exemplaire manquant comme perdu.

## Écarts / décisions

- **Réception des scans OfeliaScan** (`POST /api/inventory/{session_id}/items`)
  : hors périmètre — API REST Task #16. Le pointage web manuel
  (`inventory:add_scan`) couvre l'usage et les tests en attendant.
- **Actions sur divergences** : la v1 fournit « marquer perdu » pour les
  exemplaires manquants. Réintégrer / déplacer / créer une notice restent à
  câbler ultérieurement.
- **Comparaison entre récolements** (§6.5 historique) : l'historique des
  sessions est conservé ; la comparaison chiffrée entre campagnes est différée.
- **BUG-004** (corrigé) : le périmètre « attendu » (`scope_items`) se limite aux
  exemplaires `available` / `reserved_for_pickup` ; un exemplaire prêté n'est
  pas compté comme manquant.

## Tests (`apps/inventory/tests/`)

- `test_services.py` : périmètre (tout / emplacement), pointage (résolution,
  déduplication, code inconnu), rapport de divergences, transitions de statut.
- `test_views.py` : création, détail, pointage, pointage refusé si clôturée,
  clôture → rapport, résolution « marquer perdu ».
