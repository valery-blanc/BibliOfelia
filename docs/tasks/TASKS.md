# TASKS — BibliOfelia v1

Source de vérité de l'avancement v1. Une case `[x]` = livrable terminé et déployable. `[ ]` = à faire. `[!]` = bloqué (voir note).

Mise à jour : 2026-05-26 (Sprint 12 **CLOS** — FEAT-038 (cartes membres : fond crème, logo OFELIA filigrane, photo HG, langue BG, bloc droite), FEAT-039 (étiquettes 70×42 mm, titre wrap 2 lignes, auteurs 2 lignes, logo Ofelia), split paramétrage `labels` → `printing_cards` + `printing_labels`. BUG-013 v2 (sélecteur de langue qui perdait `/bibliofelia/` à chaque déploiement : wrapper `apps/core/i18n_views.py:set_language` force `FORCE_SCRIPT_NAME` + échange code langue même sur URL non résolue). **Gate i18n pérenne** : `scripts/i18n_check.py` exit != 0 si chaîne manquante ; documenté dans CLAUDE.md comme obligatoire avant tout commit ; 207 entrées EN/ES/MG appliquées (Sprints 10-12 incl. FORMS labels enrobés `gettext_lazy`). 304 tests verts (287 → 304). Sprint 11 **CLOS** — — BUG-014 (saisie clavier sur `/loans/lend/` + `/loans/return/` : bouton scan repassé `type="button"` + bouton « Valider » visible séparé pour la saisie clavier), FEAT-034 (UI réservations : liste d'attente PENDING sur fiche notice, expiration affichée sur exemplaires mis de côté, section « Réservations à relancer » sur page Retour, paramètres `default_loan_days`/`reservation_expiry_days`/`pickup_hold_days` exposés dans `/settings/loans/`), FEAT-035 (Setting `default_loan_days` global défaut 21, section « Relances à faire » bas du dashboard avec 10 prêts en retard), FEAT-036 (`Reservation.notified_at` + endpoint `POST /loans/reservations/<pk>/notify/`, page Réservations enrichie code Ofelia / dates avec heure / date limite retrait / police 16-17 px + cadre « Notifications à faire » entre tuiles et bannière scan sur dashboard), BUG-015 (DateInput format ISO `%Y-%m-%d` sur `MemberForm`, sinon locale FR remplit pas l'input HTML5), FEAT-037 (photo membre dans pagehead fiche + miniature sur form, expiration_date = registration_date + 1 an auto JS au change + initial `today + 1 an` à la création). 287 tests verts (266 → 287, +21). Migration `loans/0002_reservation_notified_at`. 5 vagues de déploiement Pi. 2 nouvelles entrées MEMORY (DateInput ISO format, bouton scan type=button + Valider visible). — Sprint 10 **CLOS end-to-end** — FEAT-032 + FEAT-033 validés Val 2026-05-24 sur la Pi, **+ OfeliaScan mobile mis à jour le 2026-05-24** : test prod 18:26 → session récolement scope=A1 reçue d'OfeliaScan avec 16 scans, 16 exemplaires relocate de J1 → A1 automatiquement. Bout-en-bout fonctionnel : catalogage OfeliaScan envoie `location_code`, picker récolement OfeliaScan envoie `scope_type=location` + `scope_location_code`, BibliOfelia déplace les items au scan. FEAT-032 : UI librarian /catalog/locations/ + endpoint GET /api/v1/locations testés OK. FEAT-033 : relocate auto vérifiée via UI web ET via OfeliaScan mobile. Commit `9d4fe83` + push + déploiement Pi (rebuild Docker + migration `0003`). 266 tests verts. — Sprint 8 **CLOS** — FEAT-025 **validé Val 2026-05-23** : refonte design global, 23 templates métiers harmonisés sur le design system OFELIA. Lot A pilote validé en premier (record_detail, member_detail, reports/index, settings_index), puis Lots B+C+D livrés d'un bloc. Helpers CSS ajoutés (`.req`, `.help-hint`, `.field-error`, `.form-control`, `details.advanced-section`, `.isbn-row`, `.form-actions`), `_field.html` migré `.form-row` → `.field`. Découverte d'infra : templates **embarqués au build Docker**, pas bind-mountés → rebuild obligatoire pour tout changement de template (documenté dans FEAT-025). — Sprint 7 **CLOS** — FEAT-024 **validé Val 2026-05-23** : scanner caméra navigateur sur Android Firefox HTTPS OK, fallback OfeliaScan automatique en HTTP LAN, Chrome Android sans Play Store via `S.browser_fallback_url`, bouton Annuler pendant polling. Décision UX : caméra-d'abord automatique, pas de toggle utilisateur. Décision infra : pas de cert auto-signé. 3 commits Pi `d7c8e8f` → `9d2af81` → `e9993a5`. FEAT-023 **validé Val 2026-05-23** : banner dashboard → OfeliaScan ouvre → scan livre → retour BibliOfelia → fiche notice affichée, bout-en-bout fonctionnel. Modèle `ScanHandoff` + endpoints `/api/v1/scan-handoff[/{token}]` + JS `scan-handoff.js` + 4 boutons « Scanner » câblés. BUG-010 entrypoint Dockerfile + BUG-011 CSRF cookie HttpOnly + Chrome Android `intent://` URL résolus. Sprints 3/5/6 clos. Reste pour Sprint 7 : Android-side OfeliaScan déjà fonctionnelle côté Val (intent filter + activity scan-one + POST callback) — implémentation Android terminée hors repo. Prochain sprint : FEAT-024 scanner caméra navigateur (HTTPS).)

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
- [x] Test Val OK 2026-05-24 (CRUD complet validé sur dev local)
- [x] Déploiement Pi 2026-05-24 (rebuild Docker `edubox-bibliofelia` + `-worker`, smoke test `/api/v1/locations` → 401 sans token, OK)
- [x] Commit `9d4fe83` (Sprint 10 groupé FEAT-032 + FEAT-033) + push origin/main

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
- [x] Test Val OK 2026-05-24 (UI web + relocate vérifiée)
- [x] Déploiement Pi 2026-05-24 (migration `0003` appliquée, containers healthy)
- [x] Commit `9d4fe83` (groupé avec FEAT-032) + push origin/main
- [x] **OfeliaScan mobile mis à jour 2026-05-24** : test bout-en-bout validé Val — session 18:26 `scope=location, loc=A1, relocate=16, scans=16`. 16 exemplaires catalogués en J1 puis récolés en A1 via OfeliaScan → tous déplacés automatiquement vers A1. FEAT-033 fonctionnel en production end-to-end via mobile.

### Clôture Sprint 10
- [x] Tests complets `pytest` verts : 266 (241 → 256 FEAT-032 → 266 FEAT-033)
- [x] `MEMORY.md` à jour (pas de décision structurante nouvelle, juste réutilisation des patterns existants)
- [x] Commit unique Sprint 10 (`9d4fe83`) + push origin/main + déploiement Pi
- [x] Sprint 10 **CLOS** end-to-end 2026-05-24 — BibliOfelia + OfeliaScan mobile. Test prod : 16 exemplaires J1 → A1 via récolement OfeliaScan, relocate automatique confirmée.

## Sprint 11 — Saisie clavier sur lend/return + réservations UI + relances dashboard + formulaire membre — **CLOS**

