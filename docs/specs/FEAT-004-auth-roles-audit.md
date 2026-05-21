# FEAT-004 — Auth, rôles, audit, throttling

Statut : **DONE** (2026-05-21)
Sprint : 1 (Domaine)
Task : #4 de `docs/tasks/TASKS.md`
Spec : `docs/specs/SPEC_BIBLIOFELIA.md` §9.1 / §9.2 / §9.6

## Contexte

Sprint 0 a livré le `User` étendu avec un champ `role` (enum) + django-axes + middleware auditlog. Cette feature câble effectivement les rôles aux permissions Django, automatise la synchronisation `role → Group` et active l'audit log explicite sur les modèles sensibles.

## Périmètre

### Mapping rôles → permissions (`apps/accounts/groups.py`)

Référentiel `ROLE_PERMS: dict[str, list[tuple[app_label, codename]]]`.

| Rôle | Permissions assignées (Django) |
|---|---|
| `superadmin` | Aucune explicite — `is_superuser=True` bypasse les checks. Group créé pour cohérence. |
| `librarian` | CRUD `catalog.{author,category,tag,location,item}` + add/change/view `catalog.bibliographicrecord` (pas de delete pour préserver l'historique) + add/change/view `members.member` + view `members.membercategory` + CRUD `loans.*`. Aucun accès Setting / User / auditlog. |
| `contributor_api` | `add_bibliographicrecord`, `add_item`, `add_author` + view sur le catalogue. Rien d'autre. |
| `readonly` | `view_*` sur catalog + members + loans. Aucune écriture. |

Helpers internes `_crud`, `_cv` (add/change/view), `_view` pour limiter la duplication.

### Synchronisation automatique (`apps/accounts/signals.py`)

Signal `post_save` sur `User` → `assign_role_group` :

1. Si `is_superuser=True` → force `role=SUPERADMIN` (cas `createsuperuser`).
2. `is_staff = (role == SUPERADMIN)` : seul le superadmin peut accéder à `/admin/` Django (cf. feedback Val : les bibliothécaires n'utilisent jamais l'admin Django).
3. Met à jour ces champs via `User.objects.filter(...).update(...)` pour éviter la récursion du signal.
4. Synchronise l'appartenance Group : retire les autres Groups de rôle, ajoute le bon. Idempotent.

Le signal est connecté dans `apps/accounts/apps.py:ready()` (import du module `signals`).

### Commande `setup_roles` (idempotente)

`python manage.py setup_roles` :

- Crée/maintient les 4 `Group` Django (1 par rôle).
- Résout `(app_label, codename)` en `Permission` via `ContentType` (gère les codenames qui existent dans plusieurs apps comme `add_user`).
- Diff `add/remove` plutôt que `set` pour préserver les permissions ajoutées manuellement par un admin.
- Resynchronise tous les `User` existants via un `user.save()` (déclenche le signal pour re-grouper).

Appelée automatiquement dans `scripts/dev-entrypoint.sh` après `seed_defaults`.

### Helpers d'autorisation (`apps/accounts/permissions.py`)

- `@require_role(*roles)` : décorateur de vue Django. Wraps `login_required`. Lève `PermissionDenied` si le rôle ne matche pas. `is_superuser` bypasse.
- `class HasRole(BasePermission)` : permission DRF. À utiliser via `view.required_roles = (Role.X, …)`. Renvoie False si pas de rôle requis défini.

Ces helpers seront utilisés par les vues custom du Sprint 2 (UI) et de l'API (Task #16).

### Audit log (`apps/core/apps.py:ready()`)

Enregistre dans `auditlog.registry` les 6 modèles cités SPEC §9.6 :

- `core.Setting`
- `catalog.BibliographicRecord`, `catalog.Item`
- `members.Member`
- `loans.Loan`
- `accounts.User`

Idempotent (`if not auditlog.contains(model)`). Le middleware `AuditlogMiddleware` (déjà actif dans `settings/base.py`) attache l'actor (request.user) automatiquement.

**Hors scope ici** :
- Rétention 5 ans → commande de purge périodique (Task #13/#14).
- Export pour rapport/investigation → Task #11 (rapports).

### Throttling DRF (§9.1, §6.10)

Déjà configuré dans `settings/base.py` :

```python
DEFAULT_THROTTLE_RATES = {
    "auth": "10/min",
    "scan": "60/min",
    "isbn": "30/min",
    "default": "60/min",
}
```

Les `throttle_scope` seront câblés sur les ViewSets dans Task #16 (API REST OfeliaScan). Rien à ajouter à ce stade.

### Reset administrateur (§9.3) — **différé**

`recovery_key` + procédure boot avec `recovery.key` sur clé USB : intégré au Wizard de premier démarrage (Task #15) et à la couche shell d'install (Task #18).

## Tests (`apps/accounts/tests/`)

22 tests, tous verts :

| Fichier | Couverture |
|---|---|
| `test_roles.py::TestRoleSignal` | Création librarian → Group librarian, createsuperuser → role SUPERADMIN forcé + is_staff=True, changement de rôle = changement de Group, setup_roles resync les users pré-existants |
| `test_roles.py::TestRolePermissions` | librarian a `catalog.add_item`/`loans.add_loan`, pas `core.change_setting` / `accounts.add_user` / `catalog.delete_bibliographicrecord` ; contributor_api a `add_bibliographicrecord`/`add_item` seulement ; readonly a `view_*` seulement ; superuser bypasse |
| `test_permissions_helpers.py::TestRequireRoleDecorator` | anonymous → 302 login, mauvais rôle → PermissionDenied, bon rôle → 200, superuser → 200 |
| `test_permissions_helpers.py::TestHasRoleDRF` | refuse anonymous / mauvais rôle, accepte bon rôle, ouvert si pas de required_roles |
| `test_audit.py::TestAuditLog` | création Member, update BibliographicRecord, set Setting, création User → enregistrent CREATE/UPDATE dans `auditlog.LogEntry` |

```
$ docker compose -f docker-compose.dev.yml exec -T web pytest apps/accounts/tests/ -v
22 passed in 6.07s
```

## Vérifications réelles

- `setup_roles` : crée 4 Groups, permissions assignées : `superadmin=0 (bypass), librarian=36, contributor_api=9, readonly=11`.
- `manage.py check` : 0 issue.
- Boot dev-entrypoint : `setup_roles` tourne après `seed_defaults` sans erreur.

## Suite

- Task #5 (Sprint 2) : sélecteur de langue + page de login custom + premier écran utilisant `@require_role`.
- Task #15 (Sprint 3) : wizard d'install qui génère le superadmin initial + recovery_key.
- Task #16 (Sprint 4) : DRF ViewSets avec `permission_classes = [IsAuthenticated, HasRole]` et `throttle_scope` câblés.
