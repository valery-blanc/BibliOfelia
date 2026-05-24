# TASKS — BibliOfelia v1

Source de vérité de l'avancement v1. Une case `[x]` = livrable terminé et déployable. `[ ]` = à faire. `[!]` = bloqué (voir note).

Mise à jour : 2026-05-23 (Sprint 8 **CLOS** — FEAT-025 **validé Val 2026-05-23** : refonte design global, 23 templates métiers harmonisés sur le design system OFELIA. Lot A pilote validé en premier (record_detail, member_detail, reports/index, settings_index), puis Lots B+C+D livrés d'un bloc. Helpers CSS ajoutés (`.req`, `.help-hint`, `.field-error`, `.form-control`, `details.advanced-section`, `.isbn-row`, `.form-actions`), `_field.html` migré `.form-row` → `.field`. Découverte d'infra : templates **embarqués au build Docker**, pas bind-mountés → rebuild obligatoire pour tout changement de template (documenté dans FEAT-025). — Sprint 7 **CLOS** — FEAT-024 **validé Val 2026-05-23** : scanner caméra navigateur sur Android Firefox HTTPS OK, fallback OfeliaScan automatique en HTTP LAN, Chrome Android sans Play Store via `S.browser_fallback_url`, bouton Annuler pendant polling. Décision UX : caméra-d'abord automatique, pas de toggle utilisateur. Décision infra : pas de cert auto-signé. 3 commits Pi `d7c8e8f` → `9d2af81` → `e9993a5`. FEAT-023 **validé Val 2026-05-23** : banner dashboard → OfeliaScan ouvre → scan livre → retour BibliOfelia → fiche notice affichée, bout-en-bout fonctionnel. Modèle `ScanHandoff` + endpoints `/api/v1/scan-handoff[/{token}]` + JS `scan-handoff.js` + 4 boutons « Scanner » câblés. BUG-010 entrypoint Dockerfile + BUG-011 CSRF cookie HttpOnly + Chrome Android `intent://` URL résolus. Sprints 3/5/6 clos. Reste pour Sprint 7 : Android-side OfeliaScan déjà fonctionnelle côté Val (intent filter + activity scan-one + POST callback) — implémentation Android terminée hors repo. Prochain sprint : FEAT-024 scanner caméra navigateur (HTTPS).)

## Sprint 0 — Squelette

- [x] **Task #1** Squelette projet : Django + Docker dev + git init
  - [x] requirements.txt, requirements-dev.txt, pyproject.toml
  - [x] config/ (base/dev/prod/test settings, urls, wsgi, asgi)
  - [x] manage.py, .env.example, .gitignore
  - [x] Dockerfile (multi-stage dev/prod), Dockerfile.backup
  - [x] docker-compose.dev.yml et docker-compose.yml (prod keebee)
  - [x] scripts/entrypoint.sh, backup.sh, restore.sh, backup-crontab
  - [x] Stubs des 11 apps Django (apps/{core,accounts,catalog,members,loans,inventory,printing,reports,setup,api,tasks})
  - [x] User étendu (rôles), Setting, EAN13 generator (apps.core.ean)
  - [x] Middleware SetupRequiredMiddleware + handler exceptions DRF
  - [x] Templates base.html, dashboard, login (placeholders)
  - [x] Téléchargement Pico.css 2.x + HTMX 2.0.4 + Alpine 3.14.8 dans static/
  - [x] Téléchargement Inter font + Lucide icons (fait en Task #5 : `static/fonts/`, `static/icons/`)
  - [x] Test boot : `docker compose -f docker-compose.dev.yml up` → web + worker UP, API health 200, /setup/ rend (2026-05-21)
  - [x] **BUG-001** fix : `AUDITLOG_EXCLUDE_TRACKING_MODELS` retiré + `Q_CLUSTER.retry=120` (cf. docs/bugs/BUG-001-auditlog-q2-config.md)
  - [x] `scripts/dev-entrypoint.sh` ajouté (auto makemigrations + migrate + seed au boot dev) + worker `depends_on: web` + `sleep 5`
  - [x] Migrations initiales `apps/core/0001_initial.py` (Setting) + `apps/accounts/0001_initial.py` (User)
  - [x] Skill `/vb-init` appliqué : CLAUDE.md enrichi (Chemins, Task Tracking, Resuming Work, Doc Sync, Bug/Feat workflows, Cadence /clear, Infrastructure, Skills personnalisés)
  - [x] `MEMORY.md` mis à jour (feedback_sprint_clear)
  - [x] `git init` + remote `origin` = https://github.com/valery-blanc/BibliOfelia.git
  - [x] Premier commit `init: squelette projet (Task #1)` + push → commit `eca06e6`
  - [x] Commit fix BUG-001 + dev-entrypoint + migrations initiales + CLAUDE.md enrichi (validé par Val 2026-05-21)

## Sprint 1 — Domaine

- [x] **Task #2** Modèles de données (§5) — validé Val 2026-05-21
  - [x] `apps/catalog/models.py` : Author, Category, Tag, Location, BibliographicRecord, Item (avec auto-gen `internal_id` + `ean13` préfixe 290)
  - [x] `apps/members/models.py` : MemberCategory, Member (auto-gen `card_number` préfixe 291, `expiration_date` auto)
  - [x] `apps/loans/models.py` : Loan, InHouseConsultation, Reservation
  - [x] Indexes §5.3 : unique partiel ISBN, composites Item/Loan/Member
  - [x] FTS5 SQLite (`catalog/migrations/0002_fts5.py`) — table virtuelle + 5 triggers (insert/update/delete + M2M auteurs)
  - [x] Seed §5.2 étoffé : 16 Catégories + 5 MemberCategory dans `seed_defaults`
  - [x] Admin Django minimal (catalog/members/loans/accounts) pour navigation Sprint 1
  - [x] `python-dateutil` ajouté à `requirements.txt`
  - [x] `manage.py check` OK, `migrate` OK, smoke test Item/Member/Loan + FTS5 OK, admin /admin/* en 200
  - [x] Doc : `docs/specs/FEAT-002-data-models.md` + mise à jour `SPEC_BIBLIOFELIA.md` §5 (écarts + FTS5)
  - [x] Test Val OK : menus Catalogue/Usagers/Prêts visibles, création modèles OK (2026-05-21)
  - [x] Commit `FEAT-002: modèles de données v1 + FTS5 + seed`
- [x] **Task #3** i18n + modeltranslation (4 langues) — validé Val 2026-05-21
  - [x] `apps/catalog/translation.py` : `Category.name`, `Tag.name`
  - [x] `apps/members/translation.py` : `MemberCategory.name`
  - [x] Migrations `catalog/0003_translation_fields` + `members/0002_translation_fields` (ADD COLUMN `name_fr/en/es/mg`)
  - [x] Migrations backfill `catalog/0004_backfill_translation_fr` + `members/0003_backfill_translation_fr` (UPDATE name_fr = name)
  - [x] Admin : `Category/Tag/MemberCategory` héritent de `TranslationAdmin` (onglets par langue)
  - [x] Fix `mg` absent de `LANG_INFO` Django → enregistrement dans `config/settings/base.py`
  - [x] `locale/{fr,en,es,mg}/LC_MESSAGES/django.po` générés par `makemessages` (83 msgid extraits)
  - [x] `dev-entrypoint.sh` étoffé : `compilemessages` au boot (les `.mo` sont gitignorés)
  - [x] Smoke test ORM : backfill OK, switch FR/EN/ES OK, fallback MG→FR OK, edit form admin contient les 4 champs `name_<lang>`
  - [x] Doc : `docs/specs/FEAT-003-i18n-modeltranslation.md` + `SPEC §6.9` mis à jour
  - [x] Test Val OK : admin Category/Tag/MemberCategory affiche 4 onglets de langue (2026-05-21)
  - [x] Commit `FEAT-003: i18n + modeltranslation 4 langues`
- [x] **Task #4** Auth, rôles, audit, throttling — validé Val 2026-05-21
  - [x] `apps/accounts/groups.py` : ROLE_PERMS mapping `Role → [(app, codename)]`
  - [x] `apps/accounts/signals.py` : post_save User → sync role/is_staff/Group (is_superuser → SUPERADMIN forcé)
  - [x] `apps/accounts/management/commands/setup_roles.py` : crée Groups + assigne perms (idempotent, resync users existants)
  - [x] `apps/accounts/permissions.py` : `@require_role(*roles)` + `HasRole` (DRF)
  - [x] `apps/core/apps.py:ready()` : enregistre auditlog sur Setting, BibliographicRecord, Item, Member, Loan, User (§9.6)
  - [x] `scripts/dev-entrypoint.sh` : ajout `setup_roles` au boot
  - [x] Tests pytest 22/22 verts (`apps/accounts/tests/test_roles.py`, `test_permissions_helpers.py`, `test_audit.py`)
  - [x] `manage.py check` 0 issue, boot dev OK avec setup_roles
  - [x] Doc : `docs/specs/FEAT-004-auth-roles-audit.md` + `SPEC §9.2/§9.6` mis à jour
  - [x] Test Val OK : user librarian créé via /admin/ avec Group librarian et is_staff=False (2026-05-21)
  - [x] Commit `FEAT-004: auth, rôles, audit, throttling`
  - [x] Fin Sprint 1, prêt pour `/clear` + Sprint 2

## Sprint 2 — UI et workflows métier

> Sprint codé + documenté les 2026-05-21/22. Suite de tests : **117 passed**
> (`docker compose -f docker-compose.dev.yml run --rm web pytest`).

- [x] **Task #5** UI base (Pico/HTMX/Alpine, layout, recherche globale)
  - [x] Assets locaux : Inter (`static/fonts/`) + 31 icônes Lucide (`static/icons/`)
  - [x] Tag `{% icon %}` (`apps/core/templatetags/biblio_icons.py`)
  - [x] `base.html` : nav par rôle, recherche globale, sélecteur de langue, compteurs, aide, mode simple/avancé
  - [x] Recherche globale `core:search` + `apps/core/search.py` (classification EAN/ISBN/texte + FTS5)
  - [x] `core:toggle_advanced`, `core:help`, dashboard avec KPIs réels
  - [x] `config/settings/test.py` : retrait de `SetupRequiredMiddleware` pour les tests de vues
  - [x] **BUG-002** corrigé : boucle de redirection sur `/` (RedirectView racine retiré)
  - [x] Doc : `FEAT-005-ui-base.md`, `BUG-002-root-redirect-loop.md`
  - [x] Tests écrits : `apps/core/tests/test_search.py`, `test_ui.py`
- [x] **Task #6** Catalogage (§6.1)
  - [x] `BibliographicRecordForm` (auteurs texte libre), `ItemForm`, `ItemBulkCreateForm`
  - [x] Vues notices (liste FTS + filtres, détail, CRUD), exemplaires (création groupée, édition, mise au rebut)
  - [x] Lookup ISBN OpenLibrary (`apps/catalog/openlibrary.py` + endpoint HTMX `isbn_lookup`)
  - [x] Templates `templates/catalog/`
  - [x] Doc : `FEAT-006-catalogage.md` ; Tests : `apps/catalog/tests/`
- [x] **Task #7** Gestion usagers (§6.2)
  - [x] `MemberForm` + vues (liste, fiche, historique, inscription, édition)
  - [x] `apps/members/services.py` : remplacement de carte, renouvellement, expiration
  - [x] Commande `expire_members` (tâche django-q2 quotidienne)
  - [x] Templates `templates/members/`
  - [x] Doc : `FEAT-007-gestion-usagers.md` ; Tests : `apps/members/tests/`
- [x] **Task #8** Prêts/Retours/Renouvellements/Perdus (§6.3)
  - [x] `apps/loans/services.py` : durée, vérifications, prêt, retour, renouvellement, perte
  - [x] Vues : workflow prêt (panier session), retour, renouvellement, livre perdu, consultation
  - [x] Templates `templates/loans/`
  - [x] Doc : `FEAT-008-prets-retours.md` ; Tests : `apps/loans/tests/`
- [x] **Task #9** Réservations (§6.4)
  - [x] `services.py` : création, satisfaction FIFO, annulation, expiration
  - [x] Vues : création depuis notice, liste à honorer, annulation
  - [x] Commande `expire_reservations` (tâche django-q2 quotidienne)
  - [x] Doc : `FEAT-009-reservations.md` ; Tests : `apps/loans/tests/test_services.py`/`test_views.py`
- [x] **Task #10** Récolement (§6.5)
  - [x] Modèles `InventorySession` / `InventoryScan` + migration `0001_initial` (rédigée à la main)
  - [x] `apps/inventory/services.py` : périmètre, pointage, rapport de divergences
  - [x] Vues : sessions, détail/pointage, clôture/réouverture/validation, rapport
  - [x] Templates `templates/inventory/`
  - [x] Doc : `FEAT-010-recolement.md` ; Tests : `apps/inventory/tests/`
- [x] Exécuter `pytest` dans Docker — **117 passed** (2026-05-22)
- [x] `makemigrations --check` — **No changes detected** : migration inventory `0001` conforme au modèle
- [x] Corrections suite au test de Val (2026-05-22) :
  - [x] **BUG-003** double prêt — `check_item_loanable` s'appuie sur la table `Loan` ; message « Cet ouvrage est déjà prêté » ; messages du moteur de prêt en `gettext_lazy` (traduits 4 langues)
  - [x] **BUG-004** récolement — exemplaires prêtés exclus du périmètre attendu
  - [x] **BUG-005** i18n — traduction complète `en`/`es`/`mg` (~300 chaînes) + `prefix_default_language=True`
  - [x] Docs : `BUG-003`, `BUG-004`, `BUG-005`, SPEC §6.3/§6.5/§6.9 mises à jour
- [x] Test Val des correctifs (2026-05-22 : double prêt / récolement / i18n confirmés OK)
- [x] Commit `d361965` + push `origin/main` (2026-05-22)
- [x] Commit unique Sprint 2 (code + docs + TASKS.md) — commit `d361965` poussé `origin/main`

## Sprint 3 — Connexion OfeliaScan (appairage + lookup ISBN)

> Re-priorisé le 2026-05-22 (demande de Val) : l'application Android OfeliaScan
> est prête (découverte mDNS + appairage + lookup ISBN) et doit être testée. Le
> contrat d'API est figé par `docs/specs/SPEC-CORR-001-contrat-api-box.md`,
> appliqué dans `SPEC §6.10`. Si la box respecte ce contrat à la lettre,
> OfeliaScan n'a aucune modification à faire.

- [x] **Task #16** API REST OfeliaScan — authentification, appairage, lookup ISBN (§6.10) — validé Val 2026-05-22 (conformité contrat), commit `68375df`
  - [x] Auth JWT : `POST /auth/login`, `/auth/refresh`, `/auth/logout` — serializers custom (`apps/api/serializers.py`) émettant `access_token` / `refresh_token` / `token_type` / `expires_in`
  - [x] SimpleJWT : `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` + app `token_blacklist` (déjà configurés, exploités par `/auth/refresh` et `/auth/logout`)
  - [x] `GET /pairing/info` — sans auth, champ `api_base` (réglage `API_BASE_PATH`)
  - [x] `GET /isbn/{isbn}` — champ `publication_year`, `isbn` toujours présent ; cache local `BibliographicRecord` + fallback OpenLibrary
  - [x] `GET /health` — champ `status` garanti, auth requise ; healthcheck Docker repointé sur `/pairing/info`
  - [x] Format d'erreur uniforme `{error:{code,message,details}}` (handler `apps/api/exceptions.py` + 404 ISBN)
  - [x] Tests API : `apps/api/tests/test_api.py` — 16 tests verts
  - [x] Doc : `docs/specs/FEAT-016-api-ofeliascan.md` + `SPEC §6.10` mis à jour
  - [x] **SPEC-CORR-002** : `/pairing/info` renvoie `base_url` (URL absolue, nom de champ aligné sur le `PairingInfoDto` d'OfeliaScan) au lieu de `api_base` — lève le conflit de routage `/biblio/` vs `/bibliofelia/`
- [x] **Task #19** Publication mDNS/DNS-SD `_bibliofelia._tcp.` (SPEC §6.10 / SPEC-CORR-001 §7) — *validé Val 2026-05-23 (déploiement Pi + test découverte réelle)*
  - [x] Commande `generate_avahi_service` (`apps/core/management/commands/`) : génère `/etc/avahi/services/bibliofelia.service` (TXT : `library_name`, `version`, `api_base`) à partir des `Setting` + réglages ; options `--output` / `--dry-run`
  - [x] Réglages `AVAHI_SERVICE_PATH` + `MDNS_SERVICE_PORT` (`config/settings/base.py`)
  - [x] Tests : `apps/core/tests/test_avahi.py` — 6 verts ; suite complète **138 passed**
  - [x] Doc : `docs/specs/FEAT-019-mdns-avahi.md` + `SPEC §6.10` mis à jour
  - [x] Régénération au wizard de premier démarrage — débloqué par Task #15 : `apply_wizard()` appelle `generate_avahi_service`
  - [x] Bind-mount `/etc/avahi/services/` — fait dans la compose keebee (FEAT-020 / Task #18) ; `avahi-daemon` installé par `bootstrap.sh` keebee
- [x] Test Val : découverte + appairage OfeliaScan + scan ISBN bout-en-bout (sur la Pi, après Task #18) — validé Val 2026-05-23

## Sprint 4 — Hors workflow principal

> Codé d'un bloc le 2026-05-22, **validé par Val 2026-05-22**, commité d'un bloc avec BUG-006 + FEAT-017. Suite de tests : **139 passed**.

- [x] **Task #11** Dashboard, rapports, paramètres (§6.6) — *validé Val 2026-05-22*
  - [x] `apps/reports/services.py` — agrégations (trend 30j, top10 mois/année, active members, growth, system_status, listes pour rapports, annual_report)
  - [x] `apps/reports/views.py` + `forms.py` + `pdf.py` (ReportLab annuel) + `urls.py` + templates `templates/reports/`
  - [x] Dashboard enrichi (`apps/core/views.py:dashboard` + `templates/core/dashboard.html` — sparkline + top + état système)
  - [x] Paramètres : `apps/core/forms.py` (identité, langues, backup, étiquettes, ZeroTier) + `apps/core/admin_views.py` (settings_index/section/diagnostics) + templates `templates/core/admin/`
  - [x] Gestion comptes : `apps/accounts/forms.py` (UserAdminForm, PasswordResetForm) + `apps/accounts/views.py` (user_list, create, edit, password_reset auto/manuel) + templates `templates/accounts/user_*`
  - [x] CSS additionnel : sparkline, dashboard-grid, settings-nav, breadcrumb, `msg-info`
  - [x] Doc : `docs/specs/FEAT-011-dashboard-rapports-parametres.md` + SPEC §6.6 mis à jour
- [x] **Task #12** Impression étiquettes + cartes (§6.7) — *validé Val 2026-05-22*
  - [x] `apps/printing/services.py` (render_item_labels_pdf, render_member_cards_pdf, submit_to_cups) — python-barcode + ReportLab
  - [x] `apps/printing/views.py` + `urls.py` + templates `templates/printing/`
  - [x] CUPS optionnel : pycups importé localement (échec silencieux en dev Windows → fallback PDF)
  - [x] Format paramétrable via `Setting.label_format` (FEAT-011)
  - [x] Doc : `docs/specs/FEAT-012-impression-etiquettes-cartes.md` + SPEC §6.7 mis à jour
- [x] **Task #13** Notifications offline + alertes (§6.8) — *validé Val 2026-05-22*
  - [x] `apps/members/notifications.py` (member_alerts + navbar_counts) — centralisation
  - [x] Refacto `apps/loans/views.py` (lend), `apps/core/context_processors.py` (notifications), `apps/members/views.py` (member_detail)
  - [x] Bandeau d'alertes sur fiche membre (`templates/members/member_detail.html`)
  - [x] Liste imprimable réservations à retirer (`reports:reservations_pickup`)
  - [x] Doc : `docs/specs/FEAT-013-notifications-offline.md` + SPEC §6.8 mis à jour
- [x] **Task #14** Sauvegardes locales + cloud (§8) — *validé Val 2026-05-22*
  - [x] `apps/tasks/backup.py` — `run_backup()` (sqlite3 .backup + integrity_check + rotation 24h/7j/35j/400j + rsync media + cloud rclone opt-in) + `restore_from_file()`
  - [x] `apps/tasks/scheduling.py` + commande `setup_schedules` (3 Schedule django-q2 : backup horaire, expire cartes, expire réservations)
  - [x] Commandes `manage.py run_backup` + `restore_backup`
  - [x] Vues admin : bouton « Sauvegarder maintenant » + upload restauration (`core:backup_now`, `core:backup_restore`)
  - [x] `Setting.last_backup` exploité par le dashboard (alerte > 24 h)
  - [x] `dev-entrypoint.sh` : appel à `setup_schedules` au boot dev
  - [x] Doc : `docs/specs/FEAT-014-sauvegardes.md` + SPEC §8 mis à jour
- [x] **Task #15** Wizard premier démarrage + données démo (§11.3-11.4) — *validé Val 2026-05-22*
  - [x] `apps/setup/forms.py` — 8 formulaires d'étape
  - [x] `apps/setup/views.py` — wizard multi-step session-based (`wizard_index`, `wizard_step`, `wizard_finalize`)
  - [x] `apps/setup/services.py:apply_wizard()` — persistance Setting + création superadmin + recovery_key (hash uniquement) + setup_schedules + generate_avahi_service (lève le blocage Task #19 wizard)
  - [x] `apps/setup/demo.py` — install/remove démo (50 notices, 80 exemplaires, 20 membres, 15 prêts, marqueur `[DEMO]`)
  - [x] Commande `manage.py remove_demo`
  - [x] Templates `templates/setup/` (step, completed, already_done — standalone, hors `base.html`)
  - [x] Doc : `docs/specs/FEAT-015-wizard-premier-demarrage.md` + SPEC §11.3-11.4 mises à jour

> **Sprint 3 reste à tester sur la Pi** (Task #19 mDNS découverte réelle, Task #16 lookup ISBN bout-en-bout). Une fois la Pi accessible, l'`avahi-daemon` lit le fichier généré par `generate_avahi_service` (déclenché en fin de wizard désormais).

### Corrections suite au test de Val (2026-05-22)

- [x] **BUG-006** i18n Sprint 4 : `accounts/` déplacé sous `i18n_patterns` (`/fr/accounts/users/` répond) ; chaînes EN/ES/MG complétées (0 fuzzy, 0 untranslated) ; doc `docs/bugs/BUG-006-i18n-sprint4-urls-and-strings.md` + SPEC §6.9 mise à jour.
- [x] **FEAT-017** Navigation « Avancé » + page Connexion OfeliaScan + « Mon compte »
  - [x] Onglet « Avancé » (`core:advanced`) : index des outils hors-workflow (Impression, Rapports, Inventaire, Administration), liens explicités
  - [x] Barre principale allégée : suppression « Tableau de bord » + « Récolement » ; icône logo `book-open` → `house`
  - [x] Menu utilisateur : suppression « Mode avancé » + « Administration » ; ajout « Mon compte » (auto-édition, formulaire restreint sans escalade)
  - [x] Page Connexion OfeliaScan (`core:ofeliascan`) : adresse box + identifiants `contributor_api` (login/mot de passe en clair, création/révocation)
  - [x] Renommage UI « Récolement » → « Inventaire »
  - [x] Nouveaux SVG `static/icons/house.svg` + `user.svg`
  - [x] i18n : 545 chaînes EN/ES/MG (0 fuzzy, 0 untranslated)
  - [x] Doc : `docs/specs/FEAT-017-navigation-avancee-ofeliascan.md` + SPEC §6.5/§6.6/§6.10/§10.2
- [x] **FEAT-018** Terminologie « code Ofelia » + rapport d'inventaire enrichi — *validé Val 2026-05-22*
  - [x] Libellé « EAN13 » → « Code Ofelia » : `record_detail.html`, `labels_picker.html`, `inactive_list.html`, `advanced.html`
  - [x] Page d'impression : titre + onglet « Étiquettes codes Ofelia » (`labels_picker.html`) + lien aligné dans `advanced.html`
  - [x] `session_detail.html` : « Pointer un exemplaire » → « Scanner ou saisir le code Ofelia d'un document » ; placeholder → « Scanner le code Ofelia »
  - [x] `session_report.html` : colonnes « Code Ofelia » + « ISBN » sur les manquants ; codes ajoutés sur les hors périmètre
  - [x] i18n : `makemessages -a --no-obsolete` + traductions EN/ES/MG (0 fuzzy, 0 untranslated) + `compilemessages`
  - [x] Tests : `apps/inventory` + `apps/printing` + `test_ui.py` — 22 passed
  - [x] Doc : `docs/specs/FEAT-018-code-ofelia.md` + SPEC §5.2/§6.5/§6.7
  - [x] Test Val OK (2026-05-22) + commit unique

## Sprint 5 — API complète + qualité

- [x] **Task #20** API REST OfeliaScan — sessions de scan catalogage + endpoints récolement (FEAT-021)
  - [x] `docs/specs/FEAT-021-api-scan-sessions.md` — spec alignée sur le vrai contrat OfeliaScan
  - [x] Modèles `ScanSession` + `ScanItem` (`apps/catalog/models.py`) + migration manuelle `catalog/0005_scan_sessions.py`
  - [x] Flag `mobile_created` sur `InventorySession` + migration `inventory/0002_mobile_created.py`
  - [x] Service `finalize_scan_session()` (`apps/api/services.py`) — sync, transaction, lookup ISBN puis create-or-add-copies
  - [x] Helper `get_session_for_user()` (`apps/api/permissions.py`) — ownership contributor_api (404, pas 403, pour ne pas fuir l'existence)
  - [x] Serializers `ScanItemsBatchInput`, `InventoryItemsBatchInput`, `ScanSessionCreateInput`, `InventorySessionCreateInput` (`apps/api/serializers.py`)
  - [x] 6 endpoints (`apps/api/views.py` + `urls.py`) : `POST /scan-sessions`, `/items`, `/finalize`, `POST /inventory-sessions`, `/items`, `/close`
  - [x] Tests : `apps/api/tests/test_scan_sessions.py` (10 cas) + `test_inventory_api.py` (7 cas)
  - [x] SPEC §6.10 réécrite (sections « Sessions de scan » et « Récolement ») + entête de version
  - [x] Déploiement Pi + test OfeliaScan (envoi listes de livres bout-en-bout) — validé Val 2026-05-22
  - [x] **BUG-008** fix récolement ISBN : lookup par isbn_13/isbn_10 en fallback du code Ofelia interne + multi-exemplaires — validé Val 2026-05-22

- [x] **Task #17** Tests (pytest-django, coverage 70%) — validé Val 2026-05-23 : objectif relâché, les **178 tests verts** (apps/api + catalog + core + inventory + loans + members + reports + setup) couvrent les workflows métiers critiques et le contrat API OfeliaScan ; la mesure de couverture chiffrée reste un nice-to-have post-v1.

## Sprint 6 — Déploiement

- [x] **Task #18** Intégration keebee : déploiement sur la Ofelia Box (FEAT-020) — validé Val 2026-05-23
  - Cohabitation avec Koha (qui reste sur `/biblio/` ; BibliOfelia sur `/bibliofelia/`)
  - [x] `docs/specs/FEAT-020-integration-keebee.md`
  - [x] BibliOfelia : réglage `SECURE_COOKIES` (`base.py` + `prod.py`)
  - [x] BibliOfelia : `collectstatic` ajouté à `scripts/entrypoint.sh`
  - [x] BibliOfelia : `API_BASE_PATH` par défaut corrigé `/biblio/` → `/bibliofelia/`
  - [x] BibliOfelia : `docker-compose.yml` aligné (référence keebee : web + worker, `edubox-net`)
  - [x] BibliOfelia : `SPEC §4/§11` mis à jour
  - [x] keebee : `setup/app.py` + `setup/templates/index.html` (carte wizard BibliOfelia)
  - [x] keebee : `docker-compose.yml` (services `bibliofelia` + `bibliofelia-worker`)
  - [x] keebee : `nginx/conf.d/ofelia-locations.inc` (`location /bibliofelia/`)
  - [x] keebee : `portal/index.html` (tuile) + `healthcheck/app.py`
  - [x] keebee : `bootstrap.sh` (installe `avahi-daemon`)
  - [x] keebee : `docs/specs/FEAT-029-bibliofelia.md` + `specs_keebee.md` + `TASKS.md`
  - Build multi-arch : abandonné — keebee clone + build sur la Pi (décision Val 2026-05-22)
  - [x] Déploiement sur la Pi `192.168.0.147` + test Val (portail → wizard → connexion) — OK 2026-05-22
  - [x] **BUG-007** wizard 500 fin d'install : `install_demo()` plantait sur la contrainte UNIQUE `isbn_13` ; fix `""` → `None` (`apps/setup/demo.py`) + doc + SPEC §11.4
  - [x] **BUG-009** CSRF_TRUSTED_ORIGINS manquant : login impossible depuis domaine externe (ZeroTier) — ajout variable dans `docker-compose.yml` ; doc `docs/bugs/BUG-009-csrf-trusted-origins.md`
  - [x] **FEAT-022** Refonte UI design OFELIA : tuiles, tile strip, page head, polices Bricolage Grotesque/DM Sans, ofelia.css, login stylé, logo OFELIA, 17 icônes Lucide — validé Val 2026-05-23 ; doc `docs/specs/FEAT-022-refonte-ui-design-ofelia.md`
  - [x] Pi : `/opt/edubox/bibliofelia/` converti en repo git autonome (origin = GitHub BibliOfelia/main) — wizard peut désormais faire `git pull --ff-only` pour les mises à jour ; keebee `FEAT-029-bibliofelia.md` mis à jour

## Sprint 7 — Scanner depuis le site web

> Les boutons « Scanner » de l'UI ne faisaient que décorer un champ de saisie
> texte. On les rend fonctionnels par étapes : d'abord en déléguant à
> OfeliaScan (FEAT-023, cible bibliothécaires Android), ensuite avec un
> scanner caméra navigateur pour les autres clients (FEAT-024, nécessite
> HTTPS sur la box).

- [x] **Task #21** FEAT-023 — Handoff single-scan OfeliaScan (BibliOfelia)
  - [x] Modèle `apps/api/models.py:ScanHandoff` (token UUID, target_kind, state, value, value_kind, expires_at TTL 5 min, completed_by audit) + migration `apps/api/migrations/0001_initial.py`
  - [x] Serializers `ScanHandoffCreateInputSerializer` / `ScanHandoffSubmitInputSerializer` (validation `cancelled=true` vs `value` requis)
  - [x] Endpoints (`apps/api/views.py` + `urls.py`) : `POST /scan-handoff` (création, librarian/superadmin), `GET /scan-handoff/{token}` (polling créateur), `POST /scan-handoff/{token}` (callback JWT OfeliaScan)
  - [x] Permission helpers `_can_create_handoff` / `_can_view_handoff` (404 pour les non-propriétaires, pas 403)
  - [x] Frontend : `static/js/scan-handoff.js` (clic `.js-scan-handoff` → POST handoff → ouverture deep-link → polling 700 ms → injection valeur + autosubmit OU redirection dispatch-url) ; config JSON injectée dans `base.html`
  - [x] Templates : `loans/lend.html` (Scanner la carte + Scanner un livre, autosubmit), `loans/return.html` (Enregistrer le retour, autosubmit), `core/dashboard.html` (banner → redirige vers `core:search?q=<value>`)
  - [x] Tests : `apps/api/tests/test_scan_handoff.py` — 18 cas verts (création par rôle, polling ownership/superadmin, soumission JWT, normalisation, annulation, double soumission 409, expiration 410, round-trip complet)
  - [x] Doc : `docs/specs/FEAT-023-scan-handoff-ofeliascan.md` (BibliOfelia + contrat Android) + SPEC §6.10 nouvelle sous-section « Handoff single-scan »
  - [x] Déploiement Pi (rebuild conteneurs + migration `api.0001_initial`) — 2026-05-23
  - [x] **BUG-010** entrypoint Docker prod non exécutable au rebuild (Windows git ne pose pas l'exec bit) : `chmod +x /app/scripts/*.sh` ajouté au Dockerfile (cibles dev + prod) — `docs/bugs/BUG-010-entrypoint-exec-bit.md`
  - [x] **BUG-011** scan-handoff POST silencieusement KO en prod (CSRF_COOKIE_HTTPONLY=True → JS ne pouvait pas lire `csrftoken`) : token rendu par `{% csrf_token %}` injecté dans `#scan-handoff-config`, JS utilise `cfg.csrfToken` au lieu de `getCookie('csrftoken')` — `docs/bugs/BUG-011-scan-handoff-csrf-token.md`
  - [x] Deep-link Chrome Android : ajout d'`android_intent_url` (`intent://scan-one?…#Intent;scheme=ofeliascan;package=org.zitoon.ofeliascan;end`) dans la réponse `POST /scan-handoff` ; UA-sniff côté JS (Chrome/Samsung/Edge Android → intent, sinon scheme custom) ; réglage `OFELIASCAN_ANDROID_PACKAGE` (défaut `org.zitoon.ofeliascan`). Chrome récent bloque silencieusement `ofeliascan://` via `window.location.href` pour des raisons anti-deeplink-spam.
  - [x] Test Val 2026-05-23 : banner dashboard → OfeliaScan ouvert → scan livre → retour BibliOfelia → fiche notice affichée. Bout-en-bout fonctionnel. Les boutons `loans/lend/lend.html` et `loans/return/return.html` utilisent le même JS, donc validés implicitement.
  - [x] **Côté OfeliaScan Android** (hors repo BibliOfelia) : intent filter `ofeliascan://scan-one`, écran de scan unique, POST callback — implémenté par Val 2026-05-23, validé en bout-en-bout depuis le dashboard.

- [x] **Task #22** FEAT-024 — Scanner caméra navigateur (caméra-d'abord, fallback OfeliaScan auto) — validé Val 2026-05-23
  - [x] `docs/specs/FEAT-024-scanner-camera-navigateur.md` — spec
  - [x] Lib `static/js/html5-qrcode.min.js` v2.3.8 vendorée (375 KB, Apache-2.0)
  - [x] `static/js/scan-handoff.js` refacto : `window.BibliOfelia.scan = {applyResult, flashMessage, setBusy, readMode}` + court-circuit vers mode caméra si `localStorage['bibliofelia.scan-mode']==='camera'` && `isSecureContext`
  - [x] `static/js/scan-camera.js` : lazy-load lib, modal viseur, `facingMode: environment`, formats EAN-13/EAN-8/UPC/CODE_128/CODE_39/QR/ITF, gestion `NotAllowedError` / `NotFoundError`, fallback gracieux
  - [x] `static/js/scan-mode-toggle.js` : auto-injecte chevron + popover sur chaque `.js-scan-handoff`, persistance localStorage, option Caméra grisée hors `isSecureContext`
  - [x] `static/css/ofelia.css` : `.scan-split`, `.scan-mode-toggle`, `.scan-mode-popover`, `.scan-camera-modal` (480 px desktop / full-screen mobile)
  - [x] `templates/base.html` : `#scan-mode-i18n` (13 chaînes) + chargement des 3 JS en defer
  - [x] i18n : 13 nouvelles chaînes traduites EN/ES/MG (FR = msgid par défaut)
  - [x] `pytest` → 179 passed (non-régression) ; `manage.py check` 0 issue
  - [x] **Cert auto-signé écarté** (décision Val 2026-05-23) : feature active uniquement en HTTPS (accès internet)
  - [x] Déploiement Pi + test Val — **validé Val 2026-05-23** (Android Firefox HTTPS : caméra interne ouvre dans la page, scan d'un livre OK ; Android Chrome sans OfeliaScan = plus de redirection Play Store ; bouton Annuler fonctionnel)
  - [x] **Itération 1 → 2** : suppression du toggle UI (« pas pratique, ne marche pas »), passage à caméra-d'abord automatique avec fallback OfeliaScan
  - [x] **Itération 2 → 3** : diag verbose (flashMessage indique la raison technique du fallback), `S.browser_fallback_url=` sur intent Chrome Android, bouton « Annuler » pendant le polling OfeliaScan
  - [x] 3 commits poussés : `d7c8e8f` (initial), `9d2af81` (rev caméra-d'abord), `e9993a5` (diag + Chrome fix + Annuler)

## Sprint 8 — Refonte design global (FEAT-025) — CLOS

> Sprint clos 2026-05-23, validé Val. Voir `docs/specs/FEAT-025-refonte-design-global.md`.
> Démarche : Lot A pilote (4 URLs) → validation Val → Lot B+C+D livrés d'un bloc → validation Val finale.

- [x] **Task #23** FEAT-025 — Refonte design global (23 templates) — validé Val 2026-05-23
  - [x] Spec `docs/specs/FEAT-025-refonte-design-global.md`
  - [x] **Lot A — pilote** : record_detail, member_detail, reports/index, settings_index → validation Val OK
  - [x] **Lot B — listes** (5 templates Pico restants) : user_list, session_list, overdue_list, inactive_list, reservations_pickup *(record_list, member_list, reservations déjà refondus à FEAT-022)*
  - [x] **Lot C — formulaires** (9 templates) : record_form, _record_form, item_form, record_confirm_delete, member_form, user_form, reservation_form, session_form, password_reset
  - [x] **Lot D — reste** (13 templates) : session_detail, session_report, consultation, mark_lost, settings_section, backup_restore, diagnostics, ofeliascan, labels_picker, cards_picker, period_error, help, member_history
  - [x] Helpers CSS ajoutés à `static/css/ofelia.css` : `.req`, `.help-hint`, `.field-error`, `.form-control`, `details.advanced-section`, `.isbn-row`, `.form-actions`
  - [x] `templates/partials/_field.html` migré de `.form-row` (inexistant) vers `.field` (existe dans ofelia.css)
  - [x] Déploiement Pi : tar templates + ofelia.css → scp → extract → docker compose build → up
  - [x] Découverte d'infrastructure : templates **embarqués au build**, pas bind-mountés → rebuild obligatoire pour tout changement de template (documenté dans FEAT-025)
  - [x] SPEC §10.2 mise à jour (sous-section FEAT-025), entête de version FEAT-025
  - [x] Test Val OK 2026-05-23 (toutes les pages OK)

## Sprint 9 — Suppressions / désactivation / enrichissement métadonnées

> Ouvert le 2026-05-23. 6 nouvelles features (cf. `temp.txt`) regroupées en un sprint unique.
> Ordre d'implémentation : FEAT-026 → 027 → 028 → 029 → 030 → 031.

### FEAT-026 — Suppression en masse d'ouvrages depuis le catalogue (admin)
- [x] Doc `docs/specs/FEAT-026-bulk-delete-records.md`
- [x] Vue `record_bulk_delete_confirm` + `record_bulk_delete` + URLs (superadmin)
- [x] Template `record_list.html` : colonne checkbox + barre d'action (Alpine)
- [x] Template `record_bulk_delete.html` : confirmation avec impacts
- [x] CASCADE manuel : prêts actifs → LOST, résa actives → CANCELLED, puis delete (Item.record=CASCADE)
- [x] Tests : `apps/catalog/tests/test_bulk_delete.py` (6 cas)

### FEAT-027 — Suppression définitive d'un exemplaire (librarian + admin)
- [x] Doc `docs/specs/FEAT-027-delete-item.md`
- [x] Vue `item_delete` + URL + bouton sur record_detail.html à côté de "Pilonner"
- [x] Prêts actifs → LOST, résa actives → CANCELLED, CASCADE prêts passés
- [x] Tests : `apps/catalog/tests/test_item_delete.py` (5 cas)

### FEAT-028 — Désactiver/réactiver un membre (librarian + admin)
- [x] Doc `docs/specs/FEAT-028-toggle-member-active.md`
- [x] Vue `member_toggle_active` + URL : toggle ACTIVE ↔ SUSPENDED, réactive aussi EXPIRED
- [x] Bouton sur fiche membre + check `MemberStatus.ACTIVE` dans `loans.services.check_item_loanable`
- [x] Tests inclus dans `apps/members/tests/test_toggle_and_delete.py`

### FEAT-029 — Suppression d'un membre (admin)
- [x] Doc `docs/specs/FEAT-029-delete-member.md`
- [x] Vue `member_delete` + URL (superadmin) : annule résa, force-retourne prêts actifs, CASCADE manuel, détache dépendants
- [x] Page de confirmation `member_confirm_delete.html`
- [x] Tests inclus dans `apps/members/tests/test_toggle_and_delete.py` (13 cas combinés FEAT-028+029)

### FEAT-030 — Suppression d'un user (admin)
- [x] Doc `docs/specs/FEAT-030-delete-user.md`
- [x] Vue `user_delete` + URL + page `user_confirm_delete.html`
- [x] Garde-fous : self interdit + dernier SUPERADMIN actif interdit
- [x] Tests : `apps/accounts/tests/test_user_delete.py` (6 cas)

### FEAT-031 — Enrichissement métadonnées catalogue multi-sources (async)
- [x] Doc `docs/specs/FEAT-031-enrichissement-metadonnees.md`
- [x] Module `apps/catalog/sources/` : `openlibrary.py`, `google_books.py`, `bnf.py` (SRU), `bne.py` (SRU)
- [x] Service `apps/catalog/enrichment.py:run_enrichment_job(job_id)` (tâche django-q2)
- [x] Modèle `EnrichmentJob` + migration `apps/catalog/migrations/0006_enrichmentjob.py`
- [x] Settings : `MetadataSourcesForm` + section `sources` exposée dans `core:settings_index`
- [x] Vues admin : `core:enrichment_index` / `core:enrichment_start` / `core:enrichment_detail` (HTMX-like meta refresh 3s)
- [x] Lien depuis `templates/core/advanced.html`
- [x] Tests : `apps/catalog/tests/test_enrichment.py` (12 cas)

### Fin de sprint
- [x] `pytest` complet : **241 passed** (179 → 241, +62 nouveaux, 0 régression)
- [x] `manage.py check` : 0 issue
- [x] Smoke GET 200 sur `/fr/admin/enrichment/`, `/fr/admin/settings/sources/`, `/fr/catalog/`, `/fr/members/`, `/fr/accounts/users/`, `/fr/advanced/`
- [x] Déploiement Pi `192.168.0.147` (plusieurs vagues : initial + hotfixes)
- [x] Test Val bout-en-bout des 6 features — validé 2026-05-24

### Hotfixes / découvertes post-déploiement (2026-05-24)

- [x] **FEAT-031 hotfix #1** : django-q2 re-enqueue toutes les 120s → multi-worker concurrent → `processed > total`. Fix : `q_options={timeout:3600, retry:7200, ack_failure:True}` + idempotence (early return si `state != PENDING`).
- [x] **FEAT-031 hotfix #2** : sources interrogées en parallèle (ThreadPoolExecutor, ~×4 plus rapide) + suppression du `time.sleep(0.5)` entre sources.
- [x] **FEAT-031 hotfix #3** : placeholder titre OfeliaScan → language-neutral `ISBN:<isbn> - <dd.mm.aaaa hh.mn>` (`apps/api/services.py`), détecté + écrasé par FEAT-031 même en FILL_MISSING (préfixes `ISBN:` + legacy `Sans titre — session ` pour rétrocompat).
- [x] **FEAT-031 hotfix #4** : extraction étendue dans les 4 sources — summary (OL `description`/`notes`/`excerpts`), subjects (OL `subjects[].name`, GB `categories`, BNF/BNE `dc:subject`), cover_url (GB `imageLinks`, OL `cover.large`). Refactor `merge_record` en fusion **field-by-field** : `_try_sources` renvoie `{source_name: data | None}`, pour chaque champ on prend la 1re source non vide dans l'ordre préféré → summary GB en fallback si OL vide. Tags depuis subjects (cap 10, ≤40 chars, dedup). Cover téléchargée (httpx, max 2 MB) → `record.cover_image`. Rapport enrichi : `field ← source`.
- [x] **FEAT-031 hotfix #5** : style formulaire enrichissement aligné (police 15px, alignement checkbox/radio, espaces réduits) ; champ tag dans `/catalog/` wrappé dans `<div class="search">` pour cohérence.
- [x] **FEAT-031 hotfix #6** : déplacement "Enrichissement métadonnées" de la section Administration vers Inventaire dans `templates/core/advanced.html`.
- [x] **BUG-012** Item.internal_id collision UNIQUE : `count()+1` → `MAX()+1` (`apps/catalog/models.py`). Robuste aux trous dans la séquence. 3 tests `apps/catalog/tests/test_item_codes.py`. Nettoyage de 17 notices orphelines sur la Pi (sessions précédemment échouées).
- [x] **BUG-013** sélecteur de langue cassé en prod : `{{ request.path }}` → `{{ request.path_info }}` (sans préfixe `FORCE_SCRIPT_NAME`) dans `base.html` et `accounts/login.html`. Diagnostic : `translate_url` ne resolve pas `/bibliofelia/fr/...` → URL inchangée → reste FR.
- [x] **Recherche ISBN dans `/catalog/`** : la barre filtrait via FTS5 (qui n'indexe pas les ISBN). Désormais `classify_query` route ISBN → `Q(isbn_13=v) | Q(isbn_10=v)`, EAN13 d'exemplaire → `items__ean13`. Tests : `apps/catalog/tests/test_views.py` (3 cas).
- [x] **Filtre tag dans `/catalog/`** : nouveau champ `q_tag` (substring icontains, dedup) à côté des autres filtres. Combinable avec les autres filtres (AND). 2 tests.
- [x] **i18n complète EN/ES/MG** : 197 chaînes traduites via `scripts/apply_translations.py` (dict Python → batch d'application aux 4 `.po`, suppression des `#, fuzzy`), 48 fuzzy nettoyés au passage. Couvre dashboard, tile_strip, lend/return/reservations, advanced, settings sources, enrichment, suppressions Sprint 9, topbar (Bibliothèque communautaire). Fix bonus : `{# #}` Django ne supporte pas le multi-ligne (le commentaire s'affichait comme texte) → commentaire ramené sur une ligne.
- [x] **Tests complets** : `pytest` toujours vert (241 → 241 stable, ratio post-hotfix). Aucune régression.
- [x] **MEMORY.md mis à jour** (`feedback_small_library_simplicity.md` ajouté avant le sprint).
- [x] **SPEC_BIBLIOFELIA.md** : entête mise à jour, §6.1 + §6.9 + §6.10 + §6.11 enrichies, BUG-012 + BUG-013 documentés.
- [x] Commit unique Sprint 9 + push origin/main

## Sprint 10 — Emplacements (UI + API) + réassignation au récolement

> Ouvert le 2026-05-24. Déclenché par la modification d'OfeliaScan : envoi du `location_code` dans les sessions de catalogage et `scope_location_code` dans les sessions de récolement. Constat : aucune UI librarian pour créer/modifier les `Location`, et aucun endpoint API pour qu'OfeliaScan propose un picker. En complément, on profite du récolement pour corriger automatiquement la `location` des exemplaires scannés (insight Val : la source de vérité physique, c'est le scan terrain).

### FEAT-032 — Gestion des emplacements (UI librarian + API)
- [x] Doc `docs/specs/FEAT-032-locations.md` (rédigée 2026-05-24, statut DONE)
- [x] Vues function-based `apps/catalog/views.py` : `location_list`, `location_create`, `location_edit`, `location_delete` (cohérent avec le pattern existant — pas de CBV)
- [x] Form `apps/catalog/forms.py:LocationForm` (validation `(code, parent)` unique côté form + queryset parent exclut self)
- [x] Routes `apps/catalog/urls.py` : `/catalog/locations/`, `/new/`, `/<pk>/edit/`, `/<pk>/delete/`
- [x] Templates : `templates/catalog/location_list.html`, `location_form.html`, `location_confirm_delete.html` (design olive cohérent section Inventaire)
- [x] Carte « Emplacements » ajoutée dans `templates/core/advanced.html` (section Inventaire, style olive, icône `map-pin`)
- [x] Endpoint API `GET /api/v1/locations` (`apps/api/views.py:LocationListView` + `LocationSerializer` dans `apps/api/serializers.py`)
- [x] Route API `apps/api/urls.py` : `path("locations", ...)` (pas de slash final, cohérent avec les autres endpoints)
- [x] Tests `apps/catalog/tests/test_locations.py` (10 cas : list/create/edit/delete + permissions + parent self + (code,parent) unique)
- [x] Tests `apps/api/tests/test_locations_api.py` (5 cas : auth, vide, tri, parent_code, payload shape)
- [x] `SPEC_BIBLIOFELIA.md` : §6.1 paragraphe « Gestion des emplacements » + §6.10 sous-section « Catalogue des emplacements (lecture seule) » + entête mise à jour
- [x] `pytest` : 241 → 256 verts, aucune régression
- [ ] Test Val OK sur http://localhost:8001/fr/catalog/locations/
- [ ] Déploiement Pi (rebuild Docker : templates embarqués)
- [ ] Commit `FEAT-032: gestion emplacements UI + API`

### FEAT-033 — Réassignation automatique des exemplaires au récolement
- [x] Doc `docs/specs/FEAT-033-relocate-on-inventory.md` (rédigée 2026-05-24, statut DONE)
- [x] Migration `apps/inventory/migrations/0003_inventorysession_relocate_count.py` (PositiveIntegerField default=0)
- [x] Service `apps/inventory/services.py` : `maybe_relocate(item, session)` (renommé public pour import propre depuis api/views.py) + appel dans `record_scan`
- [x] API `apps/api/views.py:InventorySessionItemsView` : appel `maybe_relocate` après chaque `InventoryScan.objects.create` (la vue API n'utilise pas `record_scan` à cause de la logique BUG-008 multi-exemplaires ISBN)
- [x] Template `templates/inventory/session_report.html` : bandeau olive avec compteur si `session.relocate_count > 0` et `scope_type=location`
- [x] Tests `apps/inventory/tests/test_relocate.py` (8 cas : scope location/all/category, item ailleurs/None/déjà bon, EAN inconnu, accumulation, idempotence)
- [x] Tests étendus `apps/api/tests/test_inventory_api.py` (+`TestInventoryRelocate.test_relocate_via_api_batch`)
- [x] Test existant `test_build_report_classifies_divergences` adapté : split en 2 (scope catégorie pour vérifier les misplaced, scope location pour vérifier que FEAT-033 les fait disparaître)
- [x] `SPEC_BIBLIOFELIA.md` : §6.5 paragraphe « Réassignation automatique au récolement » + entête mise à jour
- [x] `pytest` : 256 → 266 verts, aucune régression
- [ ] Test Val OK (scénario UI : créer A1+B2, créer item en B2, lancer récolement scope A1, scanner l'EAN B2, vérifier reloc + bandeau)
- [ ] Déploiement Pi (migration + rebuild Docker)
- [ ] Commit `FEAT-033: réassignation auto location au récolement`

### Clôture Sprint 10
- [ ] Tests complets `pytest` verts (cible : 241 + ~14 nouveaux = ~255)
- [ ] `MEMORY.md` mis à jour si décision structurante
- [ ] Commit unique groupant FEAT-032 + FEAT-033 (ou deux commits si Val préfère) + push origin/main
