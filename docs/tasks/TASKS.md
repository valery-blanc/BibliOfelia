# TASKS — BibliOfelia v1

Source de vérité de l'avancement v1. Une case `[x]` = livrable terminé et déployable. `[ ]` = à faire. `[!]` = bloqué (voir note).

Mise à jour : 2026-05-26 (Sprint 12 **CLOS** — FEAT-038 (cartes membres : fond crème, logo OFELIA filigrane, photo HG, langue BG, bloc droite), FEAT-039 (étiquettes 70×42 mm, titre wrap 2 lignes, auteurs 2 lignes, logo Ofelia), split paramétrage `labels` → `printing_cards` + `printing_labels`. BUG-013 v2 (sélecteur de langue qui perdait `/bibliofelia/` à chaque déploiement : wrapper `apps/core/i18n_views.py:set_language` force `FORCE_SCRIPT_NAME` + échange code langue même sur URL non résolue). **Gate i18n pérenne** : `scripts/i18n_check.py` exit != 0 si chaîne manquante ; documenté dans CLAUDE.md comme obligatoire avant tout commit ; 207 entrées EN/ES/MG appliquées (Sprints 10-12 incl. FORMS labels enrobés `gettext_lazy`). 304 tests verts (287 → 304). Sprint 11 **CLOS** — — BUG-014 (saisie clavier sur `/loans/lend/` + `/loans/return/` : bouton scan repassé `type="button"` + bouton « Valider » visible séparé pour la saisie clavier), FEAT-034 (UI réservations : liste d'attente PENDING sur fiche notice, expiration affichée sur exemplaires mis de côté, section « Réservations à relancer » sur page Retour, paramètres `default_loan_days`/`reservation_expiry_days`/`pickup_hold_days` exposés dans `/settings/loans/`), FEAT-035 (Setting `default_loan_days` global défaut 21, section « Relances à faire » bas du dashboard avec 10 prêts en retard), FEAT-036 (`Reservation.notified_at` + endpoint `POST /loans/reservations/<pk>/notify/`, page Réservations enrichie code Ofelia / dates avec heure / date limite retrait / police 16-17 px + cadre « Notifications à faire » entre tuiles et bannière scan sur dashboard), BUG-015 (DateInput format ISO `%Y-%m-%d` sur `MemberForm`, sinon locale FR remplit pas l'input HTML5), FEAT-037 (photo membre dans pagehead fiche + miniature sur form, expiration_date = registration_date + 1 an auto JS au change + initial `today + 1 an` à la création). 287 tests verts (266 → 287, +21). Migration `loans/0002_reservation_notified_at`. 5 vagues de déploiement Pi. 2 nouvelles entrées MEMORY (DateInput ISO format, bouton scan type=button + Valider visible). — Sprint 10 **CLOS end-to-end** — FEAT-032 + FEAT-033 validés Val 2026-05-24 sur la Pi, **+ OfeliaScan mobile mis à jour le 2026-05-24** : test prod 18:26 → session récolement scope=A1 reçue d'OfeliaScan avec 16 scans, 16 exemplaires relocate de J1 → A1 automatiquement. Bout-en-bout fonctionnel : catalogage OfeliaScan envoie `location_code`, picker récolement OfeliaScan envoie `scope_type=location` + `scope_location_code`, BibliOfelia déplace les items au scan. FEAT-032 : UI librarian /catalog/locations/ + endpoint GET /api/v1/locations testés OK. FEAT-033 : relocate auto vérifiée via UI web ET via OfeliaScan mobile. Commit `9d4fe83` + push + déploiement Pi (rebuild Docker + migration `0003`). 266 tests verts. — Sprint 8 **CLOS** — FEAT-025 **validé Val 2026-05-23** : refonte design global, 23 templates métiers harmonisés sur le design system OFELIA. Lot A pilote validé en premier (record_detail, member_detail, reports/index, settings_index), puis Lots B+C+D livrés d'un bloc. Helpers CSS ajoutés (`.req`, `.help-hint`, `.field-error`, `.form-control`, `details.advanced-section`, `.isbn-row`, `.form-actions`), `_field.html` migré `.form-row` → `.field`. Découverte d'infra : templates **embarqués au build Docker**, pas bind-mountés → rebuild obligatoire pour tout changement de template (documenté dans FEAT-025). — Sprint 7 **CLOS** — FEAT-024 **validé Val 2026-05-23** : scanner caméra navigateur sur Android Firefox HTTPS OK, fallback OfeliaScan automatique en HTTP LAN, Chrome Android sans Play Store via `S.browser_fallback_url`, bouton Annuler pendant polling. Décision UX : caméra-d'abord automatique, pas de toggle utilisateur. Décision infra : pas de cert auto-signé. 3 commits Pi `d7c8e8f` → `9d2af81` → `e9993a5`. FEAT-023 **validé Val 2026-05-23** : banner dashboard → OfeliaScan ouvre → scan livre → retour BibliOfelia → fiche notice affichée, bout-en-bout fonctionnel. Modèle `ScanHandoff` + endpoints `/api/v1/scan-handoff[/{token}]` + JS `scan-handoff.js` + 4 boutons « Scanner » câblés. BUG-010 entrypoint Dockerfile + BUG-011 CSRF cookie HttpOnly + Chrome Android `intent://` URL résolus. Sprints 3/5/6 clos. Reste pour Sprint 7 : Android-side OfeliaScan déjà fonctionnelle côté Val (intent filter + activity scan-one + POST callback) — implémentation Android terminée hors repo. Prochain sprint : FEAT-024 scanner caméra navigateur (HTTPS).)

## ⏭️ REPRISE — état au 23/08/2026