> Ouvert le 2026-05-25 (temp.txt). 1 bug + 2 features initiales, étendu en 5 itérations à 3 bugs (BUG-014, BUG-015) + 4 features (FEAT-034, FEAT-035, FEAT-036, FEAT-037). **Validé Val 2026-05-25 + commit + push origin/main.** 287 tests verts.

### BUG-014 — Saisie clavier interceptée par le scan-handoff
- [x] Doc `docs/bugs/BUG-014-lend-enter-key-scan-intercept.md`
- [x] Fix `templates/loans/lend.html` : 2 boutons scan en `type="button"` + ajout `<button type="submit" hidden>` dans chaque form
- [x] Fix `templates/loans/return.html` : idem pour bouton « Enregistrer le retour »
- [x] Tests de non-régression POST manuel (`apps/loans/tests/test_views.py` — 2 tests UI)
- [x] SPEC §6.3 mise à jour
- [x] Test Val OK 2026-05-25

### FEAT-034 — Compléments réservations (UI + paramètres)
- [x] Doc `docs/specs/FEAT-034-reservation-uplift.md`
- [x] `apps/catalog/views.py:record_detail` annote items réservés avec leur réservation `READY_FOR_PICKUP`
- [x] `templates/catalog/record_detail.html` : afficher membre + date d'expiration de la mise de côté
- [x] `apps/loans/services.py:reservations_due_soon(within_days=2)` + `pickup_expiration_for`
- [x] `apps/loans/views.py:return_items` injecte `reservations_due`
- [x] `templates/loans/return.html` : section « Réservations à relancer »
- [x] `apps/core/forms.py:LoanReservationDefaultsForm` (partagé avec FEAT-035)
- [x] `apps/core/admin_views.py` + `templates/core/admin/settings_index.html` : nouvelle section « loans »
- [x] Tests `apps/loans/tests/test_sprint11.py` + `apps/catalog/tests/test_views.py`
- [x] SPEC §6.4 mise à jour
- [x] Test Val OK 2026-05-25

### FEAT-035 — Durée prêt paramétrable + relances dashboard
- [x] Doc `docs/specs/FEAT-035-loan-defaults-and-overdue-reminders.md`
- [x] `seed_defaults` : nouvelle clé `default_loan_days` (21)
- [x] `apps/loans/services.py:compute_due_date` lit `Setting.default_loan_days` en fallback
- [x] Champ `default_loan_days` ajouté au `LoanReservationDefaultsForm` (FEAT-034)
- [x] `apps/core/views.py:dashboard` injecte `reminders` (10 derniers, annotés `days_overdue_count`)
- [x] `templates/core/dashboard.html` : section « Relances à faire »
- [x] Tests `apps/loans/tests/test_sprint11.py` + `apps/core/tests/test_ui.py`
- [x] SPEC §6.3 + §6.6 mises à jour
- [x] Test Val OK 2026-05-25

### Itération 2 — feedbacks Val 2026-05-25
- [x] BUG-014 v2 : remplacement du `<button type="submit" hidden>` par un bouton visible **« Valider »** à côté de chaque input (lend.html × 2 forms, return.html × 1) + classe CSS `.search-with-submit`
- [x] FEAT-034 v2 : ajout de la liste d'attente PENDING sur `record_detail.html` (avec position FIFO + bouton annuler)

### FEAT-036 — Flag notifié + cadre dashboard
- [x] Doc `docs/specs/FEAT-036-reservation-notified-flag.md`
- [x] Migration `apps/loans/migrations/0002_reservation_notified_at.py` (DateTimeField nullable)
- [x] Service `apps/loans/services.py:mark_reservation_notified` (idempotent)
- [x] Vue `apps/loans/views.py:reservation_notify` + URL `loans:reservation_notify`
- [x] `apps/loans/views.py:reservation_list` enrichie : `ready_at_dt`, `pickup_deadline`, position FIFO `queue_position`
- [x] `templates/loans/reservations.html` refonte section ready (typo 16-17 px, code Ofelia, dates avec heure, bouton Notifier / badge Notifié)
- [x] `apps/core/views.py:dashboard` injecte `notifications_pending`
- [x] `templates/core/dashboard.html` : cadre « Notifications à faire » entre tuiles et bannière scan
- [x] `static/css/ofelia.css` : classes `.alert-box`/`.alert-row`
- [x] Tests `apps/loans/tests/test_sprint11.py` (+4 cas FEAT-036)
- [x] SPEC §6.4 + §6.6 mises à jour
- [x] Test Val OK 2026-05-25

### Itération 3 — feedbacks Val 2026-05-25 (formulaire membre)
- [x] BUG-015 `docs/bugs/BUG-015-member-edit-dates-cleared.md` (dates DateInput format ISO)
- [x] `apps/members/forms.py` : `format="%Y-%m-%d"` sur birth_date/registration_date/expiration_date
- [x] FEAT-037 `docs/specs/FEAT-037-member-form-ergonomics.md` (photo + recalc expiration)
- [x] `templates/members/member_detail.html` : photo dans pagehead si présente
- [x] `templates/members/member_form.html` : miniature photo + JS recalc expiration +1 an
- [x] Tests `apps/members/tests/test_views.py` (BUG-015 + non-régression dates)
- [x] SPEC §6.2 mise à jour (BUG-015 + FEAT-037)
- [x] Test Val OK 2026-05-25

### Clôture Sprint 11
- [x] `pytest` complet vert (266 → 287, +21 nouveaux)
- [x] Déploiement Pi (5 vagues : initial + 4 itérations, rebuild Docker + migration `0002` loans)
- [x] Test Val OK 2026-05-25 (BUG-014 + FEAT-034 + FEAT-035 + FEAT-036 + BUG-015 + FEAT-037 bout-en-bout)
- [x] MEMORY.md mis à jour (2 nouvelles entrées feedback : DateInput ISO format, bouton scan dans un form)
- [x] SPEC §6.2 + §6.3 + §6.4 + §6.6 mises à jour
- [x] Commit unique Sprint 11 + push origin/main

## Sprint 12 — Impressions : refonte cartes membres + étiquettes livres

> Ouvert le 2026-05-25 (temp.txt). 2 features : refonte visuelle des cartes
> membres (photo + logo Ofelia + fond crème) et refonte des étiquettes livres
> (titre 2 lignes + logo + agrandissement). Splitter le formulaire de
> paramétrage `/admin/settings/labels/` en 2 sections distinctes regroupées
> dans la catégorie « Impressions ».

### FEAT-038 — Refonte impression cartes membres
> Sous-cases cochées rétroactivement 2026-05-30 (sprint clos + validé Val 2026-05-26, voir Clôture Sprint 12).
- [x] Doc `docs/specs/FEAT-038-print-member-cards.md`
- [x] Copier `Logo_ofelia_grandes_lettres.png` → `static/img/ofelia-grandes-lettres.png`
- [x] `apps/core/forms.py` : nouveau `MemberCardFormatForm` (KEY=`card_format`)
- [x] `apps/printing/services.py` : refonte `_draw_member_card` (photo HG, langue BG, fond crème, logo centré, bloc info droite)
- [x] Tests `apps/printing/tests/test_services.py` : cartes membre
- [x] SPEC §6.7 mise à jour

