# FEAT-011 — Dashboard, rapports, paramètres

Statut : DONE (validé Val 2026-05-22)
SPEC : §6.6

## Contexte

Compléter le tableau de bord (KPI + tendances + état système), ajouter les
rapports imprimables / exportables, et exposer les paramètres pour qu'un
superadmin puisse configurer la box sans passer par `/admin/` Django.

## Implémentation

### Dashboard (`apps/core/views.py:dashboard` + `templates/core/dashboard.html`)

- KPI : prêts en cours, retards, réservations prêtes, usagers, notices, exemplaires.
- Tendance prêts sur 30 jours (sparkline CSS).
- Top 10 ouvrages empruntés sur le mois et l'année (via `apps/reports/services.py:top_loaned_records`).
- Compteur d'usagers actifs et croissance du fonds (mois / année).
- État système : version, espace disque libre, dernière sauvegarde (alerte si > 24 h), état ZeroTier.

### Rapports (`apps/reports/`)

- `services.py` : agrégations (`loans_trend`, `top_loaned_records`,
  `active_members`, `collection_growth`, `overdue_loans`,
  `inactive_members`, `inactive_items`, `loans_period`, `annual_report`,
  `system_status`).
- `views.py` : index + listes imprimables (retards, inactifs,
  réservations à retirer) + export CSV des prêts + PDF rapport annuel.
- `forms.py` : `PeriodForm`, `YearForm`.
- `pdf.py` : génération du PDF annuel via ReportLab (déjà dans
  `requirements.txt`).
- Routes : `reports:index`, `reports:overdue`, `reports:reservations_pickup`,
  `reports:inactive`, `reports:loans_csv`, `reports:annual_pdf`.

### Paramètres (`apps/core/`)

- `forms.py` : `LibraryIdentityForm`, `LanguagesForm`, `BackupConfigForm`,
  `LabelFormatForm`, `ZeroTierForm` (chacun pilote des clés du modèle
  `Setting` JSON).
- `admin_views.py` : index des sections + édition + diagnostics + actions
  backup (cf. FEAT-014).
- Routes `core:settings_index`, `core:settings_section`,
  `core:diagnostics`, `core:backup_now`, `core:backup_restore`.
- Catégories, tags, emplacements, MemberCategory restent éditables via
  l'admin Django pour l'instant (gain de scope v1 — affiché dans
  l'index avec lien).

### Gestion des comptes (`apps/accounts/`)

- `forms.py` : `UserAdminForm` (création + édition + changement de mot de
  passe), `PasswordResetForm`.
- `views.py` : `user_list`, `user_create`, `user_edit`,
  `user_password_reset` (avec génération aléatoire 16 chars).
- Routes `accounts:user_list`, `accounts:user_create`,
  `accounts:user_edit`, `accounts:user_password_reset`.

### Accès

Toutes les vues paramètres + comptes : `@require_role(Role.SUPERADMIN)`.
Les rapports : `Role.LIBRARIAN | SUPERADMIN | READONLY` (lecture seule).

## Décisions

- **PDF généré côté Django** (pas une ressource statique pré-rendue) :
  permet de paramétrer le nom de la bibliothèque, l'année, le top, etc.
- **CSV streamé** via `csv.writer(response)` : pas de bibliothèque tierce.
- **Settings stockées en JSON** dans un seul modèle `Setting` (déjà
  existant) : évite l'inflation des migrations à chaque ajout de
  paramètre. Les formulaires lisent/écrivent les bonnes clés.
- **Pas de RBAC fin sur les rapports** : SUPERADMIN modifie tout, LIBRARIAN
  consulte tout, READONLY consulte tout sauf l'export CSV et le PDF
  (ces deux endpoints exigent LIBRARIAN+).

## Tests

- Aucun nouveau test (139 tests verts hérités). Sprint 5 (Task #17)
  ajoutera la couverture sur les rapports.
- Test fonctionnel Val : OK (2026-05-22).
