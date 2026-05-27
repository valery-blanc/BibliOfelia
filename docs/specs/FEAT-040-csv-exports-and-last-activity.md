# FEAT-040 — Exports CSV des rapports + date de dernière activité

**Status :** IN PROGRESS
**Date :** 2026-05-27
**Sprint :** 13
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.6 (rapports)

---

## Contexte

La page `/reports/` (FEAT-011) propose actuellement :
- listes imprimables (retards, réservations à retirer, inactifs),
- export CSV des prêts sur une période,
- rapport annuel PDF.

Manquent pour les bibliothécaires (demande Val 2026-05-27) :
1. Export CSV **catalogue complet** (1 ligne par exemplaire, toutes les infos
   notice + exemplaire sauf image).
2. Export CSV des **prêts en cours** (ACTIVE + OVERDUE) et **réservations en
   cours** (PENDING + READY_FOR_PICKUP).
3. Sur `/reports/inactive/` : ajouter un **export CSV** des deux tableaux et
   une **colonne « Dernière activité »** (ou « Aucune activité »).

## Comportement

### 3 nouveaux exports `/reports/`

| URL                                  | Contenu                                                                          |
|--------------------------------------|----------------------------------------------------------------------------------|
| `reports:catalog_csv`                | 1 ligne par exemplaire. Colonnes : `item_internal_id, item_ean13, item_state, item_status, item_location_code, item_acquisition_date, item_acquisition_source, item_donor, record_id, record_title, record_subtitle, record_authors, record_publisher, record_publication_year, record_language, record_isbn_13, record_isbn_10, record_category, record_tags, record_document_type, record_series_name, record_series_volume, record_summary` |
| `reports:active_loans_reservations_csv` | 2 sections (prêts puis réservations) dans un seul CSV ; entête `kind` discriminant `loan`/`reservation`. Colonnes communes : `kind, id, status, created_at, member_card, member_name, record_title, item_internal_id (vide pour reservation pending), due_or_expiry_date` |

### `/reports/inactive/`

- 2 boutons « Exporter CSV » à côté du bouton imprimer (1 pour les usagers,
  1 pour les exemplaires).
- 2 endpoints : `reports:inactive_members_csv`, `reports:inactive_items_csv`.
- Nouvelle colonne **« Dernière activité »** dans les 2 tableaux :
  - membres : `max(Loan.loan_date)` sur la jointure → format `YYYY-MM-DD`,
    ou littéral `« Aucune activité »` si jamais emprunté ;
  - exemplaires : idem (`max(Loan.loan_date)` sur les prêts de l'exemplaire).
- Le filtre `days` (seuil d'inactivité) reste appliqué : on n'affiche que les
  membres/exemplaires sans prêt depuis `days` jours. La colonne « dernière
  activité » montre donc soit une date antérieure au seuil, soit « Aucune
  activité ».

## Technique

- Étendre `apps/reports/services.py` :
  - `catalog_full_csv_rows()` itère `Item.objects.select_related('record',
    'location', 'record__category').prefetch_related('record__authors',
    'record__tags')`.
  - `active_loans_csv_rows()` + `active_reservations_csv_rows()` (sans
    pagination).
  - `inactive_members(days)` et `inactive_items(days)` annotent
    `last_activity=Max('loans__loan_date')`.
- Étendre `apps/reports/views.py` : 4 nouvelles vues, role `LIBRARIAN` +
  `SUPERADMIN` pour les exports (cohérent avec `loans_csv`), `READONLY`
  autorisé en lecture HTML de `/inactive/`.
- Étendre `apps/reports/urls.py` : 4 nouvelles routes.
- Mettre à jour `templates/reports/index.html` : 2 cards avec liens directs vers
  les nouveaux exports.
- Mettre à jour `templates/reports/inactive_list.html` : 2 boutons d'export
  + colonnes `Dernière activité`.
- Pas de migration (pure lecture).

## Tests

- `apps/reports/tests/test_csv_exports.py`
  - GET `catalog_csv` → 200, content-type, ligne par exemplaire, encodage UTF-8.
  - GET `active_loans_reservations_csv` → 2 sections, prêts ACTIVE + résa
    PENDING/READY.
  - GET `inactive_members_csv` + `inactive_items_csv` → respect du seuil
    `days`, colonne `last_activity` correcte (ou « Aucune activité »).
- Mise à jour des tests existants `inactive_list` pour la nouvelle colonne.

## Impact

- `apps/reports/services.py`, `views.py`, `urls.py`
- `templates/reports/index.html`, `templates/reports/inactive_list.html`
- `apps/reports/tests/` (nouveaux tests)
- `docs/specs/SPEC_BIBLIOFELIA.md` §6.6 (sous-section « Exports CSV »)