### FEAT-039 — Étiquettes livres : refonte + paramétrage séparé
- [x] Doc `docs/specs/FEAT-039-print-item-labels.md`
- [x] `apps/core/forms.py` : nouveau `ItemLabelFormatForm` (KEY=`item_label_format`)
- [x] `apps/printing/services.py` : refonte `_draw_item_label` (titre wrap 2 lignes, logo ofelia, 80×40 mm)
- [x] `apps/core/admin_views.py` : `FORMS` mis à jour (sections `printing_cards` + `printing_labels`)
- [x] `templates/core/admin/settings_index.html` : regroupement « Impressions »
- [x] `apps/core/management/commands/seed_defaults.py` : `card_format` + `item_label_format`
- [x] Tests `apps/printing/tests/test_services.py` : étiquettes livres
- [x] SPEC §6.7 mise à jour

### BUG-013 v2 — Sélecteur de langue qui perd `/bibliofelia/` (pérenne)
- [x] Doc `docs/bugs/BUG-013-set-language-script-name.md` (régression v2 + fix pérenne)
- [x] `apps/core/i18n_views.py` : wrapper `set_language` qui force `FORCE_SCRIPT_NAME` + échange code langue même si URL non résolue
- [x] `config/urls.py` : route `path("i18n/setlang/", core_set_language, name="set_language")` qui remplace `django.conf.urls.i18n`
- [x] Tests `apps/core/tests/test_i18n_setlang.py` (4 cas)
- [x] Déploiement Pi 2026-05-26 + smoke test multi-langues

### i18n — gate bloquant pérenne (Sprint 12)
- [x] `scripts/i18n_check.py` — audit pass/fail (stdlib, exit 1 si chaînes manquantes ou fuzzy)
- [x] `scripts/translations_sprint12.py` — batch des 63 chaînes manquantes (FEAT-032/035/036/037/038/039)
- [x] Application : 189 entrées remplacées (63 × 3 langues), 0 chaîne manquante post-fix
- [x] `CLAUDE.md` : section « Traductions i18n (OBLIGATOIRE — gate avant commit) » + étape « passer le gate i18n » ajoutée aux Bug Fix / Feature Workflows
- [x] `MEMORY.md` : entrée [[feedback-i18n-gate]]
- [x] Déploiement Pi 2026-05-26 (po + compilemessages OK)

### Clôture Sprint 12
- [x] `pytest` complet vert (287 → 304, +17 : 13 printing + 4 i18n setlang)
- [x] Build Docker + déploiement Pi (3 vagues : FEAT-038/039, iter2 70×42, BUG-013 v2 + i18n)
- [x] Gate i18n : `python scripts/i18n_check.py` → OK (0 chaîne manquante, 207 entrées appliquées via translations_sprint12.py incl. FORMS labels gettext_lazy)
- [x] Test Val OK 2026-05-26 (impressions cartes + étiquettes 70×42/auteurs 2 lignes + sélecteur de langue persistant + /admin/settings traduit)
- [x] Commit unique Sprint 12 + push origin/main

## Sprint 13 — Exports CSV rapports + actions de masse catalogue + traductions catégories

> Ouvert 2026-05-27 (temp.txt). 3 features (FEAT-040 / 041 / 042). Aucun bugfix.

### FEAT-040 — Exports CSV rapports + dernière activité
- [x] Doc `docs/specs/FEAT-040-csv-exports-and-last-activity.md`
- [x] `apps/reports/services.py` : `catalog_full_csv_rows`, `active_loans_for_export`, `active_reservations_for_export`, annotation `last_activity=Max(loans__loan_date)` sur inactifs
- [x] `apps/reports/views.py` : 4 nouvelles vues CSV (`catalog_csv`, `active_loans_reservations_csv`, `inactive_members_csv`, `inactive_items_csv`)
- [x] `apps/reports/urls.py` : 4 routes
- [x] `templates/reports/index.html` : 2 cards exports catalogue + prêts/résa
- [x] `templates/reports/inactive_list.html` : 2 boutons CSV + colonne « Dernière activité »
- [x] Tests `apps/reports/tests/test_csv_exports.py` (7 cas)
- [x] SPEC §6.6 mise à jour

### FEAT-041 — Bulk affect category + location (catalogue)
- [x] Doc `docs/specs/FEAT-041-bulk-affect-category-location.md`
- [x] `apps/catalog/views.py` : 4 vues (`record_bulk_assign_category[_confirm]`, `record_bulk_assign_location[_confirm]`)
- [x] `apps/catalog/urls.py` : 4 routes
- [x] Templates : `record_bulk_assign_category.html`, `record_bulk_assign_location.html`
- [x] `templates/catalog/record_list.html` : tableau de sélection ouvert aux librarians + 2 boutons via `formaction`
- [x] Tests `apps/catalog/tests/test_bulk_assign.py` (7 cas)
- [x] SPEC §6.1 mise à jour

### FEAT-042 — Traductions FR→EN/ES/MG catégories seed
- [x] Doc `docs/specs/FEAT-042-default-category-translations.md`
- [x] `apps/core/management/commands/seed_defaults.py` : tuples 4 langues + backfill idempotent
- [x] Tests `apps/catalog/tests/test_seed_translations.py` (3) + `apps/members/tests/test_seed_translations.py` (2)
- [x] SPEC §5.2 mise à jour

### BUG-016 — Mobile : sélection multiple catalogue absente (cleanup Sprint 13)
- [x] Doc `docs/bugs/BUG-016-mobile-bulk-select-catalogue.md`
- [x] `templates/catalog/record_list.html` : un seul form englobe desktop + mobile, ajout checkboxes sur cards mobiles + ligne « Tout cocher »
- [x] Note : aucune sélection multiple côté `members` à ce jour (pas de feature) → hors scope

### BUG-017 — Mobile : table sans scroll horizontal (cleanup Sprint 13)
- [x] Doc `docs/bugs/BUG-017-mobile-table-no-horizontal-scroll.md`
- [x] `static/css/ofelia.css` : `.table-wrap` `overflow: hidden` → `overflow-x: auto / overflow-y: hidden` + `min-width: 560px` sur la table en ≤ 599 px

### Clôture Sprint 13
- [x] `pytest` complet vert : 304 → 323 (+19, 0 régression)
- [x] Gate i18n `scripts/i18n_check.py` → 0 chaîne manquante (translations_sprint13.py = 25 entrées × 3 langues + 14 fuzzy nettoyés par langue)
- [x] Test Val OK 2026-05-27 (FEAT-040 + 041 + 042 bout-en-bout sur la Pi)
- [x] BUG-016 + BUG-017 + itération espacement boutons + fix compteur double (ids_desktop/ids_mobile) — test Val OK 2026-05-27 mobile
- [x] Commit unique Sprint 13 (3 FEAT + 2 BUG) + push origin/main

---

## Sprint 14 — UX bulk-delete + non-réutilisation des codes Ofelia

### FEAT-043 — Tombstones des codes Ofelia (anti-réattribution)
- [x] Modèle `RetiredItemCode` (`internal_id` PK, `ean13`, `record_title_snapshot`, `retired_at`, `retired_by`, `reason`) — `apps/catalog/models.py`
- [x] Migration `catalog/0007_retired_item_codes.py`
- [x] Signal `pre_delete` sur `Item` → `RetiredItemCode.get_or_create` — `apps/catalog/signals.py` + `apps.py:ready()`
- [x] `Item._assign_codes()` : `MAX` calculé en union `Item ∪ RetiredItemCode`
- [x] Vue `record_bulk_delete` : pré-création des tombstones avec `reason=bulk_delete` + `retired_by=request.user`
- [x] Tests `apps/catalog/tests/test_retired_codes.py` (5 tests, tous verts)
- [x] Doc FEAT-043 + SPEC §5.2 (paragraphe « Non-réutilisation des codes Ofelia »)

