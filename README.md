# BibliOfelia

Logiciel de gestion de bibliothèque pour petites bibliothèques communautaires (≤ 3000 ouvrages), hors-ligne, déployé sur **Ofelia Box** (Raspberry Pi 5) du projet Ofelia.

Spec complète : [`docs/specs/SPEC_BIBLIOFELIA.md`](docs/specs/SPEC_BIBLIOFELIA.md)
Avancement : [`docs/tasks/TASKS.md`](docs/tasks/TASKS.md)

## Stack

Python 3.12 · Django 5.1 LTS · SQLite WAL + FTS5 · DRF + simplejwt · django-q2 · django-modeltranslation · django-auditlog · django-axes · HTMX 2.x · Alpine.js 3.x · Pico.css 2.x · ReportLab · python-barcode · pycups · httpx · gunicorn · Docker.

## Démarrage dev

```powershell
# 1. Copier .env.example -> .env (les valeurs par défaut conviennent en dev)
Copy-Item .env.example .env

# 2. Lancer la stack dev (Django runserver + worker django-q2)
docker compose -f docker-compose.dev.yml up --build

# 3. Migrer la base et créer un superadmin
docker compose -f docker-compose.dev.yml exec web python manage.py migrate
docker compose -f docker-compose.dev.yml exec web python manage.py createsuperuser
```

L'interface est disponible sur http://localhost:8001/.

### Assets statiques

Le squelette référence `pico.min.css`, `htmx.min.js`, `alpine.min.js` dans `static/` — à télécharger en local (aucun CDN, contrainte hors-ligne de la spec) :

- Pico.css 2.x : https://github.com/picocss/pico/releases (fichier `pico.min.css`)
- HTMX 2.x : https://unpkg.com/htmx.org@2/dist/htmx.min.js
- Alpine.js 3.x : https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js
- Inter font : https://github.com/rsms/inter
- Lucide icons : https://unpkg.com/lucide-static/icons/

Placés dans `static/css/` et `static/js/`.

## Structure

```
config/         settings (base/dev/prod/test), urls, wsgi
apps/
  core/         Setting, EAN13, dashboard, recherche globale
  accounts/     User étendu (rôles), login
  catalog/      Author, Category, Tag, Location, BibliographicRecord, Item  [Task #2]
  members/      MemberCategory, Member                                       [Task #2]
  loans/        Loan, InHouseConsultation, Reservation                       [Task #2/8/9]
  inventory/    Sessions de récolement                                       [Task #10]
  printing/     Étiquettes + cartes membres                                  [Task #12]
  reports/      Dashboard avancé + rapports PDF/CSV                          [Task #11]
  setup/        Wizard premier démarrage + middleware                        [Task #15]
  api/          DRF endpoints OfeliaScan                                     [Task #16]
  tasks/        Jobs django-q2                                               [Task #14]
scripts/        entrypoint.sh, backup.sh, restore.sh
templates/      base.html + templates par app
static/         css/js/icônes (à compléter, voir ci-dessus)
locale/         .po fr/en/es/mg                                              [Task #3]
docs/specs/     SPEC_BIBLIOFELIA.md (source de vérité)
docs/tasks/     TASKS.md (checklist v1)
docs/bugs/      BUG-XXX-*.md
```

## Déploiement keebee (Ofelia Box)

Voir Task #18 et `C:\WORK\keebee\CLAUDE.md`. Cohabitation avec Koha :
- Koha reste sur `/biblio/`
- BibliOfelia s'installe sur `/bibliofelia/`

Cf. variables `FORCE_SCRIPT_NAME`, `STATIC_URL`, `MEDIA_URL` dans `docker-compose.yml`.

## Conventions

- `black` + `isort` + `ruff` (cf. `pyproject.toml`)
- `pytest --cov=apps` (cible 70%)
- Workflow : `[code] → [docs] → [déploiement Pi] → [test user] → [commit]`. Pas de commit avant confirmation explicite (cf. `CLAUDE.md` keebee).