**Sprint 30 CLOS**, validé par Val le 2026-08-23 (« ok tout fonctionne »).
Quatre features : **FEAT-078** (export Excel du catalogue), **FEAT-079** (mise à jour
d'exemplaires), **FEAT-080** (identification complète au prêt et au retour),
**FEAT-081** (ancienne carte d'usager reconnue partout).

**Tests : 747 passed**, mesurés sur le code du commit de clôture Sprint 30, dans un
conteneur `--target dev` sur Fez (Docker absent du poste Windows, dev local cassé et
volontairement non réparé). Gate i18n : `python scripts/i18n_check.py` = **0**
(34 chaînes + 3 pluriels × EN/ES/MG dans `scripts/translations_sprint30.py`).

**Déploiement** : instances Fez `sanjuan` et `grand-saconnex` (healthy), secours
**Avignon** (source synchronisée + image rebâtie), **Box** (`edubox-bibliofelia`), et le
conteneur `bibliofelia-docs` rebâti pour le guide.

### 🔴 À FAIRE EN PREMIER

- **L'IP de la Box a changé : `192.168.0.147` → `192.168.0.204`.** Les anciennes fiches
  et `infra.md` annonçaient `.147`, qui ne répond plus (ni ping ni SSH, depuis le poste
  comme depuis Fez). **Protocole si elle a encore bougé** : balayer le /24 depuis Fez puis
  interroger la route publique, qui identifie la Box sans authentification :
  ```bash
  ssh fez 'for i in $(seq 1 254); do (ping -c1 -W1 192.168.0.$i >/dev/null 2>&1 &); done
           sleep 6; ip neigh | grep -v FAILED'
  ssh fez 'curl -s -m 5 http://192.168.0.<ip>/bibliofelia/api/v1/pairing/info'
  ```
  **Signal de reconnaissance** : la réponse contient `"box_name":"Canaima"`.
- **Reporter `TZ: ${TZ:-UTC}` dans `C:\WORK\keebee\docker-compose.yml`** (services
  `bibliofelia` et `bibliofelia-worker`) — hérité du Sprint 29, **toujours pas fait**.
  La modification n'existe que sur la Box, dans un fichier qui appartient à keebee.
  **Signal d'échec** : après un déploiement keebee, l'accueil de la Box réaffiche l'heure
  UTC au lieu de CEST. Sauvegarde sur la Box : `/opt/edubox/docker-compose.yml.bak-tz`.

### ⏳ Ouvert, avec son motif

- **Trois décisions rendues à Val**, aucune n'est un bug à corriger à l'aveugle :
  1. **Scan caméra et code externe** — `static/js/scan-camera.js` n'accepte qu'un EAN-13
     de préfixe 290/291/978/979. Un code externe alphanumérique (Code39/Code128) est donc
     refusé à la caméra, alors qu'il passe au clavier et à la douchette USB. Deux niveaux
     d'ouverture proposés, avec leurs risques — cf. Sprint 30.
  2. **Sexe de l'usager** — `Member` n'a pas ce champ ; l'ajouter = migration + donnée
     personnelle de plus.
  3. **Bouton « Remplacer la carte »** — trop facile à déclencher (cf. FEAT-081).
- **Code interne `OFL-…` non résolu par `find_item`** : seuls l'EAN13 et le code externe
  le sont. Un bibliothécaire qui lit le code interne à l'écran et le tape dans la
  recherche n'obtient rien — alors que la fenêtre « Mettre à jour des exemplaires »,
  elle, l'accepte. Correctif d'une ligne, groupé avec la décision (1) ci-dessus.
- **Guide utilisateur prêt/retour** : captures périmées depuis FEAT-080/081.
- **Sprint 26** : quatre « Test fonctionnel Val » jamais confirmés explicitement.
- **Catégorie `TEST`** restée sur la Box (`migrate_categories` ne supprime jamais).

### 🧯 Ce qui a été RÉFUTÉ — ne pas le rebâtir

- ⛔ **« La carte de Val n'était pas reconnue à cause d'un défaut de recherche »** — faux.
  Enquête : sa carte avait été **remplacée** le 2026-08-20 à 14:02 UTC (compteur
  `Setting.next_replacement_card_seq` passé de 900 000 000 à 900 000 001). Le vrai défaut
  était ailleurs : rien ne disait qu'il fallait **réimprimer**, et seul l'écran de prêt
  acceptait l'ancien numéro. Ne pas chercher un bug dans `classify_query`.
- ⛔ **« BibliOfelia peut imprimer un code externe »** — non : `printing/services.py`
  n'encode que des **EAN13** (`from barcode import EAN13`), or un code externe est
  alphanumérique. L'étiquette de test a été produite par un script **hors dépôt**
  (`C:\WORK\BibliOfelia\_test-etiquettes\`). Ne pas chercher l'option dans l'UI.
- ⛔ **« Un commentaire `{# … #}` peut tenir sur plusieurs lignes »** — non, vérifié en
  conteneur : `tag_re` de Django n'active pas `DOTALL`, le commentaire s'affiche **en clair
  dans la page**. Un test l'interdit désormais sur les écrans prêt et retour.


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
- [x] Test Val : valider le rendu des 3 captures + le scaffolding avant Task #2 — *superseded : guide complet validé Val 2026-05-31 (FEAT-048)*

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
- [x] **Validation finale Val** : ouvrir `http://192.168.0.147/bibliofelia/docs/` dans le navigateur, vérifier le bouton ? de la topbar BibliOfelia, naviguer dans les 4 langues — OK (bouton `?` validé sur la Box ; **KO sur les instances Avignon** → Sprint 26 / FEAT-057)

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

- [x] **FEAT-050** Catalogage Excel — vérification + import — **CLOS** (test Val OK 2026-06-05, commit + push)
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
  - [x] **Guide utilisateur (2026-06-07)** : nouvelle page `inventaire/catalogage-excel.md` (×4 langues FR/EN/ES/MG), nav sous **Catalogue** + `nav_translations`. Nouveauté : **liens cliquables vers l'app** (`/bibliofelia/<lang>/advanced/`, `/catalog/excel-catalog/`, `/catalog/scan/`) sur chaque mention de page/bouton, **un lien par langue** (le doc EN pointe vers `/en/…`, etc.), `target="_blank"`. Build `mkdocs build --strict` OK (4 langues).
  - [x] Test Val (relecture guide sur la Box) — **OK 2026-06-08** (après corrections : ISBN complet 10/13 chiffres + encadré ISBN_INVALID ; durée « 300 lignes ») + commit
  - [x] **Généralisation des liens cliquables au guide entier (2026-06-09)** : convention « toute mention d'une page/bouton d'app → lien vers l'URL de l'app » étendue à toutes les pages du guide ayant un **point d'entrée à URL fixe**. Mapping établi depuis les `urls.py` (Catalogue, Nouvelle notice, Localisations, Catalogage scan, Membres, Nouveau membre, Prêt, Retour, Consultation, Réservations, Inventaire/Récolement, Cartes, Étiquettes, Rapports, Retards, dashboard). 17 pages × 4 langues éditées (ajouter-livre, localisations, operations-lot, recherche, catalogage-scan, recolement, inscription, fiche, carte, faire-pret, retour, consultation, creer, notifications, retrait, cartes, etiquettes, exports, kpis, dashboard). Lien **dans la langue de la page** (`/<lang>/…`), `target="_blank"`. Volontairement **non liés** : boutons d'action contextuels (Enregistrer, Renouveler, Générer le PDF…) et fiches à pk dynamique (pas d'URL stable). Pages `ofeliascan/*` laissées de côté (hors navigation). Build `mkdocs build --strict` OK (4 langues), aucune fuite de langue vérifiée, déployé Box.

## FEAT-051 — Filtre emplacement dans le catalogue

> Demande Val 2026-06-05 : ajouter un filtre sur l'emplacement dans la page catalogue.

- [x] **FEAT-051** Filtre emplacement (`catalog:record_list`) — **CLOS** (test Val OK 2026-06-06, commit + push)
  - [x] Vue : param GET `location` → `records.filter(items__location_id=location).distinct()` ; contexte `locations` + `selected.location`
  - [x] Template : `<select name="location">` « Tous emplacements / <code> » après le filtre langue
  - [x] **Pagination** : `base_qs` (querystring sans `page`) → liens Précédent/Suivant conservent tous les filtres (retour Val : filtre perdu au changement de page)
  - [x] i18n : « Tous emplacements » EN/ES/MG (`translations_sprint20.py`) ; gate `i18n_check.py` → 0 ; `.mo` compilés
  - [x] Doc : SPEC §6.1 (filtres + pagination) + en-tête ; `docs/specs/FEAT-051-filtre-emplacement-catalogue.md`
  - [x] `manage.py check` 0 issue
  - [x] Test fonctionnel Val (navigateur) — **OK 2026-06-06** (filtre A2 + pagination conservée)
  - [x] Commit groupé FEAT-051 + BUG-019 + push origin/main

## BUG-019 — Enrichissement : titres manquants (quota Google Books 429)

> Retour Val 2026-06-05 : après import Excel + enrichissement, beaucoup de
> notices restent au placeholder `ISBN:…`. Cause = Google Books 429 (quota)
> attrapé silencieusement. Cf. `docs/bugs/BUG-019-google-books-quota-429.md`.

- [x] **BUG-019** Robustesse quota Google Books — **CLOS** (test Val OK 2026-06-06, commit + push)
  - [x] Diagnostic terrain Box (job #9 : 96 skipped ; `GB.lookup` → 429)
  - [x] `google_books.py` : throttle + back-off 429 (`_get_json`) → `SourceRateLimited`
  - [x] **Itér. 2 (retour Val « lent »)** : throttle rendu **adaptatif** (pleine vitesse normale, lent 100 s après un 429) + saut des notices déjà complètes en FILL_MISSING (`_record_is_complete`)
  - [x] `sources/__init__.py` : exception `SourceRateLimited`
  - [x] `enrichment.py` : `_try_sources(with_rate_limit=True)` + compteur `EnrichmentJob.rate_limited` + rapport
  - [x] `excel_catalog.py` : drapeau propagé + `ExcelCatalogJob.rate_limited` + colonne `RATE_LIMITED`
  - [x] Migration `catalog/0010` (2 champs `rate_limited`)
  - [x] UI : bandeaux « Quota Google Books atteint — relancez demain » (enrichment + excel detail)
  - [x] Tests (3 nouveaux) ; suite complète 369 passed
  - [x] i18n EN/ES/MG (`translations_sprint20.py`) ; gate → 0
  - [x] Doc : `BUG-019-*.md`, SPEC §6.11/§6.12/§5.2/en-tête
  - [x] Test fonctionnel Val — **OK 2026-06-06** (bandeau quota + vitesse restaurée après throttle adaptatif)
  - [x] Commit groupé FEAT-051 + BUG-019 + push origin/main

## Sprint 21 — FEAT-052 Support des périodiques ISSN (code-barres 977)

> Demande Val 2026-07-03 : la bibliothèque va accueillir des revues/magazines
> (EAN-13 préfixe 977 = ISSN). Les cataloguer comme les livres.
> Cf. `docs/specs/FEAT-052-issn-periodiques.md`.

- [x] **FEAT-052** Support ISSN transverse — **CLOS** (test Val OK 2026-07-03, commit squash + push)
  - [x] Helper `apps/core/issn.py` (check digit mod 11, `validate_issn`, `normalize_issn`, `issn_from_ean13`, `format_issn`)
  - [x] Modèle : champ `BibliographicRecord.issn` + contrainte unique si non-null ; `ScanKind.ISSN` ; propriété `issn_display` ; migration `catalog/0011_issn_periodical`
  - [x] Sources : `lookup_issn()` BnF (`bib.issn`) + BNE (`alma.issn`) ; registre `ISSN_SOURCES` ; `lookup_issn_multi()`
  - [x] Vue `scan_add` : branche 977 → `scan_kind=issn` + `lookup_issn_multi`
  - [x] Finalisation `finalize_scan_session` : matching/creation par ISSN, `document_type=magazine_issue` ; `_create_record` paramétré
  - [x] Formulaire notice : champ `issn` + `clean_issn` ; templates `_record_form` (édition) + `record_detail` (affichage)
  - [x] Scanner JS : `isAcceptableCode(v, allowIssn)` ; `scan-cataloging.js` passe `allowIssn:true` (977 en catalogage seulement)
  - [x] **Recherche ISSN** (retour Val : revue introuvable au catalogue) : `classify_query` `kind="issn"` (EAN13 977 ou ISSN saisi) ; `record_list` filtre `issn` ; `global_search` redirige ; correctif `clean_issn` max_length 9
  - [x] Tests : `test_issn.py`, `test_search.py`, cas 977 dans `test_cataloging.py` + `test_forms.py`
  - [x] Doc : `FEAT-052-*.md`, SPEC (en-tête + §5.2/§5.3/§6.1 + filtre scanner)
  - [x] i18n : `makemessages` + `translations_sprint21.py` + `i18n_check.py` → **0** + `.mo` compilés (sur la Box)
  - [x] `migrate` (0011 appliquée au boot) + suite pytest **387 passed** (sur la Box, `FORCE_SCRIPT_NAME=` neutralisé)
  - [x] Déploiement Box (branche `feat/issn-052`, rebuild bibliofelia + worker, healthy)
  - [x] Test fonctionnel Val — **OK 2026-07-03** (scan revue 977 en catalogage ; recherche par scan 977 + ISSN saisi ; 977 refusé en prêt)
  - [x] Commit unique squash `FEAT-052` → `main` + push origin/main

## Sprint 22 — FEAT-053 Import Excel : métadonnées de la fiche

> Demande Val 2026-07-03 : dans l'import Excel, pouvoir affecter toutes les
> infos de la fiche catalogue via colonnes optionnelles (AUTHOR, CATEGORY, TYPE,
> EDITOR, YEAR, LANGUAGE, TAGS + CONDITION pour l'exemplaire). Colonne présente
> et remplie → écrase l'existant ; cellule vide → conserve.
> Cf. `docs/specs/FEAT-053-import-excel-metadonnees.md`.

- [x] **FEAT-053** Import Excel — affectation des métadonnées — **CLOS** (commit `39a4c51` déjà poussé origin/main, gate i18n vert)
  - [x] Décisions Val : cellule vide = garder l'existant ; AUTHOR/TAGS = remplacer
  - [x] Code : `IMPORT_OVERRIDE_COLUMNS` (TITLE + 8 colonnes), résolveurs `_resolve_document_type`/`_resolve_item_state`, `_split_multi`, `_parse_row_overrides` (TITLE → `metadata_title` aussi), `_apply_import_overrides` (passe post-finalize, flux caméra/OfeliaScan inchangé)
  - [x] TITLE ajouté (oubli spec Val) : notice neuve titrée directement, sinon placeholder `ISBN:…`
  - [x] UI : `_import_form.html` documente les 9 colonnes + règle d'écrasement
  - [x] Tests : 8 cas ajoutés (`test_excel_catalog.py`)
  - [x] Doc : `FEAT-053-*.md`, SPEC §6.12 + en-tête
  - [x] **Guide utilisateur** (MkDocs ×4 langues) : `catalogage-excel` (nouvelles colonnes + règle d'écrasement) ; **rattrapage FEAT-052/ISSN** : `catalogage-scan` (section revues 977), `glossaire` (entrée ISSN), `ajouter-livre` (tip ISSN). Build `mkdocs --strict` → 0 warning
  - [x] i18n : `makemessages` + `translations_sprint22.py` + `i18n_check.py` → **0** + `.mo` compilés (sur la Box)
  - [x] pytest (sur la Box, `FORCE_SCRIPT_NAME=` neutralisé)
  - [x] Déploiement Box (branche `feat/import-excel-053`, rebuild bibliofelia + worker, healthy)
  - [x] Test fonctionnel Val
  - [x] Commit unique squash `FEAT-053` → `main` + push origin/main (commit `39a4c51`, vérifié présent sur origin/main 2026-07-08)

## Sprint 23 — Support douchette USB (keyboard-wedge) + catalogage douchette

> Ouvert le 2026-07-08 (temp.txt). Contexte : Val teste depuis **Bruxelles** (les
> autres machines ne sont pas accessibles physiquement) avec une **douchette USB**
> (lecteur code-barres en mode clavier HID) branchée sur le PC qui affiche le
> site. Le repo est sur Tulear, monté en `Z:\` (`\\tulear\C\WORK\BibliOfelia`) ;
> déploiement sur la Box (192.168.0.147), Val teste depuis le navigateur Bruxelles.
> Décisions Val (2026-07-08) : catalogage douchette = **nouvelle page dédiée** ;
> wedge global **alimente aussi prêt/retour/consultation** (pas seulement la
> navigation).

### BUG-020 — Scan douchette ouvre la page de téléchargement du navigateur
- [x] Read and validate spec
- [x] Doc `docs/bugs/BUG-020-douchette-download-page.md`
- [x] Fix = wedge global (FEAT-054) : `preventDefault`+`stopImmediatePropagation` sur toute la rafale + fenêtre de garde 300 ms testée en premier → aucune touche ne fuit vers un raccourci navigateur (Ctrl+J downloads / Ctrl+Tab)
- [x] SPEC §6.1 (comportement scan douchette)
- [x] Test Val **OK 2026-07-08** (scan recherche → fiche seule, plus de page download ni changement d'onglet)

### FEAT-054 — Support douchette USB (keyboard-wedge global) + catalogage douchette
- [x] Read and validate spec
- [x] Doc `docs/specs/FEAT-054-douchette-keyboard-wedge.md`
- [x] `static/js/scan-wedge.js` : détection rafale HID (timing), buffer, capture-phase `preventDefault`, routage
- [x] Routage contextuel : input scan focalisé/`data-wedge-primary` → remplir + submit ; sinon → `core:search?q=` (fiche notice / fiche membre 291)
- [x] `templates/base.html` : chargement `scan-wedge.js` + config JSON (URL search, seuils)
- [x] lend/return : `data-wedge-primary` sur le champ scan autofocus (carte + livre, alimentation sans clic). Consultation = pas de champ scan (compteur) → scan y route vers recherche
- [x] Modèle : `ScanSession.input_mode` (mobile/camera/douchette) + migration `catalog/0012` ; API OfeliaScan crée en `mobile`
- [x] Nouvelle page « Catalogage par douchette » : tuile Avancé→Inventaire + route `catalog:scan_douchette_create` + hub réutilisant `ScanSession` + `scan_add` (mode douchette : champ `data-wedge-primary`, bouton caméra masqué)
- [x] Tests : 3 cas `test_cataloging.py` (input_mode camera/douchette + hub marque le champ primaire)
- [x] i18n dict `scripts/translations_sprint23.py` (9 chaînes × EN/ES/MG)
- [x] i18n : `makemessages` + `translations_sprint23.py` (9×EN/ES/MG) + `compilemessages` + gate `i18n_check.py` → **0** (exécuté dans le conteneur Box ; `.po` resynchronisés dans Z:)
- [x] `pytest` : catalog+api scan sessions **29 passed** + loans+core **89 passed**, 0 régression (conteneur jetable sur la Box, `--ds=config.settings.test`)
- [x] SPEC §6.1 + en-tête
- [x] Déploiement Box 2026-07-08 (rebuild bibliofelia + worker healthy, migration `0012` appliquée, `scan-wedge.js` baké + collectstatic, nginx 302) — **déployé depuis Bruxelles via clé Pi copiée de Tulear**
- [x] Test fonctionnel Val **OK 2026-07-08** (depuis Bruxelles, douchette USB → Box : recherche, catalogage douchette, prêt/retour)
- [x] **Itér. 2 (retours Val 2026-07-08)** : cause racine BUG-020 identifiée = terminateur douchette **CR+LF** → `CR`=Ctrl+M (Entrée) et **`LF`=Ctrl+J = raccourci « page téléchargements »** (+ Tab possible = changement d'onglet). Le wedge v1 avait un bug d'ordre fatal : `if (ev.ctrlKey) return` s'exécutait **avant** la fenêtre de garde → le LF=Ctrl+J fuyait à chaque scan, même focus dans un `<input>` (un champ texte ne consomme pas Ctrl+J). Wedge réécrit : garde vérifiée **en premier**, suppression agressive de toute la salve en rafale (chiffres + Ctrl-combos), MAX_INTERKEY 50 ms, garde 300 ms, flush de secours. **Catalogage douchette** : la page ne se rechargeant jamais (pas de « fermeture caméra »), le tableau éditable + « Envoyer au catalogue » (gated `{% if items %}`) n'apparaissaient pas → « 2 scannés / Aucun livre » simultanés ; ajout d'un bouton « Terminer et voir le lot » (reload) + empty-state mode-aware. 3 chaînes i18n de plus (gate → 0). Redéployé Box (wedge hash `86a394489fcb`, healthy).
- [x] Commit (après confirmation Val) — commit `8d2a927` `FEAT-054 + FIX BUG-020` poussé origin/main

## Sprint 24 — Récolement à la douchette USB + guide catalogage douchette

> Ouvert le 2026-07-09 (questions Val). Suite de FEAT-054 : (1) le récolement
> n'était pas câblé à la douchette — pire, un scan douchette sur la page rapport
> tombait dans le fallback du wedge (`core:search`) et **quittait** la page sans
> jamais pointer ; (2) le catalogage douchette (FEAT-054) n'était pas documenté
> dans le guide utilisateur.

### FEAT-055 — Récolement à la douchette USB + guide catalogage douchette
- [x] Doc `docs/specs/FEAT-055-recolement-douchette.md`
- [x] Code : `data-wedge-primary autofocus` sur `#inv-manual-form input[name=ean]` (`templates/inventory/session_report.html`) → la douchette remplit + submit → handler AJAX `scan-inventory.js` poste à `inventory:add_scan` sans quitter la page. Aucune nouvelle chaîne d'app, aucune migration.
- [x] SPEC §6.5 (pointage douchette) + en-tête (version 2026-07-09)
- [x] Guide : section « Avec une douchette USB » ajoutée à `inventaire/recolement.{,en,es,mg}.md`
- [x] Guide : nouvelle page `inventaire/catalogage-douchette.{,en,es,mg}.md` (documente FEAT-054) + nav MkDocs + `nav_translations` ×3
- [x] Gate i18n `python scripts/i18n_check.py` → 0 (aucune nouvelle chaîne d'app pour FEAT-055 ; 4 chaînes BUG-021 retraduites — voir ci-dessous)
- [x] Déploiement Box (rebuild bibliofelia+worker healthy ; guide MkDocs `--strict` build OK + déployé 4 langues, page catalogage-douchette HTTP 200 ×4)
- [x] Test fonctionnel Val **OK 2026-07-09**
- [x] Commit unique groupé FEAT-055 + BUG-021 → `main` + push origin/main (commit `98aadd9`)

### BUG-021 — Catégorie « Impressions » disparue de /admin/settings/ (régression FEAT-047)
- [x] Doc `docs/bugs/BUG-021-settings-impressions-disparues.md`
- [x] Cause : FEAT-047 a retiré `printing_cards`/`printing_labels` de `FORMS` (`admin_views.py`) — seul accès UI au format des étiquettes
- [x] Fix : restauration des 2 sections dans `FORMS` + `settings_index.html` (icônes/sous-titres). ZeroTier/Sources non restaurées (hors périmètre). Aucune migration.
- [x] i18n : `scripts/translations_sprint24.py` (4 chaînes × EN/ES/MG, reprises de l'historique git)
- [x] SPEC §6.6 + en-tête
- [x] Gate i18n `makemessages` + `translations_sprint24.py` + `i18n_check.py` → **0** (dans le conteneur Box ; 4 chaînes × EN/ES/MG ; `.po` resync dans Z:)
- [x] Déploiement Box (rebuild bibliofelia+worker, healthy)
- [x] Test fonctionnel Val **OK 2026-07-09** (sections Impressions réapparaissent, réglage taille étiquettes OK)
- [x] Commit (groupé avec FEAT-055, commit `98aadd9`)

## Sprint 25 — Hébergement multi-instances + domaine bibliofelia.org

> Ouvert le 2026-07-18. Infra : domaine bibliofelia.org (Infomaniak), 2 nouvelles
> instances sur Avignon, migration Pi ofelia.zitoon.com → canaima.bibliofelia.org,
> SMTP, redirect apex. Travail additif, ne rien casser sur Avignon.

### FEAT-056 — Hébergement multi-instances + domaine bibliofelia.org
- [x] DNS : zone `dns_bibliofelia.org.txt` livrée + collée chez Infomaniak (Val)
- [x] Doc `docs/specs/FEAT-056-hebergement-multi-instances.md`
- [x] Phase 1 — canaima.bibliofelia.org : fichier Traefik + CSRF Pi + restart + vérif TLS (HTTP 200, cert OK, ofelia.zitoon.com conservé)
- [x] Phase 2 — redirect 301 apex/www → ofeliainternational.org/what-we-do/ (301 OK apex+www, certs OK)
- [x] Phase 3 — docs.bibliofelia.org (MkDocs statique + nginx + Traefik) — HTTP 200, cert OK, doc LOCALE Box intacte (additif)
- [x] Phase 4 — instances sanjuan + grand-saconnex (image BibliOfelia + 2 stacks web+worker+nginx + Traefik) — HTTP 200 setup wizard, static/cert OK, healthy
- [x] Phase 5 — SMTP docker-mailserver (Rspamd, 3 boîtes, DKIM généré, TLS acme.json, test interne OK). EN ATTENTE Val : DNS DKIM + port-forward 25/993 + rDNS
- [x] SPEC_BIBLIOFELIA.md §11.7 hébergement multi-instances + en-tête
- [x] Test fonctionnel Val **OK 2026-07-18** (web 1/2/3 OK ; mail SPF/DKIM/DMARC/réception validés bout-en-bout par Claude)
- [x] Commit unique `ac62620` + push origin/main (2026-07-18)

## Sprint 26 — Doc accessible sur les instances + sources de métadonnées + hub de catalogage

> Ouvert le 2026-08-03 (temp.txt, retours Val depuis `grand-saconnex.bibliofelia.org`).
> Découvertes d'investigation majeures : (a) les parsers SRU **BnF et BNE renvoyaient
> des notices vides** (les champs `dc:*` sont imbriqués sous `oai_dc:dc`/`srw_dc:dc`,
> notre `findall("dc:title")` ne cherchait qu'en enfant direct) → les 2 bibliothèques
> nationales ne remontaient **rien** depuis un moment ; (b) les instances Avignon
> n'avaient **pas** la clé API Google Books → quota anonyme épuisé (HTTP 429 systématique).
> Résultat cumulé : tout livre catalogué par scan sur ces instances arrivait avec un
> titre placeholder `ISBN:… - date`.
>
> **Question Val « 3 sessions validées, 6 livres, catalogue vide »** : répondu — les
> 6 notices ont bien été créées (`processing_summary` propres) puis **supprimées
> depuis l'app par `admin`** (audit log : 4 notices à 18:33:30, 2 à 19:24:23).
> Aucun bug de finalisation ; les titres placeholder (causes a+b) expliquent
> vraisemblablement la suppression.
>
> Décisions Val : sources → **Swisscovery + K10plus** ; lot validé →
> **consultation en lecture seule** (pas de réouverture) ; liens `/bibliofelia/…`
> en dur du guide → **laissés en l'état** pour l'instant.

### BUG-022 — Sources BnF & BNE : notices vides (parsing SRU)
- [x] Doc `docs/bugs/BUG-022-sru-namespace-dc.md`
- [x] Fix `_texts()` : `findall("dc:X")` → `findall(".//dc:X")` (`bnf.py` ; `bne.py` via le nouveau socle)
- [x] `sources/_alma_sru.py` : parsing SRU Alma factorisé (BNE + Swisscovery) + nettoyage du bruit MARC (`880-01`, `(IDREF)…`, rôle `aut`)
- [x] Les 3 chemins couverts : `lookup` (ISBN), `lookup_issn` (FEAT-052), `search` (FEAT-050 passe 2)
- [x] Tests `apps/catalog/tests/test_sources_sru.py` (11 cas, fixtures = captures réelles)
- [x] SPEC §6.11 + en-tête
- [x] Vérif terrain sur grand-saconnex : 3 des 6 ISBN du 2026-08-03 désormais retrouvés (0 avant) ; les 3 restants absents de toutes les sources
- [x] Test fonctionnel Val — inclus dans le OK global 2026-08-03 (points 1-6)

### BUG-023 — Google Books en 429 sur les instances hébergées (clé API absente)
- [x] Doc `docs/bugs/BUG-023-google-books-key-instances.md`
- [x] `metadata.google_books_api_key` + `metadata.sources` posés sur **sanjuan** et **grand-saconnex**
- [x] Aide du champ corrigée (la clé relève le quota, elle n'active pas la source)
- [x] Vérif : `google_books.lookup("9782882415417")` → « Muses » (429 → 200)
- [x] SPEC §6.11 + §11.7 (réglages à poser sur une instance neuve)
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)

### BUG-024 — Bouton « Terminer et voir le lot » persistant après rechargement
- [x] Doc `docs/bugs/BUG-024-douchette-terminer-bouton.md`
- [x] `scan_session.html` : bloc dans `#cat-refresh-wrap`, `hidden` si la liste est à jour
- [x] `scan-cataloging.js` : `revealRefresh()` réaffiche au premier scan `created`/`incremented`
- [x] Test `test_douchette_hub_hides_refresh_button_when_list_is_fresh`
- [x] SPEC §6.1
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)

### FEAT-057 — Guide utilisateur accessible depuis les instances hébergées
- [x] Doc `docs/specs/FEAT-057-docs-sur-instances.md`
- [x] `deploy/avignon/instance-nginx.conf` (versionné) : `location /docs/` → conteneur `bibliofelia-docs` + 301 `/docs` → `/docs/`
- [x] **Robustesse** : `resolver 127.0.0.11` + variable d'upstream sur les 2 `proxy_pass` — un 502 est survenu pendant le déploiement (nginx rechargé avant la recréation de `web`, IP en cache)
- [x] Déployé + rechargé sur les 2 instances ; `/docs/` = 200 sur grand-saconnex et sanjuan (4 langues), assets 200
- [x] canaima (Box) vérifiée : `/bibliofelia/docs/` déjà 200, rien à changer
- [x] Liens `/bibliofelia/<lang>/…` en dur du guide : **fermé en l'état** (décision Val 2026-08-03 : « on laisse tomber »), limite documentée dans FEAT-057
- [x] SPEC §11.7
- [x] Test fonctionnel Val **OK 2026-08-03** (bouton « ? » sur les 3 sites)

### FEAT-058 — Consulter un lot de catalogage validé
- [x] Doc `docs/specs/FEAT-058-consulter-lot-valide.md`
- [x] `scan_session_list.html` : bouton « Voir le lot » sur les lots validés
- [x] `scan_session.html` : tableau en lecture seule + « Voir la notice » par ligne
- [x] `views.py:scan_session` : `it.record_pk` depuis `processing_result["record_id"]`
- [x] Tests `test_finalized_hub_lists_items_read_only`, `test_session_list_links_to_finalized_batch`
- [x] SPEC §6.1
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)

### FEAT-059 — Google Books dans les sources d'enrichissement
- [x] Doc `docs/specs/FEAT-059-enrichment-sources-ui.md`
- [x] `MetadataSourcesForm` : `SOURCE_ORDER` unique, champs générés en boucle, toutes les sources actives par défaut
- [x] `enrichment_index` passe `(slug, libellé)` ; `enrichment_start` valide contre `SOURCE_ORDER`
- [x] `enrichment_index.html` : libellés lisibles + lien « Activer ou désactiver des sources »
- [x] Tests `apps/core/tests/test_metadata_sources_form.py` (5 cas dont smoke de la page)
- [x] SPEC §6.11
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)

### FEAT-060 — Sources européennes additionnelles (Swisscovery, K10plus)
- [x] Doc `docs/specs/FEAT-060-sources-europeennes.md`
- [x] Endpoints testés en direct : Swisscovery ✅, K10plus ✅ ; DNB (clé requise), SBN Italie (pas de SRU public), PORBASE Portugal (404) écartées — **fermé en l'état** (décision Val 2026-08-03) : IT/PT couverts par Google Books
- [x] `sources/swisscovery.py` (Alma) + `sources/k10plus.py` (contributeurs routés par rôle `(Verlag)`)
- [x] Registres `SOURCES` / `SEARCHES` / `ISSN_SOURCES` (Swisscovery seul) / `SOURCE_LABELS` + ordres de préférence
- [x] Tests dans `test_sources_sru.py`
- [x] SPEC §6.11
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)

### Guide utilisateur — expliquer le process de catalogage par lot
- [x] Section « À quoi sert une session de catalogage » (3 temps : scanner → modifier par lot → envoyer au catalogue) ajoutée à `inventaire/catalogage-scan` **et** `catalogage-douchette`, ×4 langues
- [x] Build `mkdocs build --strict` OK ; déployé sur les 2 instances + `docs.bibliofelia.org` + **guide local de la Box** (`/var/lib/bibliofelia-docs`)
- [x] Smoke test : section présente en FR/EN/ES/MG sur instance et sur la Box
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)

### Fin de sprint
- [x] `pytest` complet : **420 passed** (419 → 420, +16 nouveaux depuis 404 avant sprint, 0 régression)
- [x] `manage.py check` : 0 issue
- [x] Gate i18n : `makemessages` + `scripts/translations_sprint26.py` (9 × EN/ES/MG) + `i18n_check.py` → **0**
- [x] Déploiement **instances Avignon** (image `ofelia/bibliofelia:avignon` rebuildée, web+worker recréés, healthy) + **Box** (rebuild `edubox-bibliofelia` + worker, healthy)
- [x] Test fonctionnel Val **OK 2026-08-03** (points 1 à 6)
- [x] Commit unique groupé + push origin/main → commit `cddb518` (« clôture Sprint 26 »)

### Retours de test Val (2026-08-03) — 2e itération

> « points 1 à 6 ok » sur la 1re vague. 3 retours supplémentaires, plus la
> demande explicite : « il faut rajouter une erreur pour les ISBN manquants ou
> invalides ». Les 2 points laissés ouverts sont **fermés en l'état**.

#### BUG-025 — Import Excel : ligne sans ISBN escamotée sans erreur
- [x] Diagnostic terrain : job #1 sur grand-saconnex, `Collection_L483731.xlsx`, 105 lignes de données, `job.total = 104` → la perte est **à la lecture**, pas à l'import ; ligne 85 (« Ruiz, Miguel — L'art de vivre et de mourir ») a une cellule ISBN vide
- [x] Doc `docs/bugs/BUG-025-excel-ligne-sans-isbn.md`
- [x] Fix `run_import_job` : ligne remplie sans ISBN → comptée (`total`/`processed`), `errors++`, rapport `ISBN_MISSING` + `label` « Auteur — Titre » (`_row_label`) ; lignes entièrement vides toujours ignorées en silence
- [x] `ISBN_INVALID` reçoit le même `label`
- [x] **Bandeau rouge « N lignes non importées »** sur la page du job dès `errors > 0` (demande Val) + phrase explicative par code dans le tableau
- [x] Tests `test_import_job_reports_row_without_isbn`, `test_import_job_ignores_fully_empty_rows`
- [x] SPEC §6.12 + en-tête
- [ ] Test fonctionnel Val (relancer l'import : 105 lignes → 104 notices **+ 1 erreur visible**)

#### BUG-026 — Commentaires `{# … #}` multi-lignes affichés à l'écran
- [x] Doc `docs/bugs/BUG-026-commentaires-django-multiligne.md`
- [x] Cause : le lexer Django compile `({%.*?%}|{{.*?}}|{#.*?#})` **sans `re.DOTALL`** → un commentaire multi-ligne n'est pas un token et traverse jusqu'au HTML
- [x] 5 occurrences converties en `{% comment %}` : `scan_session.html` (celle vue par Val), `session_report.html`, `record_bulk_delete.html`, `errors/_error_page.html`, `500.html` — les 4 dernières étaient des régressions latentes jamais signalées
- [x] **Garde-fou** `apps/core/tests/test_template_comments.py` : scanne tous les templates, échoue si un `{#` n'a pas son `#}` sur la même ligne
- [ ] Test fonctionnel Val

#### FEAT-061 — Accès au guide sur smartphone
- [x] Doc `docs/specs/FEAT-061-guide-accessible-mobile.md`
- [x] Cause : le bouton « ? » porte `.hide-sm` (masqué < 600 px) → guide inatteignable en portrait
- [x] Entrée « Guide utilisateur » ajoutée en tête du menu utilisateur, `.only-sm` → pas de doublon avec l'icône sur grand écran ; aucune chaîne i18n nouvelle, aucun CSS nouveau
- [ ] Test fonctionnel Val (smartphone portrait)

#### 2e vague — vérifications
- [x] `pytest` : **423 passed** (420 → 423, 0 régression)
- [x] `manage.py check` : 0 issue
- [x] Gate i18n : `makemessages` + `translations_sprint26.py` (12 × EN/ES/MG) + `i18n_check.py` → **0**
- [x] Redéploiement : image Avignon rebuildée + web/worker recréés (grand-saconnex, sanjuan) ; Box rebuildée + recréée ; smoke tests 200
- [ ] Test fonctionnel Val
- [x] Commit unique groupé + push origin/main → commit `cddb518` (« clôture Sprint 26 »)

## Sprint 27 — Imprimante à ruban Brother QL-810W

> Ouvert le 2026-08-18 (demande Val) : « j'ai une imprimante brother QL-810Wc
> avec un ruban rouge noir de 62mm de large (sur 5m en continu). l'imprimante
> est connectée au pc bruxelles. il faut ajouter le support de cette imprimante
> pour l'impression des étiquettes et des cartes membres ».

### FEAT-062 — Support imprimante Brother QL-810W (ruban continu 62 mm noir/rouge)
- [x] Constat matériel : `Get-Printer` sur Bruxelles → `Brother QL-810W` sur **USB001**, non partagée ; scan LAN 9100 depuis la Box → seul `192.168.0.201` répond = **DCP-L3550CDW** (laser). La QL **n'est pas joignable en réseau** → ni CUPS ni raster `brother_ql` possibles depuis la Box ou Avignon
- [x] Décision Val : PDF à la géométrie du ruban + dialogue d'impression du navigateur (marche aussi sur les instances Avignon) ; carte membre au **format carte bancaire couché** (85,6 × 54 mm tourné à 90°)
- [x] Doc `docs/specs/FEAT-062-imprimante-ql810w.md`
- [x] `services.py` : `_roll_settings`, `_accent`, `render_item_labels_roll_pdf`, `render_member_cards_roll_pdf`, `_draw_roll_item_label`, `_draw_roll_member_card` ; retraits `ROLL_INSET_MM=2` (largeur) et `ROLL_FEED_INSET_MM=3` (avance papier)
- [x] Défauts 62 × 36 mm (étiquette) et 62 × 92 mm (carte) — calés sur les marges du pilote après vérification du rendu à 300 dpi
- [x] Accents en **rouge pur** (nom bibliothèque, code Location, « Carte de membre ») ; **code-barres toujours noir**
- [x] `RollPrinterFormatForm` + section `printing_roll` + seed `roll_printer_format`
- [x] Vues `labels_roll_pdf`, `cards_roll_pdf`, `roll_print` + factorisation `_pdf_response` / `_selected_items` / `_selected_members`
- [x] `templates/printing/roll_print.html` (iframe + `print()` auto, bouton de secours) + boutons « Ruban 62 mm » sur les 2 écrans de sélection
- [x] Tests `apps/printing/tests/test_roll_printing.py` (15 cas : géométrie, 1 page par sortie, réglages, ruban étroit, vues, bouton masqué)
- [x] Vérification visuelle du rendu (PDF → PNG 300 dpi depuis le conteneur)
- [x] SPEC §6.7 + en-tête
- [x] Test fonctionnel Val — OK 2026-08-18 (cf. « c'est ok pour les étiquettes livres et les cartes membres » plus bas)

### Fin de sprint
- [x] `pytest` complet : **438 passed** (423 → 438, +15 nouveaux, 0 régression)
- [x] Gate i18n : `makemessages` + `scripts/translations_sprint27.py` (22 × EN/ES/MG) + `i18n_check.py` → **0**
- [x] Guide utilisateur `impressions/etiquettes` + `impressions/cartes` ×4 langues (section « Imprimer sur une étiqueteuse à ruban ») ; `mkdocs build --strict` OK, déployé sur la Box, smoke test 200 + section présente en FR/EN/ES/MG
- [x] Déploiement Box 2026-08-18 (rebuild `edubox-bibliofelia` + worker, healthy, 0 migration en attente, `.mo` recompilés, seed `roll_printer_format` OK)
- [x] Smoke tests sur la Box : pickers, page ruban et PDF en 200 (FR/EN/MG), section de réglages `printing_roll` en 4 langues
- [x] Déploiement **instance grand-saconnex** 2026-08-18 — ⚠️ **les instances ne sont plus sur Avignon** : depuis le failover du 2026-08-08, le nœud **actif est Fez** (`192.168.0.221`) et porte `bo-grand-saconnex-*`, `bo-sanjuan-*`, `bibliofelia-docs`, traefik. Sync `~/BibliOfelia` + `docker build --target prod -t ofelia/bibliofelia:avignon` + `compose up -d web worker` → web *healthy*, 0 migration en attente, seed `roll_printer_format` OK
- [x] Smoke tests grand-saconnex : pickers, page ruban, PDF étiquettes en 200 ; réglages `printing_roll` en 200 ; `https://grand-saconnex.bibliofelia.org/` en 302 → `/fr/` (le PDF cartes rend 302 « aucune sélection » : l'instance a 0 usager et 104 exemplaires)
- [x] Guide en ligne rebuildé (`bibliofelia-docs`) : section ruban en 200 sur `docs.bibliofelia.org` (FR/EN/ES/MG) et sur `grand-saconnex.bibliofelia.org/docs/`
- [x] Nœud de **secours Avignon** remis au même niveau (sync + rebuild image) — sinon une bascule annulerait le déploiement
- [x] Instance **sanjuan** : recréée sur la nouvelle image lors de la clôture Sprint 27

### Retours de test Val (2026-08-18) — 2e itération étiquettes

> « le titre occupe toute la place […] supprime le code interne […] tous les
> textes et le code barre en monochrome, logo en niveaux de gris, même taille
> et même police, auteur en italique […] supprime la page intermédiaire ».

- [x] Titre pleine largeur : wrap sur la **largeur mesurée** (`_wrap_to_width` + `pdfmetrics`) au lieu d'un quota de 38 caractères ; `_fit_to_width` pour les textes d'une ligne
- [x] `internal_id` retiré du pied ; le code Ofelia passe à gauche, l'emplacement reste à droite
- [x] Étiquette **entièrement monochrome** (le code Location était rouge) ; `_accent()` ne sert plus qu'aux cartes membres
- [x] Logo Ofelia converti en **niveaux de gris** avec alpha conservé (`_static_logo_grayscale`, Pillow)
- [x] Tous les textes en `Helvetica-Bold` 7,5 pt ; auteurs en `Helvetica-BoldOblique` (vérifié : les 2 polices sont bien dans le PDF)
- [x] Bloc titre + auteurs **centré verticalement** : un titre d'une ligne ne creuse plus de trou
- [x] Taille d'étiquette inchangée (62 × 36 mm)
- [x] **Page intermédiaire supprimée** : bouton → PDF direct (`formtarget="_blank"`), vue `roll_print` + route + template retirés
- [x] Vérification visuelle 300 dpi : titre court et titre de 66 caractères (2 lignes pleines, sans troncature)
- [x] Tests : 33 dans `apps/printing/` (wrap mesuré, troncature, logo gris sans composante colorée, page intermédiaire en 404, bouton `_blank`)
- [x] Gate i18n rejoué : 1 chaîne modifiée, 10 chaînes de la page supprimée retirées de `translations_sprint27.py` → `i18n_check.py` = **0**
- [x] SPEC §6.7 + en-tête + `FEAT-062-*.md` mis à jour
- [~] **Groupage portrait essayé puis retiré** — 1re version : 2 étiquettes sur une page de 62 × 72 mm pour que Chrome ouvre en portrait. **Test Val KO** : sa QL coupe tous les 35 mm et ne peut pas honorer une page plus longue (elle a tenté de faire tenir les 2 étiquettes dans une coupe) ; par ailleurs « portrait » était déjà sélectionné dans son dialogue
- [x] Retour à **1 étiquette par page, 62 × 35 mm** : `_labels_per_page()` et le réglage `portrait_pages` supprimés
- [x] Défaut `label_length_mm` 36 → **35** (code + seed + formulaire) ; aide reformulée en « longueur de coupe réglée dans le pilote »
- [x] `Setting.roll_printer_format` corrigé en base sur la Box **et** sur grand-saconnex (36 → 35, `portrait_pages` retiré) — le seed ne touche pas les valeurs existantes
- [x] Rendu 300 dpi revérifié en 62 × 35 : titre de 66 caractères sur 2 lignes pleines, 1 page par étiquette

#### Retour Val : « je dois passer par use system dialog + more settings à chaque fois »
- [x] Contenu des étiquettes **et** des cartes validé par Val
- [x] Inventaire des formats du pilote relevé sur Bruxelles (`System.Drawing.Printing.PrinterSettings`) : le format continu « 62mm » vaut **62 × 89,9 mm**
- [x] Carte membre alignée dessus : `card_length_mm` 92 → **89** (juste en dessous, pas de rognage), marge d'avance des cartes ramenée à 1,7 mm (`ROLL_CARD_FEED_INSET_MM`) pour garder 85,6 × 54 exact → **plus de hauteur à saisir pour les cartes**
- [x] `Setting.roll_printer_format` corrigé en base sur la Box et grand-saconnex (92 → 89)
- [x] Constat documenté : longueur de coupe et orientation sont des propriétés du **pilote Windows**, pas du PDF — le serveur ne peut que proposer une géométrie
- [x] **Test fonctionnel Val OK 2026-08-18** : « c'est ok pour les étiquettes livres et les cartes membres », puis « ok c'est bien comme ça » après l'alignement de la carte sur 89 mm
- [~] **Piste non retenue pour l'instant** : créer 2 objets imprimante Windows (même pilote, même port USB001) « QL-810W — Étiquettes » 35 mm et « QL-810W — Cartes » 89 mm, chacun avec ses *Printing Defaults* — Chrome mémorise ses réglages par destination, donc plus qu'un choix d'imprimante par impression. `Add-Printer` est scriptable ; les *Printing Defaults* se règlent une fois dans l'interface du pilote. **Touche le poste de Val, à faire sur sa demande.**

#### Infra + clôture Sprint 27
- [x] **Failover Fez ⇄ Avignon documenté dans le repo** : table des serveurs de `CLAUDE.md` corrigée (Fez = nœud actif, Avignon = secours) + section « ⚠️ Failover Fez ⇄ Avignon » avec la procédure de déploiement d'instance ; encart équivalent dans SPEC §11.7. Mémoire `project_bibliofelia_org_infra` corrigée (elle disait encore « instances sur Avignon »)
- [x] Déploiement **toutes cibles** 2026-08-18 : Box (`edubox-bibliofelia` + worker), **grand-saconnex**, **sanjuan** (recréée sur la nouvelle image), guide en ligne `bibliofelia-docs`, + nœud de secours Avignon (sync + build)
- [x] `Setting.roll_printer_format` aligné sur les 3 bases (Box, grand-saconnex, sanjuan) : `label_length_mm` 35, `card_length_mm` 89, `portrait_pages` retiré
- [x] Smoke tests : `sanjuan.bibliofelia.org` et `grand-saconnex.bibliofelia.org` en 302 → `/fr/`, `docs.bibliofelia.org` en 200, pickers et réglages `printing_roll` en 200 sur les 2 instances
- [x] `pytest` : **444 passed** (438 → 444) ; `manage.py check` : 0 issue ; gate i18n : **0**
- [x] Commit groupé + push origin/main

## Sprint 28 — Codes externes, provenance, langues/enfants usagers, catégories abrégées

> Ouvert le 2026-08-19 depuis `temp.txt` (6 features). Décisions Val prises au
> lancement (questions posées avant tout code) :
> 1. **Provenance** = liste gérée (modèle dédié, comme les emplacements), pas de texte libre.
> 2. **Catégorie abrégée** portée par la **catégorie** (héritée par les notices), pas par la notice.
> 3. Saisie des abréviations : **nouvel écran « Catégories »** dans l'UI biblio + colonne Excel
>    (les catégories n'étaient éditables que dans `/admin/`, jamais montré aux bibliothécaires).
> 4. Suppression des exemplaires d'une provenance : **depuis la recherche d'exemplaires**
>    (filtrer → tout cocher → supprimer), pas d'écran dédié dans les Paramètres.
>
> Relevé terrain 2026-08-19 (avant migration destructive `parent_account`) :
> Box 22 usagers dont **1 avec parent_account** ; sanjuan 0 usager ;
> grand-saconnex 1 usager / 104 exemplaires, 0 parent_account.

### FEAT-063 — Code Ofelia externe (20 car. alphanumériques)
- [x] Doc `docs/specs/FEAT-063-code-ofelia-externe.md`
- [x] `Item.external_code` + contrainte d'unicité partielle (`item_external_code_unique_not_blank`) + migration `0013`
- [x] `apps/catalog/lookup.py` : `find_item()` / `normalize_external_code()` / `is_valid_external_code()` — garde-fou : pas de requête pour du texte libre
- [x] Câblage : recherche globale, recherche catalogue, prêt, retour, récolement (pointage stocké sous le code Ofelia), API OfeliaScan
- [x] `ItemForm` (normalisation + message clair si code déjà pris) ; `ItemBulkCreateForm` refuse code + copies > 1 ; colonne « Code externe » sur la fiche notice et le picker d'impression
- [x] Import Excel : colonne `EXTERNAL_CODE` + alias (`_resolve_column`), avertissements `EXTERNAL_CODE_DUPLICATE` / `EXTERNAL_CODE_INVALID` expliqués dans le rapport
- [x] Tests : 35 nouveaux (`test_external_code.py` 33 + 2 prêt/retour) — suite **479 passed**

### FEAT-064 — Provenance des exemplaires + recherche par exemplaire
- [x] Doc `docs/specs/FEAT-064-provenance-exemplaires.md`
- [x] Modèle `Provenance` (code + libellé + notes) + `Item.provenance` (PROTECT) + migration `0014`
- [x] Écran de gestion Provenances (liste avec compteur cliquable, création, édition, suppression refusée tant que des exemplaires la portent) + entrée dans « Avancé »
- [x] `ScanSession.default_provenance` appliquée dans `_add_copies` + champ dans le formulaire de lot
- [x] Import Excel : colonne `PROVENANCE` (résolue par code **ou** libellé, alias `ORIGINE`), avertissement `PROVENANCE_UNKNOWN`
- [x] Catalogue : case « Chercher les exemplaires » (`mode=items`) → 1 ligne par exemplaire,
      colonnes Code Ofelia / Code Ofelia externe / Provenance, colonne « Ex. » retirée
      (partial `catalog/_item_results.html`, desktop + mobile, lecture seule si non biblio)
- [x] Filtre provenance (mode notice = « au moins un exemplaire », mode exemplaire = la ligne elle-même) + actions de masse : affecter une provenance (biblio), supprimer les exemplaires (superadmin, avec tombstones FEAT-043 et clôture des prêts en cours)
- [x] Tests : 26 nouveaux (`test_provenance.py`) — suite **505 passed**

### FEAT-065 — Langues parlées de l'usager
- [x] Doc `docs/specs/FEAT-065-langues-parlees-usager.md`
- [x] `Member.spoken_languages` (JSON) + `spoken_languages_other` + migration `members/0004`
- [x] `apps/members/languages.py` (22 langues, codes figés, `labels_for` conserve un code inconnu) + `LanguageChecklistWidget` / `SpokenLanguagesField` partagés avec les enfants + CSS `div.lang-grid`
- [x] Formulaire (encadré de cases + champ libre « autres langues ») + affichage sur la fiche
- [x] Tests : `test_languages_and_children.py` (FEAT-065 : 9 cas)

### FEAT-066 — Enfants de l'usager (remplace `parent_account`)
- [x] Doc `docs/specs/FEAT-066-enfants-usager.md`
- [x] Suppression `Member.parent_account` (modèle, form, admin, vues, fiche, page de suppression) ; le test « détache les dépendants » devient « supprime les enfants »
- [x] Modèle `MemberChild` (sexe, prénom, âge, langues + autres langues), CASCADE depuis l'usager
- [x] Formset inline dans le formulaire usager (ajout/retrait de lignes en JS, sans dépendance) ; une ligne au prénom vide est ignorée, ce qui fait office de suppression
- [x] **Piège Django corrigé** : marquer `DELETE` *après* `super().clean()` est sans effet — `BaseModelFormSet.clean()` met `deleted_forms` en cache via `validate_unique()`, et la ligne vidée était enregistrée au lieu d'être supprimée
- [x] Tests : `test_languages_and_children.py` (FEAT-066 : 7 cas) — suite **520 passed**

### FEAT-067 — Catégorie abrégée + écran de gestion des catégories
- [x] Doc `docs/specs/FEAT-067-categorie-abregee.md`
- [x] `Category.abbreviation` (non traduite : une cote est physique) + migration `0015`
- [x] Écran Catégories (liste code/nom/cote/parent/nb notices, création, édition, suppression qui ne supprime aucune notice) + entrée dans « Avancé » — 1re UI biblio pour les catégories
- [x] `seed_defaults` : 8e colonne `abbreviation` sur les 16 catégories, backfill si vide, **jamais** d'écrasement d'une cote saisie à la main
- [x] Import Excel : colonne `CATEGORY_ABBR` (+ alias `ABREVIATION`…), avertissement `CATEGORY_ABBR_ORPHAN` si aucune catégorie n'est résolue ; cote affichée sur la fiche notice
- [x] Tests : 14 nouveaux (`test_categories.py`)

### FEAT-068 — Étiquettes de tranche (62 × 35 mm, abréviation centrée)
- [x] Doc `docs/specs/FEAT-068-etiquettes-tranche.md`
- [x] `render_spine_labels_roll_pdf` + `spine_layout()` : dichotomie de 96 pt à 10 pt jusqu'à ce que la cote tienne en largeur **et** en hauteur — « PER » remplit l'étiquette, « RO FI ADO » sort sur 2 lignes comme la maquette
- [x] Vue `spine_labels_roll_pdf` + route + bouton « Étiquettes de tranche » (PDF direct, `_blank`) ; exemplaires sans cote ignorés, message clair si aucun n'en a
- [x] Vérification visuelle 300 dpi (pypdfium2) : « RO FI / ADO », « PER » pleine étiquette, « BANDES DESSINEES JEUNESSE » sur 3 lignes sans débordement
- [x] Tests : 19 nouveaux (`test_spine_labels.py`)

### Fin de sprint
- [x] `pytest` complet : **553 passed** (444 → 553, +109 nouveaux, 0 régression)
- [x] `manage.py check` : 0 issue
- [x] Gate i18n : `makemessages` (via l'image Docker sur Fez — pas de `xgettext` sur le poste) + `scripts/translations_sprint28.py` (**119 chaînes + 15 formes plurielles** × EN/ES/MG) + `i18n_check.py` → **0**
- [x] **Trou du gate comblé** : `i18n_check.py` n'auditait que `msgstr`, jamais `msgstr[0]`/`msgstr[1]` — 15 `{% blocktrans count %}` sortaient en français dans les 3 autres langues, dont 7 antérieurs au sprint (emplacements, récolement, rapport d'import). Contrôle ajouté + vérifié en le faisant échouer volontairement
- [x] Guide utilisateur ×4 langues : 2 pages neuves (`catalogue/provenances`, `catalogue/categories`) + sections ajoutées à `catalogue/recherche` (code externe, mode exemplaires), `catalogue/exemplaires` (code externe, provenance), `usagers/inscription` (langues parlées, enfants), `impressions/etiquettes` (étiquettes de tranche), `inventaire/catalogage-excel` (3 colonnes) ; nav + `nav_translations` mis à jour ; `mkdocs build --strict` OK
- [x] **Box** déployée (rebuild + migrations `catalog/0013-0015` + `members/0004`, seed = 16 cotes backfillées, healthy, 0 migration en attente) ; guide local remplacé
- [x] **Gotcha guide sur la Box** : remplacer `/var/lib/bibliofelia-docs` par un `mv` casse le bind-mount nginx (l'inode monté suit l'ancien répertoire) → nginx servait encore l'ancien guide (404 sur les pages neuves). Il faut **vider et réextraire dans le répertoire monté**, jamais le remplacer
- [x] **Instances Fez** (nœud actif) : image rebuildée, `grand-saconnex` (104 exemplaires, 1 usager) et `sanjuan` recréées, migrations OK, données intactes, écrans neufs en 200
- [x] Guide en ligne `bibliofelia-docs` rebuildé (le contexte de build est `~/BibliOfelia/docs/user-guide` : il faut aussi y synchroniser les sources du guide) — `docs.bibliofelia.org` et `/docs/` des instances en 200 (FR/EN/ES/MG)
- [x] **Nœud de secours Avignon** resynchronisé + image rebuildée
- [x] Test fonctionnel Val **OK 2026-08-21**
- [x] Commit unique groupé + push origin/main

### Retours de test Val (2026-08-20) — 2e itération

> Remarques déposées dans `temp2.txt`. Arbitrages pris avant de coder :
> 1. **Catégories** : remapper les anciennes vers les nouvelles **puis les supprimer**.
> 2. **Langues** : normaliser les codes hérités de la BnF (`fre-fre` → `fr`, 94 notices sur la Box).
> 3. **Barres d'action** : fenêtre **notices** = catégorie + emplacement ; fenêtre
>    **exemplaires** = provenance (correction Val : chaque information se pilote au niveau
>    où elle appartient).
> 4. **Carte de membre** : prénoms de la famille en **colonne de droite**.

#### BUG-027 — Provenance absente de plusieurs écrans
- [x] Doc `docs/bugs/BUG-027-provenance-ecrans-manquants.md`
- [x] Colonne Provenance dans le tableau des exemplaires de la fiche notice **et** dans le picker d'impression
- [x] Page d'import Excel : `EXTERNAL_CODE`, `PROVENANCE`, `CATEGORY_ABBR` annoncés avec leur description
- [x] Audit des autres écrans montrant un exemplaire — tableau de décision dans `BUG-027` (rapport de récolement, exemplaires inactifs et API OfeliaScan écartés, avec la raison)
- [x] **Faux positif confirmé** : le champ provenance **est** présent au formulaire
      d'exemplaire ; c'est la liste vide (0 provenance en base) qui trompait l'œil. L'aide du
      champ renvoie désormais vers Avancé → Provenances quand la liste est vide
- [x] Tests : couverts par `test_provenance.py` et les écrans existants

#### FEAT-069 — Affectation en masse depuis la page catalogue
- [x] Doc `docs/specs/FEAT-069-affectation-masse-catalogue.md`
- [x] Barre notices : menus Catégorie + Emplacement (« Ne pas modifier » par défaut, « — (vider) » explicite) + bouton Affecter
- [x] Barre exemplaires : menu Provenance + bouton Affecter (correction Val : chaque information au niveau où elle appartient)
- [x] 3 pages de confirmation d'affectation supprimées ; retour au catalogue **avec les filtres actifs** (`back_qs`) ; les suppressions gardent leur confirmation
- [x] Tests : `test_bulk_assign.py` réécrit (19 cas). **Piège attrapé** : `get(field) or _KEEP` confondait chaîne vide et absence → « vider » était impossible

#### FEAT-070 — Liste de langues gérée
- [x] Doc `docs/specs/FEAT-070-langues-gerees.md`
- [x] Modèle `Language` (code + nom traduit) + seed des 22 + migration `catalog/0016`
- [x] Langue des notices, filtre du catalogue, lot de scan et langues parlées branchés dessus (`choices` en **callable** : la liste est modifiable serveur allumé)
- [x] Tri alphabétique par libellé **traduit** — l'ordre suit donc la langue de l'interface
- [x] Normalisation des codes hérités en migration `catalog/0017` — vérifié sur la Box : `fr` passe de 205 à 305 notices, plus aucun `fre-fre`/`fre-eng`/`fre-jpn`
- [x] Écran Avancé → Langues (liste triée, compteur cliquable, suppression qui ne touche aucune notice) + `LanguageAdmin`
- [x] Tests : `test_languages.py` (32 cas)

#### FEAT-071 — Catégories officielles Ofelia
- [x] Doc `docs/specs/FEAT-071-categories-ofelia.md`
- [x] Seed des 20 catégories (code = cote), noms traduits ×4, construites par produit `_AGE_GROUPS × _DOC_KINDS`
- [x] Commande `migrate_categories` (`--dry-run`, idempotente) : retrait du préfixe de langue, fusion, remap des anciennes, jamais de suppression d'une catégorie non reclassée
- [x] **Coquille corrigée** : « Adolescents Fiction » → `ADO FIC` (la liste fournie disait `ADO DOC`, en doublon avec « Adolescents Documentaire »)
- [x] Appliqué : **Box** (32 notices déplacées, 16 anciennes supprimées, `TEST` laissée intacte) et **grand-saconnex** (11 catégories `FR …` fusionnées, **104 notices reclassées, 0 orpheline**) ; sanjuan (catalogue vide) alignée aussi
- [x] Tests : `test_categories_migration.py` (15 cas)

#### FEAT-072 — Gestion des familles (remplace les enfants)
- [x] Doc `docs/specs/FEAT-072-gestion-familles.md`
- [x] `MemberChild` → `MemberFamilyMember` (**renommage**, pas recréation) ; `age` → `birth_year` converti + `is_adult` — migration `members/0005`
- [x] Libellés « Enfants » → « Famille » (formulaire, fiche, page de suppression) ; champ « Adulte ou enfant », l'année de naissance n'est demandée que pour un enfant
- [x] Carte de membre : colonne « Famille » à droite (A4 + ruban), tronquée par « … » si la place manque
- [x] **Régression attrapée au rendu 300 dpi** : la colonne tronquait le nom sur la planche A4 (« Rakoto H… ») → le bloc texte se décale à gauche **uniquement** quand il y a une famille ; une carte sans famille garde le rendu du Sprint 27
- [x] Tests : 7 cas de carte famille + cas famille dans `test_languages_and_children.py`

#### 2e vague — vérifications
- [x] `pytest` : **620 passed** (553 → 620, +67, 0 régression)
- [x] `manage.py check` : 0 issue
- [x] Gate i18n : `translations_sprint28.py` étendu (**137 chaînes + 16 pluriels** × EN/ES/MG) → `i18n_check.py` = **0**
- [x] Guide utilisateur ×4 langues : page neuve `catalogue/langues`, section « Affecter en masse » qui remplace les 2 anciennes sous-sections, tableau des 20 catégories officielles, « Enfants » → « Famille » dans l'inscription, colonne Famille dans `usagers/carte` ; `mkdocs build --strict` OK
- [x] Déploiement **Box** (migrations + `migrate_categories` + guide), **grand-saconnex** et **sanjuan** sur Fez, guide en ligne, nœud de secours Avignon resynchronisé
- [x] Test fonctionnel Val **OK 2026-08-21**

### Retours de test Val (2026-08-21) — 3e itération

> « Tout le reste est ok (testé validé) ». Restent 4 points : les libellés
> anglais de la page notice, les 2 boutons de recherche, la double sélection,
> et la provenance en toutes lettres.

#### BUG-028 — Libellés de formulaire en anglais dans une interface française
- [x] Doc `docs/bugs/BUG-028-libelles-formulaires-anglais.md`
- [x] Cause : sans `labels` ni `verbose_name`, **Django fabrique** le libellé depuis le nom du
      champ Python (`publication_year` → « Publication year »). La chaîne n'existe nulle part
      dans le code → `makemessages` ne la voit pas, `i18n_check.py` non plus
- [x] **Ampleur bien plus large que signalé** : 25 champs, soit toute la fiche notice **et**
      tout le formulaire usager ; l'audit a débusqué 8 champs de plus (accounts, inventory, loans)
- [x] 41 `verbose_name=_()` posés sur les modèles (corrige aussi `/admin/` et les erreurs de
      validation) ; `tags` traité par `Meta.labels` (le label d'un M2M vient du `related_name`)
- [x] Migrations `catalog/0018`, `catalog/0019`, `members/0006`, `accounts/0002`,
      `inventory/0004`, `loans/0003` — métadonnées seules, aucune donnée touchée
- [x] **Garde-fou** `apps/core/tests/test_form_labels.py` : parcourt tous les `ModelForm` et
      échoue si un libellé n'est pas un objet de traduction *lazy*. Tester la **nature** de
      l'objet plutôt que les mots évite une liste blanche (« Code », « Notes », « Date »…) et
      attrape un oubli qui ressemblerait à du français
- [x] Tests : 5 cas

#### FEAT-073 — Catalogue : boutons de recherche, sélection étendue, provenance lisible
- [x] Doc `docs/specs/FEAT-073-catalogue-ui-selection.md`
- [x] Case « Chercher les exemplaires » → boutons **« Rechercher des notices »** et
      **« Rechercher des exemplaires »** ; celui du mode courant est mis en avant ; défaut
      inchangé (notices, sans filtre)
- [x] **Deux cases de sélection** : « les N résultats visibles » (page courante) et « les N
      résultats de la recherche » (toutes les pages, masquée s'il n'y a qu'une page). Cocher
      l'une décoche l'autre ; cocher une ligne annule la sélection étendue
- [x] `filtered_records()` / `filtered_items()` extraites de `record_list` + `_selected_pks()` :
      la sélection étendue reconstruit **la recherche**, filtres compris (`back_qs`)
- [x] Pages de confirmation : identifiants réinjectés en clair (ce qui est confirmé est ce qui
      sera supprimé) mais **affichage plafonné** à 100 lignes + « … et N autres non affichés »
- [x] Provenance en toutes lettres (filtre, colonnes, menus d'affectation, confirmations)
- [x] Tests : 19 cas (`test_catalog_selection.py`)

#### 3e vague — vérifications
- [x] `pytest` : **643 passed** (620 → 643) ; `manage.py check` : 0 issue
- [x] Gate i18n : `translations_sprint28.py` étendu (**174 chaînes + 20 pluriels** × EN/ES/MG) → **0**
- [x] Guide utilisateur ×4 langues : `catalogue/recherche` (les 2 boutons) et
      `catalogue/operations-lot` (les 2 cases de sélection) ; `mkdocs build --strict` OK
- [x] Déploiement Box + grand-saconnex + sanjuan + guide en ligne + secours Avignon
- [x] Smoke tests : fiche notice en français, 2 boutons présents, ancienne case absente,
      cases de sélection, provenance complète — sur la Box et les 2 instances
- [x] Test fonctionnel Val **OK 2026-08-21**
- [x] Commit unique groupé + push origin/main

#### Retours Val (2026-08-21) — ajustements
- [x] **Provenance** : `__str__` renvoie le nom complet seul (`label or code`) — répéter le
      code devant n'allongeait que les menus et les colonnes
- [x] **Boutons de mode** groupés dans `.search-modes` : ils restent côte à côte même quand la
      barre de filtres passe à la ligne (et pleine largeur sur mobile)
- [x] **Couleurs** : bordeaux (mode courant) / olive (l'autre) — deux fonds pleins de la
      charte, plus de bouton blanc qui se fond dans la page
- [x] **Question « faut-il un tour complet du site ? »** → tour fait automatiquement :
      `test_i18n_coverage.py` couvre les 3 angles morts restants (texte en dur dans les
      templates, `messages`/`ValidationError`/`help_text` sans `_()`, `choices` et
      `verbose_name` de Meta). Résultat : **3 vrais oublis corrigés** (les 4 rôles utilisateur
      + `Setting.Meta`), 3 chaînes de `500.html` **justifiées** (handler500 n'a ni context
      processor ni middleware de langue, textes en 4 langues en dur, déjà documenté)
- [x] `pytest` : **648 passed** ; gate i18n (**180 chaînes + 20 pluriels**) → 0
- [x] Test fonctionnel Val **OK 2026-08-21**

### Clôture Sprint 28
- [x] **Test fonctionnel Val OK 2026-08-21** — les 4 vagues validées (« c'est ok pour ces
      3 points et pour le reste »)
- [x] `pytest` : **648 passed** (444 au commit `cddb518` → 648, +204, 0 régression)
- [x] `manage.py check` : 0 issue
- [x] Gate i18n : `scripts/translations_sprint28.py` (**180 chaînes + 20 formes plurielles**
      × EN/ES/MG) → `i18n_check.py` = **0**
- [x] **3 garde-fous i18n ajoutés ce sprint** : `i18n_check.py` audite désormais les pluriels
      (15 `{% blocktrans count %}` sortaient en français, dont 7 antérieurs) ;
      `test_form_labels.py` vérifie que les libellés sont extractibles ;
      `test_i18n_coverage.py` couvre les 3 angles morts restants
- [x] Guide utilisateur ×4 langues : 3 pages neuves (`catalogue/provenances`,
      `catalogue/categories`, `catalogue/langues`) + 6 pages enrichies
- [x] SPEC §5.2, §6.1, §6.2, §6.7, §6.9, §6.12 + en-tête
- [x] Commit unique groupé + push origin/main
- [x] Déploiement final : Box, grand-saconnex, sanjuan, `docs.bibliofelia.org`, secours Avignon

### Reste ouvert (hors Sprint 28)
- [ ] Sprint 26 — 4 « Test fonctionnel Val » jamais confirmés explicitement (BUG-025 import
      Excel sans ISBN, BUG-026 commentaires multi-lignes, FEAT-061 guide sur smartphone). Le
      code est déployé et committé (`cddb518`) depuis le 2026-08-18 : il ne manque que la
      confirmation
- [ ] Catégorie `TEST` restée sur la Box : `migrate_categories` ne supprime jamais une
      catégorie qu'elle n'a pas su reclasser. À retirer à la main si elle ne sert plus.
      **Vérifiée le 2026-08-22** : toujours là (pk=17), **0 notice rattachée** — donc
      supprimable sans risque, mais c'est une donnée de production : sur demande de Val

## Sprint 29 — Nettoyage du chemin d'impression

### FEAT-074 — Suppression du chemin CUPS

Constat Val (2026-08-22) : le bouton « Imprimer (CUPS) » de l'écran **Étiquettes
codes Ofelia** renvoie une page **« Interdit (403) — La vérification CSRF a
échoué »**. Diagnostic : POST forcé (`formmethod="post"`) sur un formulaire
`method="get"` sans `{% csrf_token %}` → le bouton n'a jamais fonctionné. Sur le
fond, CUPS suppose une imprimante visible depuis le serveur, alors que
l'étiqueteuse est sur le poste du bibliothécaire et le site hébergé hors de la
bibliothèque. **Décision Val : tout supprimer.**

- [x] `templates/printing/labels_picker.html` — bouton « Imprimer (CUPS) » retiré
- [x] `apps/printing/views.py` — vue `labels_send()` retirée
- [x] `apps/printing/urls.py` — route `printing:labels_send` retirée
- [x] `apps/printing/services.py` — `submit_to_cups()`, `PrintResult`, import
      `dataclass` et mention CUPS du docstring retirés
- [x] `config/settings/base.py` + `.env.example` — réglages `CUPS_HOST` / `CUPS_PORT` retirés
- [x] `Dockerfile` — `libcups2`, `libcups2-dev`, `pip install pycups==2.0.4` retirés
      (`gcc` conservé : peut servir à d'autres roues sans binaire ARM)
- [x] `requirements.txt` — commentaire pycups retiré
- [x] `templates/core/advanced.html` — description de l'écran d'étiquettes
      réécrite (« … ou ruban 62 mm pour l'étiqueteuse Brother QL »)
- [x] Wizard : étape « Imprimante » (CUPS uniquement) retirée → **8 étapes → 7**,
      formulaires et clés de session renumérotés, `Setting.printer_config` plus écrit
- [x] `docs/specs/FEAT-074-suppression-cups.md` créé
- [x] SPEC §2.1, §3.1, §6.7, §11.3, §12 + en-tête mis à jour (plus aucune mention
      CUPS hors historique FEAT-074)
- [x] Gate i18n : `makemessages -a --no-obsolete` (joué dans un conteneur sur Fez, Docker
      absent en local) + `scripts/translations_sprint29.py` (1 chaîne × EN/ES/MG) →
      `i18n_check.py` = **0**. Les chaînes CUPS supprimées sortent des `.po` via `--no-obsolete`
- [x] `pytest` sur Fez (image `--target dev`) : **648 passed**, 0 régression ;
      `manage.py check` : 0 issue
- [x] Déploiement : image `ofelia/bibliofelia:avignon` rebâtie sur Fez, instances
      `sanjuan` et `grand-saconnex` recréées (healthy) ; source synchronisée et image
      rebâtie sur le secours **Avignon**. Route `printing:labels_send` vérifiée absente,
      traductions EN/ES/MG vérifiées compilées dans l'image
- [x] **Test fonctionnel Val OK 2026-08-22** — écran Étiquettes : bouton CUPS
      disparu, « Générer PDF » / « Ruban 62 mm » / « Étiquettes de tranche » OK
- [x] Commit unique groupé + push origin/main → commit `a85d8c2`

### FEAT-075 — Deux écrans d'étiquettes + libellé « PDF A4 » + cote condensée

Demande Val (2026-08-22) : séparer les deux sortes d'étiquettes en deux pages et
deux entrées de menu (même fonctionnement général, même code de base), renommer
« Générer PDF » en « PDF A4 », et rendre la cote de tranche **35 % plus étroite
à hauteur constante** pour qu'elle tienne sur les tranches minces.

- [x] `apps/printing/views.py` — `_picker_context()` extrait et partagé ;
      nouvelle vue `spine_labels_picker`
- [x] `apps/printing/urls.py` — route `spine-labels/` (`printing:spine_labels`)
- [x] `templates/printing/_picker_base.html` — gabarit commun (filtres, table,
      « tout cocher », `?catalog_session=N`)
- [x] `templates/printing/labels_picker.html` — n'override que ses boutons ;
      « Générer PDF » → « **PDF A4** » ; le bouton de tranche part sur son écran
- [x] `templates/printing/spine_labels_picker.html` — bouton ruban seul,
      colonnes **Catégorie** / **Cote imprimée**, encadré d'explication quand
      l'impression ruban est désactivée
- [x] `templates/printing/cards_picker.html` — « Générer PDF » → « PDF A4 »
      aussi, pour que le bouton ne porte pas deux noms selon l'écran
- [x] `templates/core/advanced.html` — entrée « Étiquettes de tranche » dans le
      chapitre Impression
- [x] `apps/printing/services.py` — `SPINE_WIDTH_SCALE = 0.60` + `scale(0.60, 1)`
      autour du tracé, dans `_draw_spine_text()` partagé ruban / A4.
      **Deux corrections successives** : (1) la 1re version élargissait la zone
      de calcul, donc grossissait la police au lieu de condenser — contraire à
      la demande ; (2) Val a relevé le même symptôme après essai et porté la
      consigne de 35 % à **40 %**. Mesures finales : `RO FI ADO` 41,9 mm →
      **25,1 mm** de large, capitale inchangée à 11,3 mm (police 44,5 pt, la
      même qu'avant FEAT-075). Garde-fou :
      `test_font_size_is_computed_on_the_real_width_not_a_widened_one` relit la
      taille de police dans le flux PDF
- [x] **Planche A4 de cotes** (demande Val du 2026-08-22, absente de la 1re
      version) : `render_spine_labels_pdf()`, vue `spine_labels_pdf`, route
      `spine-labels.pdf`, bouton « PDF A4 » sur l'écran des cotes. Même grille
      que les étiquettes code Ofelia (`item_label_format`, 21 par page)
- [x] **Cote A4 réduite à 70 %** (`SPINE_A4_SIZE_SCALE`, retour Val du
      2026-08-22) : la cellule A4 (70 × 42 mm) étant plus grande qu'une étiquette
      de ruban, la cote la remplissait démesurément. Hauteur et largeur réduites
      de 30 %, découpage en lignes inchangé. `RO FI ADO` : 31,0 × 14,0 mm →
      **21,7 × 9,8 mm**. Le ruban garde sa taille pleine
      (`test_roll_label_keeps_its_full_size`)
- [x] Redirections d'erreur de `spine_labels_roll_pdf` → `printing:spine_labels`
- [x] `docs/specs/FEAT-075-ecrans-etiquettes-separes.md`

### FEAT-076 — Chapitre « Méta-données » dans le menu Avancé

- [x] `templates/core/advanced.html` — nouveau chapitre (bleu `--sky`, icône
      `database`) entre Inventaire et Administration : emplacements, langues,
      catégories, provenances, enrichissement. L'Inventaire ne garde que les
      sessions de travail
- [x] `docs/specs/FEAT-076-menu-metadonnees.md`

### Vérifications 2e vague

- [x] `pytest` sur Fez : **662 passed** (648 → 662, +14 tests d'étiquettes)
- [x] Gate i18n : 8 chaînes neuves × EN/ES/MG (dont l'encadré « ruban désactivé » réécrit) dans
      `scripts/translations_sprint29.py` → `i18n_check.py` = **0**
- [x] SPEC §6.7 (deux écrans, cote condensée), §10.1 (menu) + en-tête

### FEAT-077 — Logo compact + horloge de la Box

Demande Val (2026-08-22) : logo de la topbar plus petit, et date/heure à droite
du « Bonjour » sur l'accueil — **la Box perd son horloge quand on l'éteint**
(pas de pile RTC), les bibliothécaires doivent pouvoir s'en apercevoir.

- [x] `static/img/ofelia-logo-small.png` (emblème seul, 726 × 688) + `base.html`
      → ~30 px de large au lieu de ~104. `ofelia-logo.png` conservé (impressions)
- [x] `templates/core/dashboard.html` — hero en deux blocs, heure + date à
      droite, script de rafraîchissement (15 s) **basé sur l'horodatage serveur**
- [x] `static/css/ofelia.css` — `.hero` en flex, `.hero-clock` (tabular-nums)
- [x] **`TIME_ZONE` lu dans `TZ`** (défaut UTC inchangé) : sans ça, une Box à
      Madagascar aurait affiché 3 h de moins que la pendule et aurait paru
      déréglée en permanence — l'inverse du but recherché
- [x] **Réglage du fuseau dans Avancé → Paramètres** (demande Val du 2026-08-22) :
      `TimezoneForm` (liste IANA + « Fuseau du système »), section `timezone` dans
      le registre `FORMS`, `TimezoneMiddleware` qui l'active à chaque requête.
      Deux niveaux : `TZ` de l'instance = défaut, réglage Paramètres = surcharge
- [x] **Libellés de la liste enrichis** (retour Val du 2026-08-22, il cherchait
      le fuseau de Canaima) : « Europe/Zurich — CEST (UTC+2) », « America/Caracas
      (UTC-4) ». Coût mesuré dans le conteneur : ~220 ms au 1er rendu, ~40 ms
      ensuite → pas de cache
- [x] **Abréviation du fuseau** affichée à côté de l'heure. Sigle IANA quand il
      existe (`CEST`, `IST`), **nom de la ville** sinon (`Caracas`, `San Juan`) :
      la base a retiré les sigles littéraux d'Amérique du Sud et un « -04 »
      n'apprend rien au bibliothécaire (retour Val 2026-08-22)
- [x] **BUG corrigé** : le sigle disparaissait au bout de 15 s — le script
      écrasait tout le bloc heure via `textContent`. L'heure a désormais son
      propre span `.hero-clock-hm` ; un test interdit de viser à nouveau
      `.hero-clock-time`
- [x] `apps/core/timeutils.py` — `abbreviation()` / `utc_offset()` / `city()` /
      `zone_label()` partagés entre l'accueil et les Paramètres
- [x] `TZ` posée hors dépôt : `America/Argentina/San_Juan` (sanjuan),
      `Europe/Zurich` (grand-saconnex), `Europe/Zurich` sur la Box (lu de
      `timedatectl`, donc « la TZ de la Box »)
- [x] `apps/core/tests/test_dashboard_clock.py` — 10 tests, dont un qui interdit
      `new Date()` sans argument dans le script (l'horloge du poste masquerait
      celle de la Box), la surcharge du réglage, le repli sur le système et le
      fuseau inconnu non fatal
- [x] `docs/specs/FEAT-077-logo-compact-horloge-box.md`
- [x] `pytest` : **678 passed** ; gate i18n = 0
- [x] Déploiement : Fez (`sanjuan`, `grand-saconnex`), secours Avignon, **et la
      Box** — remise à jour le 2026-08-22 (`git pull` → `a85d8c2` + copie des
      FEAT-075/076/077 non committés, rebuild `bibliofelia` + `bibliofelia-worker`,
      0 migration en attente, healthy)
- [!] `/opt/edubox/docker-compose.yml` (projet **keebee**) modifié sur la Box pour
      y ajouter `TZ: ${TZ:-UTC}` sur les deux services. **À reporter dans
      `C:\WORK\keebee\docker-compose.yml`**, sinon le prochain déploiement keebee
      l'efface. Sauvegarde sur la Box : `docker-compose.yml.bak-tz`
- [x] Déploiement Fez (`sanjuan`, `grand-saconnex`, healthy) + secours Avignon
      (source synchronisée + image rebâtie)
- [x] ~~Box non mise à jour~~ — **rattrapé le 2026-08-22** : elle était
      injoignable pendant la 1re vague puis en panne au début de la 2e ; remise
      en ligne par Val en fin de session, elle a reçu `a85d8c2` + FEAT-075/076/077
      (rebuild `bibliofelia` + `bibliofelia-worker`, 0 migration en attente, healthy)
- [x] **Test fonctionnel Val OK 2026-08-22**, en quatre temps : étiquettes
      (« c'est bon »), logo (« validé »), heure sur la Box (« ok validé »), puis
      fuseaux et libellés (« c'est ok comme ça »)
- [x] Commit unique groupé + push origin/main

## Sprint 30 — Export Excel du catalogue + mise à jour d'exemplaires

Demande Val (2026-08-23), depuis `https://grand-saconnex.bibliofelia.org/fr/catalog/excel-catalog/` :
deux fenêtres de plus sur l'écran Catalogage Excel — un **export** de toute la
base avec les champs supportés par l'import, et une **mise à jour d'exemplaires**
qui ne crée rien, clée sur le code Ofelia et/ou le code externe.

### FEAT-078 — Export Excel de tout le catalogue

- [x] `apps/catalog/excel_export.py` — `EXPORT_COLUMNS` (16 colonnes),
      `items_queryset()`, `export_row()`, `build_catalog_workbook()`
- [x] Vue `catalog:excel_catalog_export` + route + carte
      `templates/catalog/excel_catalog/_export_form.html`
- [x] **Une ligne par exemplaire** (l'emplacement, l'état, la provenance et le
      code externe appartiennent à l'exemplaire, pas à la fiche) ; tri titre puis
      code interne ; en-têtes gras, `freeze_panes`, largeurs de colonne posées
- [x] **Export synchrone**, pas un job : aucun appel réseau, c'est une lecture de
      base. `openpyxl` en `write_only` + `.iterator(chunk_size=500)` pour ne pas
      faire tenir deux fois le catalogue en RAM sur une Box à 4 Go
- [x] Colonnes = **exactement** celles que l'import/la mise à jour savent relire,
      plus `OFELIA_CODE` et `INTERNAL_ID` → le fichier se renvoie tel quel
- [x] `apps/catalog/tests/test_excel_export.py` — 8 tests
- [x] `docs/specs/FEAT-078-export-excel-catalogue.md`

### FEAT-079 — Mise à jour d'exemplaires depuis Excel

- [x] `ExcelJobMode.UPDATE` + `ExcelCatalogJob.updated` / `.unchanged` → migration
      `catalog/0020_excel_update_mode` (`makemigrations --check` = *No changes detected*)
- [x] `run_update_job()`, `_apply_item_update()`, `_find_item_by_ofelia_code()`,
      `UPDATE_KEY_COLUMNS` / `UPDATE_OVERRIDE_COLUMNS`, alias d'en-tête FR
- [x] `validate_xlsx` : branche UPDATE — au moins une colonne clé (alias compris),
      sinon upload refusé **sans créer de job**
- [x] Vue `catalog:excel_catalog_update` + carte `_update_form.html` + branches
      `mode == "update"` de `detail.html` (compteurs, bandeau rouge, colonne
      « Exemplaire » au lieu d'« ISBN », explications des 6 nouveaux avertissements)
- [x] **Ne crée jamais rien** — vérifié par comptage notices + exemplaires dans
      les tests. Seule création héritée de l'import : les tags absents
- [x] **Code Ofelia prioritaire** : les deux codes présents → le code Ofelia
      identifie l'exemplaire et le code externe de la ligne **lui est appliqué**
      (règle Val). Un code Ofelia inconnu **ne retombe pas** sur le code externe
- [x] `LOCATION` et `ISBN` deviennent modifiables (en import, clé et création
      seulement). `ISBN_CONFLICT` garde-fou sur l'unicité d'`isbn_13` — sans lui la
      ligne aurait fait tomber le lot entier
- [x] Robustesse : **une transaction par ligne** (`ROW_ERROR` → les autres passent),
      référentiels chargés une fois, sauvegarde partielle toutes les 10 lignes
- [x] `apps/catalog/tests/test_excel_update.py` — 35 tests, dont l'aller-retour
      export → mise à jour « 0 modification, 0 erreur » et un garde-fou de
      cohérence colonnes d'export ⊆ colonnes relisables
- [x] `docs/specs/FEAT-079-mise-a-jour-exemplaires-excel.md`

### Corollaire — résolutions insensibles à la langue

L'export écrit `TYPE`, `CONDITION` et `CATEGORY` dans la langue du
bibliothécaire, alors que le job de relecture tourne dans le **worker
django-q2, en français**. Sans ces trois helpers, un fichier exporté en espagnol
serait revenu avec `TYPE_UNKNOWN` + `CATEGORY_UNKNOWN` sur **chaque** ligne —
l'aller-retour n'aurait marché qu'en français.

- [x] `_translated_label_aliases()` — libellés `DocumentType` / `ItemState` de
      toutes les langues de l'instance (vérifié en conteneur : `Livre` /
      `Comic / manga` / `Cómic / manga` / `Tantara an-tsary / manga` → `comic`)
- [x] `_resolve_category()` — tous les champs `name_<lang>` de modeltranslation,
      puis à défaut par **code** de catégorie
- [x] `_get_or_create_tag()` — recherche multi-langue avant création, sinon chaque
      tag serait recréé en double avec le libellé espagnol dans le champ français
- [x] Ces trois helpers servent **aussi à l'import**, strictement plus permissifs
      qu'avant → aucune régression

### Qualité

- [x] `pytest` sur Fez (image `--target dev`) : **721 passed** (678 → 721, +43),
      0 régression
- [x] `makemigrations --check --dry-run` : *No changes detected*
- [x] Gate i18n : `makemessages -a --no-obsolete` (conteneur Fez) +
      `scripts/translations_sprint30.py` (24 chaînes + 2 pluriels × EN/ES/MG) →
      `python scripts/i18n_check.py` = **0**
- [x] `compilemessages` OK, tests rejoués **avec les `.mo` compilés**
      (43 passed) — c'est ce qui prouve la relecture multi-langue
- [x] Correctif au passage : `{% icon "alert-triangle" %}` → `"triangle-alert"`
      dans `detail.html` (le fichier `static/icons/alert-triangle.svg` n'existe
      pas, l'icône des deux bandeaux ne s'affichait pas)

### FEAT-080 — Identification complète au prêt et au retour

Né du test physique du code externe `BCF132770013` : avec deux codes possibles
par exemplaire, le comptoir n'affichait qu'un titre et le code interne `OFL-…`
— celui qui n'est imprimé sur aucune étiquette. Et au retour, la personne
debout en face du bibliothécaire n'était nommée nulle part.

- [x] **Panier de prêt** : titre + auteur(s) + **code Ofelia** + **code externe**,
      les deux affichés quel que soit celui qui a été scanné (pastilles
      `.code-chip`). `OFL-…` retiré de la ligne
- [x] **Journal de retour** : photo / nom / prénom / âge de la personne qui rend
      (cliquable vers sa fiche), titre + auteur(s), les deux codes, et une mention
      explicite « Retour effectué » / « … livre perdu réintégré » / « Aucun
      prêt actif ». Message flash nominatif
- [x] `ReturnResult.loan` — sans le prêt soldé, la vue ne peut plus nommer
      l'emprunteur ; pour le livre perdu réintégré, le prêt est **lu avant**
      l'`update()` de masse qui le solde
- [x] `Member.age` — années **révolues** (anniversaire non passé décompté), `None`
      sans date de naissance. Aucune migration : propriété calculée
- [x] `prefetch_related("record__authors")` sur le panier et sur la résolution du
      retour (sinon une requête par livre scanné)
- [x] Journal en **session** : le gabarit tolère les entrées antérieures à
      FEAT-080, qui n'ont pas les nouvelles clés (test dédié)
- [!] **Sexe non affiché** : `Member` n'a pas ce champ (seul
      `MemberFamilyMember.gender` existe, FEAT-072, et ces personnes n'empruntent
      pas). L'ajouter = migration + donnée personnelle de plus → **décision Val**
- [x] **Correctif de gabarit** : trois commentaires `{# … #}` étaient à cheval sur
      deux lignes. Vérifié en conteneur — le lexer Django n'active pas `DOTALL`,
      un tel commentaire s'affiche **en clair dans la page**. Repassés en
      `{% comment %}`, avec un test qui interdit `FEAT-080` ou `{#` dans le HTML rendu
- [x] `apps/loans/tests/test_lend_return_display.py` — 13 tests
- [x] `docs/specs/FEAT-080-identification-pret-retour.md` + SPEC §6.3
- [x] `pytest` : **734 passed** (721 → 734, +13) ; gate i18n = 0 (32 chaînes +
      3 pluriels × EN/ES/MG)
- [x] Déployé sur Fez (`sanjuan`, `grand-saconnex`, healthy) ; les deux écrans
      rendus en 200, sans commentaire cassé

### FEAT-081 — Ancienne carte d'usager reconnue partout

Signalé par Val : sa carte `2910000000017` n'était pas reconnue depuis l'accueil
ni la liste des usagers. **Enquête** sur `grand-saconnex` (un seul usager) :

| Fait | Valeur |
|---|---|
| Carte courante | `2919000000003` |
| Ancienne carte | `2910000000017` — celle qui était scannée |
| Inscription | 2026-08-18 |
| Remplacement | **2026-08-20 à 14:02 UTC** (16:02 CEST) |

`Setting.next_replacement_card_seq` est passé de `900 000 000` à `900 000 001`
à cet horodatage → `replace_card()` a tourné **une fois**, le 20 août.
`2910000000017` = numéro auto à la création (`build_ean13("291", pk=1)`),
`2919000000003` = 1re carte de remplacement. Seul chemin d'appel : le bouton
« Remplacer la carte » de la fiche usager (POST + `confirm()`).

- [x] `apps/members/lookup.py` — `find_member` (carte courante **puis** ancienne,
      saisie normalisée) et `is_replaced_card`. Pendant de `find_item`
- [x] Les **trois** écrans passent par le même résolveur : accueil
      (`core:search`), liste des usagers (`+ replaces_card_number__icontains`),
      prêt (doublon inline supprimé). Avant : le prêt seul acceptait l'ancienne
- [x] **Avertissement** « Carte remplacée » quand la résolution passe par
      l'ancienne carte — une carte périmée ne doit pas marcher en silence
- [x] **Rappel de réimpression** après `replace_card` : le numéro change en base,
      la carte en poche porte encore l'ancien. C'est exactement ce qui a produit
      ce ticket
- [x] `apps/core/views.py` n'importait ni `messages` ni `gettext` — ajoutés
- [x] `apps/members/tests/test_card_lookup.py` — 13 tests, dont la priorité du
      porteur actuel et les trois écrans qui répondent pareil
- [x] `docs/specs/FEAT-081-ancienne-carte-usager.md` + SPEC §6.2
- [x] `pytest` : **747 passed** (734 → 747, +13) ; gate i18n = 0
- [x] Déployé Fez ; résolution vérifiée en direct sur `grand-saconnex`
- [!] **Bouton « Remplacer la carte » non touché** : voisin de « Renouveler la
      carte », deux boutons fantômes identiques dont l'un prolonge la validité et
      l'autre invalide le numéro ; son `confirm()` se valide sans lire. Candidat
      à durcissement (libellé, message nommant le numéro désactivé) → **décision Val**

### Étiquette de test du code externe (hors dépôt)

- [x] `BCF132770013` vérifié présent sur `OFL-20260803-0064` (grand-saconnex) et
      résolu par `find_item` sous toutes ses formes (casse, tirets, espaces)
- [x] PDF **62 × 35 mm** (Code128) + planche A4 (Code128 + Code39) générés par un
      script jetable : BibliOfelia ne sait produire que des EAN13, or un code
      externe est alphanumérique. Fichiers dans `C:\WORK\BibliOfelia\_test-etiquettes\`
- [x] Pas de décodeur (zbar) disponible → vérification **géométrique** :
      145 modules = 12×11+13 (structure Code128 exacte), écart à un multiple entier
      de module **0 µm**, zones de silence ≈ 3 mm, barre fine 0,339 mm
- [x] **Correctif au passage** : le pas demandé (0,33 mm) tombait sur 7,795 px à
      600 dpi et python-barcode arrondissait chaque barre séparément (7 ou 8 px)
      → code-barres à pas irrégulier. Pas aligné sur un pixel entier

### Reste à faire

- [x] ~~Guide utilisateur `catalogage-excel*.md` à faire~~ — **fait dans la même
      session** : les deux nouvelles fenêtres documentées en FR + EN + ES + MG, et le
      conteneur `bibliofelia-docs` rebâti. Vérifié sur le **contenu servi**, pas sur le
      succès du build (`grep OFELIA_CODE_UNKNOWN` dans l'`index.html` publié)
- [ ] Guide utilisateur : écrans **prêt et retour** (FEAT-080/081). Les pages
      `prets-retours/*` décrivent des écrans qui ont changé d'aspect (panier avec les
      deux codes, journal de retour avec la fiche de l'usager) et les **captures sont
      donc périmées**. À reprendre en FR + EN + ES + MG. *Motif du report : arrivé en
      fin de session, après la validation de Val*
- [x] Déploiement complet : Fez (`sanjuan`, `grand-saconnex`), secours **Avignon**
      (source + image à jour de FEAT-081) et **la Box**
- [x] **Test fonctionnel Val — OK 2026-08-23**, en trois temps : « ok ca fonctionne »
      (FEAT-078/079), « le code barre externe fonctionne » (FEAT-080 + étiquette
      Code128), « ok tout fonctionne » (FEAT-081)
- [x] Commit unique groupé + push origin/main

### Audit demandé par Val — « code externe accepté partout où le code Ofelia l'est »

Demande du 2026-08-23, en marge du sprint. Résultat :

- [x] **Saisie clavier / douchette USB : conforme partout.** Tous les points
      d'entrée passent par `apps/catalog/lookup.py::find_item` (code Ofelia
      d'abord, puis code externe) : recherche de l'accueil (`core:global_search`),
      recherche du catalogue (`filtered_records`, notices **et** exemplaires),
      prêt (`loans:lend` → `add_item`), retour (`_process_return`), récolement web
      (`inventory:add_scan` → `record_scan`), récolement API OfeliaScan
      (`/api/v1/inventory/…/items`). La douchette USB (`scan-wedge.js`) n'applique
      aucun filtre de forme → elle transmet n'importe quel code au serveur
- [!] **Scan caméra : le code externe est rejeté.** `static/js/scan-camera.js`
      n'accepte qu'un **EAN-13 à clé valide et préfixe 290/291/978/979** (+977 en
      catalogage). Un code externe est donc refusé dans deux cas : (a) c'est un
      EAN-13 d'un autre préfixe, (b) c'est un Code39/Code128/Codabar — très
      courant sur les étiquettes de bibliothèque — or les deux moteurs sont
      configurés **EAN-13 uniquement** (`Html5QrcodeSupportedFormats.EAN_13`,
      Quagga `ean_reader`). **Décision Val requise**, cf. ci-dessous
- [ ] (a) Ouvrir le filtre de préfixe à tout EAN-13 à clé valide — petit
      changement, garde-fous checksum + consensus conservés, léger risque de
      lecture parasite d'un code-barres produit voisin
- [ ] (b) Activer les lecteurs Code39/Code128 — couvre le gros des étiquettes de
      bibliothèque, mais décodage plus lent et Code39 sans somme de contrôle →
      plus de fausses lectures. À ne faire que si Val le demande
