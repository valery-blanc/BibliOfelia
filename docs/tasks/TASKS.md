# TASKS — BibliOfelia v1

Source de vérité de l'avancement v1. Une case `[x]` = livrable terminé et déployable. `[ ]` = à faire. `[!]` = bloqué (voir note).

Mise à jour : 2026-05-22 (Sprint 3 : Task #16 codée + 132 tests verts, en attente test Val ; Task #19 → avahi hôte décidé)

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
  - [x] Tests API : `apps/api/tests/test_api.py` — 15 tests verts, suite complète **132 passed**
  - [x] Doc : `docs/specs/FEAT-016-api-ofeliascan.md` + `SPEC §6.10` mis à jour
- [ ] **Task #19** Publication mDNS/DNS-SD `_bibliofelia._tcp.` (SPEC §6.10 / SPEC-CORR-001 §7) — *codée, test mDNS réel à faire sur la Pi*
  - [x] Commande `generate_avahi_service` (`apps/core/management/commands/`) : génère `/etc/avahi/services/bibliofelia.service` (TXT : `library_name`, `version`, `api_base`) à partir des `Setting` + réglages ; options `--output` / `--dry-run`
  - [x] Réglages `AVAHI_SERVICE_PATH` + `MDNS_SERVICE_PORT` (`config/settings/base.py`)
  - [x] Tests : `apps/core/tests/test_avahi.py` — 6 verts ; suite complète **138 passed**
  - [x] Doc : `docs/specs/FEAT-019-mdns-avahi.md` + `SPEC §6.10` mis à jour
  - [!] Régénération au wizard de premier démarrage — bloqué : dépend de Task #15 (Sprint 4) ; la commande est prête, reste à brancher le `call_command`
  - [!] Bind-mount `/etc/avahi/services/` + exécution au déploiement — bloqué : dépend de Task #18 (intégration keebee, Sprint 6)
- [ ] Test Val : découverte + appairage OfeliaScan + scan ISBN bout-en-bout (sur la Pi, après Task #18)

## Sprint 4 — Hors workflow principal

- [ ] **Task #11** Dashboard, rapports, paramètres (§6.6)
- [ ] **Task #12** Impression étiquettes + cartes (§6.7)
- [ ] **Task #13** Notifications offline + alertes (§6.8)
- [ ] **Task #14** Sauvegardes locales + cloud (§8)
- [ ] **Task #15** Wizard premier démarrage + données démo (§11.3-11.4)

## Sprint 5 — API complète + qualité

- [ ] **Task #20** API REST OfeliaScan — sessions de scan catalogage + endpoints récolement (reste de §6.10)
- [ ] **Task #17** Tests (pytest-django, coverage 70%)

## Sprint 6 — Déploiement

- [ ] **Task #18** Intégration keebee : docker-compose + nginx /bibliofelia/
  - Cohabitation avec Koha (qui reste sur `/biblio/`)
  - Modifier C:\WORK\keebee/docker-compose.yml + conf nginx
  - Build multi-arch arm64+amd64
  - Documenter dans `keebee/docs/specs/specs_keebee.md`