### UX bulk-delete
- [x] `record_list.html` : bouton « Supprimer la sélection » → « Supprimer les notices sélectionnées »
- [x] `record_bulk_delete.html` : warning enrichi (« Les notices et tous leurs exemplaires seront supprimés. Les prêts en cours seront marqués « Perdu » et les réservations actives seront annulées. Ces suppressions sont définitives. »)

### Fix 405 sur sélecteur de langue + pages d'erreur Ofelia (400/403/404/405/500)
- [x] `base.html` : block `lang_next` overridable (default `request.path_info`)
- [x] Override `lang_next = /<lang>/catalog/` dans `record_bulk_delete.html`, `record_bulk_assign_category.html`, `record_bulk_assign_location.html`
- [x] `apps/core/middleware.py:MethodNotAllowedPrettyMiddleware` — substitue toute 405 par notre template (Django n'a pas de `handler405`)
- [x] `templates/errors/_error_page.html` — layout partagé (étend `base.html`, blocks `error_title`/`error_subtitle`/`error_icon`/`error_body`)
- [x] `templates/400.html` (Requête invalide), `403.html` (Accès interdit), `404.html` (Page introuvable), `405.html` (Méthode non autorisée) — étendent `_error_page.html`
- [x] `templates/500.html` — **standalone** (handler500 n'exécute pas les context processors → pas d'extends base.html, textes FR/EN/ES/MG en dur)

### Clôture Sprint 14
- [x] `pytest` complet vert (catalog + core + loans + members + inventory)
- [x] Gate i18n `scripts/i18n_check.py` → 0
- [x] Déploiement Pi (192.168.0.147) + rebuild Docker
- [x] Test Val OK 2026-05-28 (UI bulk-delete + non-réutilisation code Ofelia + pages d'erreur 404/403/405)
- [x] Commit unique Sprint 14 + push origin/main (afddac9)

## Sprint 15 — Guide utilisateur bibliothécaires (site MkDocs, FR + EN + ES + MG)

> Lancé 2026-05-29. Objectif : produire un site statique de documentation utilisateur pour bibliothécaires, avec captures d'écran annotées, en 4 langues, déployable sur la Box à `/bibliofelia/docs/`.

### Task #1 — Scaffolding + 3 captures échantillon (POC)
- [x] `requirements-doc.txt` : mkdocs 1.6 + mkdocs-material 9.5 + mkdocs-static-i18n 1.2 + playwright 1.49 + Pillow 11
- [x] `.venv-doc/` créé + dépendances installées + Chromium Playwright téléchargé
- [x] `docs/user-guide/mkdocs.yml` : config Material, palette deep purple/amber, navigation tabs+sections, search FR/EN, fonts désactivées (contrainte hors-ligne)
- [x] `docs/user-guide/docs/index.md` + `premiers-pas/{connexion,dashboard}.md` + `prets-retours/faire-pret.md` (pages POC)
- [x] `apps/setup/management/commands/seed_demo.py` : wrapper sur `install_demo()` + création compte `demo_librarian` (rôle LIBRARIAN, password `OfeliaDemo2026!`) idempotent et tolérant
- [x] `docs/user-guide/scripts/capture_screenshots.py` : Playwright headless, viewport 1440×900, locale fr-FR, capture login + dashboard (full page) + form prêt (full page)
- [x] 3 captures générées : `docs/user-guide/docs/assets/screenshots/fr/{login,dashboard,lend-form}.png`
- [x] `mkdocs build` OK (1.86 s)
- [x] `.gitignore` mis à jour (`.venv-doc/`, `docs/user-guide/site/`, `docs/user-guide/preview/`)
- [ ] Test Val : valider le rendu des 3 captures + le scaffolding avant Task #2

### Task #2 — Jeu de données démo stable
- [x] `install_demo()` rendu idempotent : garde sur `BibliographicRecord.summary=DEMO_MARKER` ; re-run = no-op + retour des compteurs actuels (`skipped=True`)
- [x] Fix bug `create_loan(item=, member=)` sans librarian → ajout `librarian=user` (passé par seed_demo) ; **15 prêts effectivement créés** (avant : 0 silencieux à cause de TypeError caché par try/except)
- [x] Nouvelle fonction `install_doc_extras(librarian)` : 2 réservations PENDING + 3 prêts forcés en retard + 1 carte de membre expirée (idempotent via garde sur Reservation existante)
- [x] `remove_demo()` : prise en compte des réservations (delete avant loans)
- [x] Commande `seed_demo` enrichie : `--reset` (purge + reinstall), `--librarian-username/password`, ordre user → reset → install_demo → install_doc_extras, sortie verbeuse
- [x] Test idempotence manuel : 2 runs successifs OK (1er = installation, 2e = skip)
- [x] 163 tests verts (`pytest apps/catalog apps/loans apps/members`)
- [x] Dashboard re-capturé avec état riche : 16 prêts en cours, 3 retards (section « Relances à faire » visible), Top 10 rempli

### Task #3 — Script de capture exhaustif FR (24 écrans + annotations)
- [x] `capture_screenshots.py` refondu : liste `PAGES` structurée (group, name, url, full_page), boucle générique, helpers `open_first_record` / `open_first_member` pour les fiches dynamiques, options `--lang/--only/--headed`
- [x] 24 captures FR générées dans `docs/user-guide/docs/assets/screenshots/fr/{group}/{name}.png` (login, dashboard, help, advanced, record-list/create/detail, item-create, location-list/create, member-list/create/detail/history, lend, return, consultation, reservation-list, cards-picker, labels-picker, reports-index, overdue-list, reservations-pickup, inactive)
- [x] `annotate.py` : helper Pillow pour encadrés rouges + pastilles numérotées (font Segoe UI Bold ou Arial Bold via Windows Fonts)
- [x] Smoke test annotations validé (4 boxes sur tuiles dashboard) puis nettoyé
- [ ] Coordonnées d'annotation à capturer via `page.locator().bounding_box()` au moment de la rédaction (Task 4) — pas de hardcoding

### Task #3b — Thème OFELIA pour MkDocs (cohérence avec l'app)
- [x] Tokens OFELIA récupérés depuis `static/css/ofelia.css` (burgundy `#6B2138`, cream `#F7F5F0`, ink `#3D3530`, orange `#ED7538`, forest, blush, sky)
- [x] Polices Bricolage Grotesque (3 subsets) + DM Sans (2 subsets) copiées dans `docs/user-guide/docs/stylesheets/fonts/` (contrainte hors-ligne respectée)
- [x] Logos `ofelia-logo.png` + `ofelia-grandes-lettres.png` copiés dans `docs/user-guide/docs/assets/img/`
- [x] `docs/user-guide/docs/stylesheets/extra.css` : surcharge palette Material (default + slate), titres en Bricolage, corps en DM Sans, headings burgundy, admonitions OFELIA (forest=tip, orange=warning, sky=info, burgundy=danger), tables/codeblocks ton crème
- [x] `mkdocs.yml` : `logo: assets/img/ofelia-logo.png`, `favicon`, `palette: primary/accent: custom`, `extra_css: stylesheets/extra.css`
- [x] Rebuild OK, preview captures site-home + site-faire-pret validées par Val
- [x] MEMORY : `feedback_doc_reuse_design.md` créée (règle pérenne : pour tout livrable visuel, réutiliser la charte OFELIA existante)

### Task #4 — Rédaction guide FR (22 pages)
- [x] Page pilote `prets-retours/faire-pret.md` rédigée + capture annotée pixel-perfect (4 zones numérotées via `capture_annotated.py` + `boxes_from_selectors`) → validation Val OK sur ton, niveau de détail, format
- [x] **Premiers pas** (4) : `connexion`, `dashboard`, `langue`, `saisie`
- [x] **Catalogue** (5) : `ajouter-livre`, `exemplaires`, `localisations`, `recherche`, `operations-lot`
- [x] **Usagers** (4) : `inscription`, `fiche`, `carte`, `renouvellement`
- [x] **Prêts et retours** (3 + pilote) : `retour`, `prolongation`, `consultation`
- [x] **Réservations** (3) : `creer`, `notifications`, `retrait`
- [x] **OfeliaScan** (3) : `activer`, `pret-retour`, `recolement`
- [x] **Impressions** (2) : `cartes`, `etiquettes`
- [x] **Rapports** (2) : `kpis`, `exports`
- [x] **Cas courants** (3) : `livre-perdu`, `carte-perdue`, `retard`
- [x] **Annexes** (2) : `faq`, `glossaire`
- [x] `mkdocs.yml` nav complète (10 sections + 22 pages)
- [x] Build mkdocs sans warning, liens internes tous résolus
- [x] Preview de 8 pages clés validées (home, faire-pret, ajouter-livre, inscription, reservation-creer, recolement, livre-perdu, glossaire)
- [x] Validation Val sur ton et fond : OK, avec corrections demandées (codes + langage trop technique + FAQ facturation + toggle dark + brancher bouton aide)

### Task #4b — Corrections demandées par Val
- [x] **Glossaire refondu** : section dédiée « Les différents codes » distinguant ISBN-13, ISBN-10, code Ofelia (290/291), code interne (OFL-YYYYMMDD-NNNN), n° de membre — chacun expliqué avec exemples et usage (prêt, catalogage, scan)
- [x] **Termes techniques retirés** : `FTS5` (recherche.md → "recherche tolérante"), `Tombstone` (livre-perdu.md, carte-perdue.md, glossaire.md → formulations en langage simple), `UTF-8` (exports.md → "caractères accentués s'affichent correctement")
- [x] **FAQ** : suppression de la question facturation
- [x] **Nomenclature corrigée partout** : "code interne" → "code Ofelia" quand il s'agit du code-barres scannable (recherche.md, exemplaires.md, faire-pret.md, inscription.md)
- [x] **Toggle mode sombre supprimé** : `mkdocs.yml` palette simplifiée à `scheme: default` (style imposé)
- [x] **Bouton « ? » topbar BibliOfelia** branché vers `docs_url` :
  - `apps/core/context_processors.py` : ajout `docs_url = FORCE_SCRIPT_NAME.rstrip('/') + '/docs/'`
  - `templates/base.html` : `href` change vers `{{ docs_url }}` + `target="_blank"`, libellé « Guide utilisateur »
  - `apps/core/views.py:help_page` : 302 vers `docs_url` (ancien `/help/` reste fonctionnel comme redirect)
- [x] Tests `apps/core` verts (32 passed)

### Task #5 — Capture EN/ES/MG + traduction des 22 pages
- [x] Plugin `mkdocs-static-i18n` activé en mode `suffix` dans mkdocs.yml + `nav_translations` (12 sections × 3 langues)
- [x] Captures EN/ES/MG via `capture_screenshots.py --lang en/es/mg` (72 captures supplémentaires)
- [x] Désactivation de `navigation.instant` (incompatible avec le switcher de langue contextuel)
- [x] Création de `overrides/partials/languages/mg.html` (Material n'a pas de partial Malagasy par défaut) avec `custom_dir: overrides`
- [x] Traduction des 22 markdowns en EN (`.en.md`)
- [x] Traduction des 22 markdowns en ES (`.es.md`)
- [x] Traduction des 22 markdowns en MG (`.mg.md`) — **bandeau d'avertissement sur `index.mg.md` indiquant qu'une relecture par locuteur natif reste à faire**
- [x] Build 4 langues OK (FR=racine, EN=/en/, ES=/es/, MG=/mg/) — 6.58 s
- [x] Preview validée (4 home + faire-pret EN + glossaire ES + glossaire MG)

### Task #6 — Déploiement nginx Box `/bibliofelia/docs/`
- [x] `mkdocs.yml` : `site_url: http://ofelia.local/bibliofelia/docs/` pour résoudre correctement les URLs absolues
- [x] Build production statique (4 langues, ~23 Mo total)
- [x] Tar + scp + extract sur Pi vers `/var/lib/bibliofelia-docs/` (chown ofelia:ofelia)
- [x] **keebee/nginx/conf.d/ofelia-locations.inc** : nouveau `location /bibliofelia/docs/` AVANT `/bibliofelia/` (alias + try_files index.html, expires 1d) — push sur Pi `/opt/edubox/nginx/conf.d/`
- [x] **keebee/docker-compose.yml** : ajout volume `/var/lib/bibliofelia-docs:/var/lib/bibliofelia-docs:ro` sur container `nginx-proxy` — push sur Pi `/opt/edubox/docker-compose.yml`
- [x] `docker compose up -d nginx-proxy` pour recréer avec nouveau volume monté
- [x] Tests HTTP : FR/EN/ES/MG/CSS/Logo tous 200 sur `http://192.168.0.147/bibliofelia/docs/...`
- [x] **Rebuild image BibliOfelia** : push code (Tasks 4b + 5) via tar/scp/extract dans `/opt/edubox/bibliofelia/` (git stash des dirty changes avant), `docker compose up -d --build bibliofelia` — image recréée, bouton `?` et `help_page → /docs/` actifs
- [x] Smoke test Playwright sur Pi : 6 captures (4 home + faire-pret FR + glossaire EN) — rendu nominal OK
- [x] `scripts/deploy_pi.sh` : script de redéploiement futur (build strict + tar + scp + extract + nginx reload)
- [ ] **Validation finale Val** : ouvrir `http://192.168.0.147/bibliofelia/docs/` dans le navigateur, vérifier le bouton ? de la topbar BibliOfelia, naviguer dans les 4 langues

## Sprint 16 — Scanner caméra navigateur en mode unique (FEAT-044)

Objectif (demande Val 2026-05-30) : les 4 boutons « Scanner » du site (dashboard, prêt-carte, prêt-livre, retour) utilisent **uniquement la caméra du navigateur** ; suppression de l'appel OfeliaScan dans ce flux. OfeliaScan reste pour le catalogage et le récolement en masse.

- [x] **FEAT-044** Caméra unique sur les boutons « Scanner » du site
  - [x] Réécrire `static/js/scan-handoff.js` : retrait complet du handoff OfeliaScan (createHandoff/pollHandoff/startHandoff/deep-link/intent/WeakMap/config). Caméra = unique chemin. Sur échec → message d'erreur explicite (raison exacte) + invitation à saisir à la main, pas de redirection silencieuse.
  - [x] `static/js/scan-camera.js` inchangé (callback `onUnavailable` → erreur au lieu de fallback)
  - [x] `templates/base.html` : suppression du bloc `#scan-handoff-config` (createUrl orphelin) + ajout des 9 chaînes d'erreur dans `#scan-mode-i18n`
  - [x] Routage notice/membre déjà assuré par `global_search` (`apps/core/views.py:94`) + `data-scan-dispatch-url` : aucune modif serveur
  - [x] Templates métier inchangés (les 4 boutons `.js-scan-handoff` gardent leurs attributs)
  - [x] Docs : `docs/specs/FEAT-044-scanner-camera-unique.md`, SPEC §6.10, ce TASKS.md
  - [x] Gate i18n : `makemessages` + `scripts/translations_sprint16.py` + `i18n_check.py` → 0
  - [x] Déploiement Pi (rebuild Docker — templates/JS embarqués au build) — 2026-05-30
  - [x] **Mise au point décodage** (test bout-en-bout Val) :
    - [x] Fix 404 lib : URL `html5-qrcode`/`quagga` injectée via `{% static %}` (`#scan-camera-config`) → résout préfixe `/bibliofelia/` + hash ManifestStaticFilesStorage
    - [x] Fix iOS `NotAllowedError` : `primeCameraPermission()` (getUserMedia dans le geste avant lazy-load)
    - [x] Garde anti « ghost-click » mobile (`DISMISS_GUARD_MS=600`)
    - [x] **Double moteur** : html5-qrcode + BarcodeDetector natif (Chrome) / **QuaggaJS** vendoré (`static/js/quagga.min.js`, iOS/Firefox)
    - [x] Fiabilité : EAN-13 uniquement + clé de contrôle + préfixe `290/291/978/979` + consensus 2 lectures + haute résolution 1920×1080
  - [x] **Boutons scan inline** (`.scan-inline-btn`, cercle plein) ajoutés : recherche catalogue, recherche membres, champ ISBN du formulaire notice
  - [x] **Layout dashboard** : bannière scan + recherche remontées au-dessus des tuiles (sous la topbar)
  - [x] Nettoyage du code de debug (panneau de log à l'écran, traces `slog`/`build`)
  - [x] **Validé Val 2026-05-30** : Chrome Android excellent ; Firefox/Safari fonctionnels via Quagga
  - [ ] (Suivi séparé) HTTPS local sur la box pour faire marcher la caméra aussi en LAN HTTP — chantier nginx/cert côté keebee, hors de ce sprint.

## Sprint 17 — Récolement & catalogage en scan caméra continu (remplacement OfeliaScan)

> Ouvert 2026-05-30 (temp.txt). Décisions Val : (1) coder maintenant, HTTPS LAN
> box traité à part — tests sur accès HTTPS ; (2) **récolement d'abord**
> (FEAT-045) puis catalogage (FEAT-046) ; (3) catalogage web réutilise
> `ScanSession`/`ScanItem` + `finalize_scan_session()` (OfeliaScan).

### FEAT-045 — Récolement en scan caméra continu
- [x] Doc `docs/specs/FEAT-045-recolement-camera-continu.md`
- [x] `static/js/scan-camera.js` : mode continu (`opts.continuous` + `onCode`, bip, compteur viseur, cooldown 1,8 s, bouton « Terminer », `onClose`)
- [x] `static/js/scan-inventory.js` (nouveau) : contrôleur page rapport (POST live + compteurs + saisie manuelle + reload à la fermeture)
- [x] `apps/inventory/forms.py` : scope ALL/LOCATION uniquement, `scope_category` retiré, emplacement obligatoire si LOCATION
- [x] `apps/inventory/views.py` : `add_scan` → JSON ; `create`/`reopen` → redirigent vers `report` ; suppression `session_detail`
- [x] `apps/inventory/urls.py` : suppression route `detail`
- [x] `templates/inventory/session_list.html` : sessions ouvertes → `report`
- [x] `templates/inventory/session_form.html` : sous-titre sans OfeliaScan + JS grise/active l'emplacement
- [x] `templates/inventory/session_report.html` : panneau scan + compteurs live + saisie manuelle + `scan-inventory.js`
- [x] `templates/inventory/session_detail.html` : supprimé
- [x] `templates/base.html` : chaînes i18n mode continu (« Terminer », « Scannés : »)
- [x] Tests `apps/inventory/tests/` (endpoint JSON, redirections, form scope, render) — 11 verts ; suite complète 331 verts
- [x] SPEC §6.5 + en-tête mises à jour
- [x] Gate i18n `scripts/i18n_check.py` → 0 (`scripts/translations_sprint18.py`, 51 entrées)
- [x] Itération 2 (retours Val) : dé-dup par code + bip/vibration + « exemplaire N » (`copy_index`) ; rapport **par notice** trié auteur/titre, codes Ofelia en pastilles vert/rouge ; suppression statut + « Marquer perdu » (`resolve_missing`). 336 tests verts.
- [x] Itération 3 (retour Val) : zone de décodage restreinte à une bande centrale (~1/4 hauteur) — `qrbox` (html5) + `inputStream.area` 37/37 % (Quagga) + guide visuel `.scan-camera-band` → un seul code-barres lu à la fois.
- [x] Déploiement Pi + test Val (HTTPS) — **validé Val 2026-05-31** (itér. 1+2+3 déployées, scan continu + dé-dup + exemplaire N + rapport par notice + bande de décodage)
- [x] Commit unique FEAT-045 + push origin/main

### FEAT-046 — Catalogage en scan caméra continu
> Spécifié 2026-05-31 (go Val). Miroir de FEAT-045 mais en **création** : scan
> continu d'ISBN (978/979) → `ScanItem` éditables → `finalize_scan_session()`.
> Décisions Val : notice existante = on n'ajoute que des exemplaires (notice
> intouchée) ; chaque nouvel exemplaire rattaché à la **session de catalogage**
> (`Item.catalog_session`) pour réimprimer uniquement ses étiquettes ; pendant le
> scan titre+auteur sinon ISBN+langue ; « exemplaire X » en gros au 2ᵉ exemplaire
> (>3 s) ; défauts catégorie+emplacement par lot, surchargeables par ligne.

- [x] Doc `docs/specs/FEAT-046-catalogage-camera-continu.md` + SPEC §6.1 + en-tête
- [x] Modèles (`apps/catalog/models.py`) + migration `0008_cataloging_session_fields` :
  - [x] `Item.catalog_session` (FK ScanSession, SET_NULL) — rattachement pour impression ciblée
  - [x] `ScanItem.category` (FK Category, SET_NULL) — catégorie par ligne
  - [x] `ScanSession.default_location` + `default_category` (FK, SET_NULL) — défauts du lot
- [x] `apps/api/services.py:finalize_scan_session` : pose `catalog_session` sur chaque exemplaire créé + `category` sur les **nouvelles** notices (notice matchée intouchée)
- [x] `apps/catalog/forms.py:ScanCatalogSessionForm` (défauts emplacement/catégorie + label)
- [x] `apps/catalog/views.py` : `scan_session_list`, `scan_session_create`, `scan_session` (hub), `scan_add` (JSON, règle <3 s ignoré / >3 s +1 exemplaire, rejet 290/291), `scan_item_delete`, `scan_session_commit`
- [x] `apps/catalog/urls.py` : routes `/catalog/scan/...`
- [x] Templates `catalog/scan_session_form.html`, `scan_session.html` (hub éditable), `scan_session_list.html`
- [x] `static/js/scan-cataloging.js` (POST live, « exemplaire X » en gros, repli saisie manuelle) + CSS `ofelia.css`
- [x] `apps/printing/views.py` + `labels_picker.html` : filtre `?catalog_session=` (n'imprimer que les étiquettes du lot, pré-cochées)
- [x] Entrée UI « Cataloguer en scannant » (catalogue + Avancé)
- [x] i18n : `scripts/translations_sprint19.py` (42 entrées × EN/ES/MG, overwrite + de-fuzzy) → `i18n_check.py` → 0 + `compilemessages`
- [x] Tests `apps/catalog/tests/test_cataloging.py` (13 cas) ; `pytest` vert (**349 passed**) + `makemigrations --check` → No changes
- [x] Déploiement Pi (rebuild Docker, migration `0008` au boot, conteneur healthy)
- [x] **Itér. 1 (retour Val)** — hub simplifié + mobile : titre/auteur/langue lecture seule (auteur au-dessus du titre, colonne large) ; catégorie/emplacement/état par lot (cases à cocher + « tout cocher ») ; Ex.+corbeille inchangés ; scroll horizontal mobile.
- [x] **Itér. 2 (BUG doublons ISBN)** — `ATOMIC_REQUESTS` tenait la transaction ouverte pendant le lookup → ligne invisible aux POST concurrents. Fix `@transaction.non_atomic_requests` + création avant lookup + réconciliation + garde client `inFlight`.
- [x] **Itér. 3 (titres FR manquants)** — `lookup_isbn_multi()` (OpenLibrary + Google Books + BnF + BNE en parallèle, titre SRU nettoyé au ` / `). Vérifié live Box.
- [x] **Test Val OK 2026-05-31** (Box HTTPS) — commit `1fa6c91` + push origin/main

## Sprint 18 — Nettoyage UI + guide utilisateur scan caméra

> Ouvert 2026-05-31 (temp.txt). Décisions Val : config impressions/sources
> retirée des Paramètres (défauts seed conservés) ; fix volume `/backup`
> éphémère **hors sprint** (juste documenté — voir [[project_backup_ephemeral]]).

### FEAT-047 — Nettoyage UI Paramètres + Avancé
- [x] Read and validate spec
- [x] Doc `docs/specs/FEAT-047-nettoyage-ui-parametres-avance.md`
- [x] `apps/core/admin_views.py` : retirer `printing_cards`/`printing_labels`/`zerotier`/`sources` de `FORMS` + nettoyer imports
- [x] `templates/core/admin/settings_index.html` : retirer lien « Comptes utilisateurs » + branches mortes
- [x] `templates/core/advanced.html` : Rapports → « Tous les rapports » seul ; Emplacements → icône étagère
- [x] `static/icons/library.svg` (Lucide étagère) + bascule `map-pin`→`library` sur location_list/location_form/session_report
- [x] Gate i18n `scripts/i18n_check.py` → 0 ; `manage.py check` 0 issue ; `pytest` 349 verts
- [x] Déploiement Pi (rebuild Docker → `144afaf`, healthy, migrate --check 0) + test Val OK 2026-05-31
- [x] SPEC §6.6 + en-tête mises à jour
- [x] Commit `144afaf` + push origin/main (groupé avec FEAT-049)

### FEAT-049 — Enrichissement métadonnées ouvert aux bibliothécaires
> Demandé Val 2026-05-31 (« avant de comiter »). Embarqué dans le commit FEAT-047
> (touche les mêmes fichiers `admin_views.py` + `advanced.html`).
- [x] `apps/core/admin_views.py` : 3 vues `enrichment_*` → `@require_role(Role.LIBRARIAN, Role.SUPERADMIN)`
- [x] `templates/core/advanced.html` : retrait du garde `{% if user.is_superadmin %}` autour du lien (déjà dans la section `{% if user.is_librarian %}`)
- [x] Vérif locale : librarian 200 + lien visible ; superadmin 200 ; READONLY 403 + lien masqué ; `manage.py check` 0 issue
- [x] SPEC §6.11 + en-tête mises à jour
- [x] Déploiement Pi (rebuild Docker → `144afaf`, healthy) + test Val OK 2026-05-31
- [x] Commit `144afaf` + push origin/main (groupé avec FEAT-047)

### Task — Guide utilisateur : scan caméra (catalogage / récolement / prêt-retour)
> Refléter dans `docs/user-guide/` (4 langues) que le scan passe désormais par
> la **caméra du navigateur** (FEAT-044 prêt/retour, FEAT-045 récolement,
> FEAT-046 catalogage par scan). OfeliaScan conservé (décision Val : « on garde
> ofeliascan pour l'instant ») comme complément mobile/masse.
- [x] Nouvelle page `premiers-pas/scanner-camera.md` (×4) : caméra navigateur, HTTPS, mode continu vs unique, repli clavier
- [x] Update `premiers-pas/saisie.md` (×4) : ajout du mode caméra navigateur + recadrage OfeliaScan
- [x] Nouvelle page `catalogue/catalogage-scan.md` (×4) : catalogage caméra continu (FEAT-046)
- [x] Rewrite `ofeliascan/recolement.md` (×4) : récolement caméra continu (FEAT-045) + note OfeliaScan masse
- [x] Note de cadrage en tête de `ofeliascan/activer.md` + `pret-retour.md` (×4) : caméra = défaut du site, OfeliaScan = complément
- [x] Recadrage des références scan obsolètes : `faire-pret.md`, `retour.md`, `dashboard.md`, `recherche.md` (×4)
- [x] `mkdocs.yml` : nav (scanner-camera + catalogage-scan)
- [x] **Restructure (retour Val)** : nouvelle section **Inventaire** (miroir app Avancé→Inventaire) regroupant Récolement + Catalogage par scan. Déplacement `ofeliascan/recolement.*` + `catalogue/catalogage-scan.*` → `inventaire/` (×4 langues), tous les liens internes corrigés (scanner-camera, localisations, etiquettes, glossaire, faq, activer), labels « Récolement OfeliaScan » → « Récolement », nav_translations Inventaire EN/ES/MG (Inventory/Inventario/Fijerena rakitra)
- [x] 1er build+déploi Box (avant restructure) — smoke test HTTP 200 FR/EN/ES/MG OK
- [x] Re-build mkdocs `--strict` (post-restructure) — OK, 0 warning (2026-05-31)
- [x] Re-déploiement Box `/bibliofelia/docs/` — section Inventaire smoke test 200 FR/EN/ES/MG
- [x] Test Val (navigateur) — approuvé 2026-05-31
- [x] Commit (après confirmation Val) — groupé avec FEAT-048

### FEAT-048 — Réorganisation des menus du guide utilisateur
> Demandé Val 2026-05-31. Regrouper les rubriques, alléger le menu, unifier le
> top menu. Décisions Val : Prêts = 7 pages (prêts/retours + réservations) ;
> cas courants réécrits en Q/R dans la FAQ (fichiers supprimés) ; suppression de
> `navigation.tabs` (top menu instable) ; OfeliaScan retiré du nav mais
> fichiers conservés (réintégration ultérieure).
- [x] `deploy_pi.sh` : détection rsync + fallback `tar | ssh` (rsync absent en Git Bash Windows)
- [x] `mkdocs.yml` : fusion Accueil→Premiers pas, Inventaire→Catalogue, Réservations→Prêts ; retrait menus OfeliaScan + Cas courants ; `not_in_nav: /ofeliascan/` ; suppression `navigation.tabs` ; `nav_translations` mises à jour (9 entrées/langue)
- [x] `faq.md` (×4) : nouvelle section « Cas difficiles » (4 Q/R, ancres `attr_list` stables `#livre-perdu`/`#supprimer-notice`/`#carte-perdue`/`#retard`) + clôture nettoyée
- [x] Suppression des 12 fichiers `cas-courants/*` ; repointage des ~28 liens internes → `faq.md#…` (script `repoint.py`, 24 fichiers)
- [x] `index.md` (×4) : sommaire d'accueil réécrit (8 rubriques)
- [x] `extra.css` : police menu latéral 0.78→0.68rem + interligne resserré (voir plus de sous-chapitres)
- [x] Build `--strict` 0 warning ; doc équilibrée 32 pages × 4 langues ; gate app `i18n_check.py` → 0
- [x] Déploiement Box + smoke test (200 pages clés, 404 anciennes URLs cas-courants, ancres FAQ présentes, OfeliaScan hors-nav toujours joignable)
- [x] Accents restaurés dans tout le nav (Prêts, Récolement, Caméra…) + i18n du menu **complétée** : sous-pages traduites EN/ES/MG (36 éléments/langue, build `--strict` 0 warning). Corrige les `<title>` EN/ES/MG qui restaient en français.
- [x] Test Val (navigateur) — approuvé 2026-05-31
- [x] Commit (après confirmation Val)

## Correctifs i18n post-FEAT-044 (BUG-018)

Signalés par Val 2026-05-30 (navigation espagnole).

- [x] **BUG-018** Chaînes non traduites (dashboard / formulaire exemplaires / Avancé)
  - [x] (A) Alerte relance dashboard : `msgstr[0]/[1]` du `blocktrans count` renseignés EN/ES/MG (édition directe `.po` — pluriels non gérés par les scripts)
  - [x] (B) `ItemForm.Meta.labels` traduits (`_()`) : Emplacement, État, Date d'acquisition, Source d'acquisition, Donateur, Notes (`apps/catalog/forms.py`) ; +`format="%Y-%m-%d"` sur `acquisition_date`
  - [x] (C) Faux positif « En attente d'OfeliaScan… » = build périmée (handoff retiré FEAT-044, « Annuler » caméra déjà traduit) → rebuild Box
  - [x] (D) `templates/core/advanced.html` : « (réservé Claude / support distant) » → « (réservé au support technique) »
  - [x] Traductions `scripts/translations_sprint17.py` + `makemessages` + `compilemessages` ; gate `i18n_check.py` → 0
  - [x] Docs : `docs/bugs/BUG-018-*.md`, SPEC en-tête
  - [x] Test Val (UI espagnole, dev local) — OK 2026-05-30
  - [x] Déploiement Pi (rebuild Docker `edubox-bibliofelia` + worker, couvre aussi C) — 2026-05-30

## Sprint 20 — FEAT-050 Catalogage Excel

> Spec validée 2026-06-05 (cf. `docs/specs/FEAT-050-catalogage-excel.md`). Deux
> fonctionnalités sous **Avancé → Inventaire → Catalogage Excel** :
> (1) vérifier un fichier Excel (passe 1 ISBN + passe 2 titre+auteur fuzzy)
> et produire un fichier annoté ; (2) importer un Excel d'ISBN dans
> BibliOfelia via une ScanSession virtuelle (réutilise pipeline FEAT-021 /
> FEAT-046, LOCATION/CATEGORY optionnelles appliquées par ligne).
>
> **NOTE DE REPRISE (2026-06-05, session ANQA → Tulear)** : Val a validé toute
> la spec et explicitement demandé : « code tout et déploie sur Pi, je teste
> à mon retour ou à distance sur le Pi ». Donc **aucun commit ni push** avant
> sa confirmation explicite. Le déploiement Pi se fait via `deploy_pi.sh`
> (ou tar+ssh fallback, cf. FEAT-048). Session interrompue ANQA car Tulear
> est le poste habituel ; reprise prévue depuis Tulear avec accès complet
> aux clés SSH Pi.

- [ ] **FEAT-050** Catalogage Excel — vérification + import
  - [x] Spec `docs/specs/FEAT-050-catalogage-excel.md` rédigée et validée Val 2026-06-05
  - [x] Dépendances : `openpyxl==3.1.5` + `rapidfuzz==3.10.1` dans `requirements.txt`
  - [x] Modèle `ExcelCatalogJob` (apps/catalog/models.py) + admin minimal
  - [x] Migration `apps/catalog/migrations/0009_excel_catalog_job.py` (id BigAutoField)
  - [x] Sources : `search(title, author, limit=5)` ajouté à `openlibrary.py`, `google_books.py`, `bnf.py`, `bne.py` + registre `SEARCHES`
  - [x] Module `apps/catalog/sources/_fuzzy.py` (score WRatio + seuils `CONFIDENCE_FLOOR=60` / `HIGHLIGHT_BELOW=75` + `best_candidate`)
  - [x] Service `apps/catalog/excel_catalog.py` : `validate_xlsx`, `run_verify_job`, `run_import_job`, `run_excel_catalog_job` (entrée django-q2)
  - [x] Vues `apps/catalog/views.py` : `excel_catalog_index/_verify_create/_import_create/_detail/_download` (`@require_role(LIBRARIAN, SUPERADMIN)`)
  - [x] Templates `templates/catalog/excel_catalog/` (index, _verify_form, _import_form, detail)
  - [x] Icône Lucide `file-spreadsheet` dans `static/icons/`
  - [x] Entrée menu `templates/core/advanced.html` section Inventaire
  - [x] URLs `apps/catalog/urls.py` (5 routes sous `/excel-catalog/`)
  - [x] Tests `apps/catalog/tests/test_excel_catalog.py` (16 cas, coverage `excel_catalog.py` 78 % / `_fuzzy.py` 90 %) ; suite complète **362 passed**
  - [x] i18n : `scripts/translations_sprint20.py` (35 × EN/ES/MG) + `makemessages` + `compilemessages` + gate `scripts/i18n_check.py` → 0
  - [x] Doc : `FEAT-050-catalogage-excel.md` → `DONE` ; SPEC §5.2 (`ExcelCatalogJob`) + §6.12 + Annexe B + en-tête mis à jour
  - [x] `docker compose -f docker-compose.dev.yml up --build` OK + `manage.py check` 0 issue + `makemigrations --check` No changes
  - [x] Déploiement Pi (2026-06-05)
  - [x] **Itér. 2 (retours Val 2026-06-05)** : passe 2 (titre+auteur) lancée sur **toutes** les lignes, y compris celles avec ISBN (recoupement des ISBN saisis à la main ; mismatch ISBN→orange) ; **Google Books interrogé sans clé** (`lookup`+`search`) ; constat : `isbn:` Google Books n'indexe pas certains ISBN (ex. `9786074440966`) → c'est la passe 2 par titre qui les retrouve. Clé API Google Books `AIzaSyDSiDi…` (fournie Val) posée en `Setting metadata.google_books_api_key` (dev + Pi) ; `Setting` enregistré dans `/admin/` (`apps/core/admin.py`). 17 tests excel + enrichment verts. Redéployé Pi.
  - [x] Test fonctionnel Val (navigateur, fichier réel) — **OK 2026-06-05** (vérification + import + passe 2 + clé Google Books)
  - [x] Commit unique `FEAT-050: catalogage Excel — vérification + import` + push origin/main
