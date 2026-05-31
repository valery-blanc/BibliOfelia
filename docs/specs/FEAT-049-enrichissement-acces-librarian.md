# FEAT-049 — Enrichissement métadonnées ouvert aux bibliothécaires

**Statut** : DONE (en attente déploiement Pi + test Val + commit)
**Date** : 2026-05-31
**Demande** : Val (chat) — « rendre accessible le menu d'enrichissement des
métadonnées aux bibliothécaires en plus des superadmins ».

## Contexte

L'enrichissement multi-sources (FEAT-031, `Avancé → Enrichissement métadonnées`)
était réservé au rôle **SUPERADMIN**. Les bibliothécaires cataloguent au
quotidien (saisie, scan caméra FEAT-046) ; il est naturel qu'ils puissent aussi
lancer un enrichissement pour compléter les notices, sans dépendre d'un
superadmin.

## Changement

Permission élargie de `SUPERADMIN` à **`LIBRARIAN + SUPERADMIN`** (READONLY reste
exclu, car l'enrichissement modifie le catalogue).

- `apps/core/admin_views.py` — les 3 vues passent à
  `@require_role(Role.LIBRARIAN, Role.SUPERADMIN)` :
  - `enrichment_index` (liste + formulaire)
  - `enrichment_start` (POST, crée le `EnrichmentJob` + enqueue django-q2)
  - `enrichment_detail` (suivi d'un job)
- `templates/core/advanced.html` — le lien « Enrichissement métadonnées » perd
  son garde `{% if user.is_superadmin %}`. Il se trouve déjà dans la section
  **Inventaire** gardée par `{% if user.is_librarian %}` (qui couvre LIBRARIAN
  **et** SUPERADMIN, cf. `accounts.models.User.is_librarian`), donc le simple
  retrait du garde interne suffit.

`require_role` accepte déjà plusieurs rôles (cf. `apps/printing/views.py`).

## Vérification (Docker dev local)

| Rôle | `GET enrichment_index` | Lien dans `/advanced/` |
|---|---|---|
| LIBRARIAN | 200 | visible |
| SUPERADMIN | 200 (`is_librarian` vrai) | visible |
| READONLY | 403 | masqué |

`manage.py check` : 0 issue. Aucun test n'asservissait l'accès superadmin-only
(les tests `test_enrichment.py` portent sur la logique de merge/run_job), donc
aucun test à corriger.

## Impact / limites

- Aucune migration, aucune nouvelle chaîne i18n.
- Le worker django-q2 reste requis pour l'exécution (inchangé).
- **Couplage commit** : `admin_views.py` et `advanced.html` sont aussi modifiés
  par FEAT-047 (en test, non commité) ⇒ FEAT-049 part dans le **même commit** que
  FEAT-047.
