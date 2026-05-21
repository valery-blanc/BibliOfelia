# TASKS — BibliOfelia v1

Source de vérité de l'avancement v1. Une case `[x]` = livrable terminé et déployable. `[ ]` = à faire. `[!]` = bloqué (voir note).

Mise à jour : 2026-05-21

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
  - [ ] Téléchargement Inter font + Lucide icons (esthétique uniquement, non bloquant)
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

- [ ] **Task #2** Modèles de données (§5)
- [ ] **Task #3** i18n + modeltranslation (4 langues)
- [ ] **Task #4** Auth, rôles, audit, throttling

## Sprint 2 — UI et workflows métier

- [ ] **Task #5** UI base (Pico/HTMX/Alpine, layout, recherche globale)
- [ ] **Task #6** Catalogage (§6.1)
- [ ] **Task #7** Gestion usagers (§6.2)
- [ ] **Task #8** Prêts/Retours/Renouvellements/Perdus (§6.3)
- [ ] **Task #9** Réservations (§6.4)
- [ ] **Task #10** Récolement (§6.5)

## Sprint 3 — Hors workflow principal

- [ ] **Task #11** Dashboard, rapports, paramètres (§6.6)
- [ ] **Task #12** Impression étiquettes + cartes (§6.7)
- [ ] **Task #13** Notifications offline + alertes (§6.8)
- [ ] **Task #14** Sauvegardes locales + cloud (§8)
- [ ] **Task #15** Wizard premier démarrage + données démo (§11.3-11.4)

## Sprint 4 — API et qualité

- [ ] **Task #16** API REST OfeliaScan v1 (§6.10)
- [ ] **Task #17** Tests (pytest-django, coverage 70%)

## Sprint 5 — Déploiement

- [ ] **Task #18** Intégration keebee : docker-compose + nginx /bibliofelia/
  - Cohabitation avec Koha (qui reste sur `/biblio/`)
  - Modifier C:\WORK\keebee/docker-compose.yml + conf nginx
  - Build multi-arch arm64+amd64
  - Documenter dans `keebee/docs/specs/specs_keebee.md`
