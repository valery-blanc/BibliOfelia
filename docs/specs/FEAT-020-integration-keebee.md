# FEAT-020 — Intégration keebee (déploiement sur la Ofelia Box)

Statut : **EN COURS** (2026-05-22)
Sprint : 6
Task : #18 de `docs/tasks/TASKS.md` — débloque aussi Task #16 et #19 (tests Pi)
Spec : `SPEC_BIBLIOFELIA.md` §4 (Architecture), §11 (Déploiement)

## Contexte

BibliOfelia doit tourner sur la Ofelia Box (Raspberry Pi 5) en cohabitation
avec EduBox/keebee. keebee installe ses applications via un **wizard web**
(`setup/app.py`, `setup/templates/index.html`) : l'utilisateur coche les
logiciels voulus, puis le wizard fait `docker compose build && up` sur les
services correspondants. Ajouter une application à la Box revient donc à
**éditer le dépôt keebee** : entrée dans le wizard, services dans son
`docker-compose.yml`, route nginx, tuile du portail.

Choix retenu (validé Val 2026-05-22) : keebee **clone le dépôt GitHub
BibliOfelia** au moment de l'installation et **build l'image sur la Pi** —
même mécanisme que Digistorm. Pas de registry, pas de buildx multi-arch ;
internet n'est requis que pendant l'installation.

## Décisions d'intégration

| Point | Constat | Décision |
|---|---|---|
| Réseau Docker | BibliOfelia prod = `ofelia-net` ; keebee = `edubox-net` | Les services rejoignent `edubox-net` |
| `SECRET_KEY` | prod accepte `SECRET_KEY_FILE` *ou* `SECRET_KEY` ; keebee gère tout par `.env` | Wizard génère `BIBLIOFELIA_SECRET_KEY` dans `.env`, passé en variable `SECRET_KEY` (pas de docker secret) |
| Fichiers statiques | `prod.py` = `ManifestStaticFilesStorage`, conçu pour être servi par nginx | nginx sert `/bibliofelia/static/` et `/bibliofelia/media/` via `alias` sur volumes partagés en lecture seule |
| Collecte statique | Faite au build dans le `Dockerfile` → volume figé après rebuild | `collectstatic` déplacé dans `entrypoint.sh` (runtime) → volume toujours à jour |
| Cookies sécurisés | `prod.py` force `SESSION_COOKIE_SECURE=True` + HSTS ; or l'accès via le point d'accès WiFi de la Box est **HTTP** (443 bloqué sur `wlan0`) | Réglage `SECURE_COOKIES` (défaut `True`) ; mis à `False` pour la Box → connexion possible en HTTP comme en HTTPS |
| `ALLOWED_HOSTS` / CSRF | IP de la Box variable (DHCP), multiples noms (`.local`, AP, ZeroTier) | `ALLOWED_HOSTS=*` ; pas de `CSRF_TRUSTED_ORIGINS` (les POST sont same-origin → acceptés via `X-Forwarded-Proto` + `SECURE_PROXY_SSL_HEADER`) |
| Container backup | `bibliofelia-backup` monte `/mnt/usb-backup` (absent sur la Pi) | Non déployé — le worker django-q2 fait déjà la sauvegarde horaire (FEAT-014) |
| mDNS (Task #19) | `generate_avahi_service` écrit `/etc/avahi/services/bibliofelia.service` | Bind-mount hôte `/etc/avahi/services/` rw dans le conteneur web ; `avahi-daemon` installé par `bootstrap.sh` |
| Healthcheck | `Dockerfile` teste `/api/v1/pairing/info` en direct sur le conteneur (port 8001, sans préfixe nginx) | Inchangé — vérifié correct : `FORCE_SCRIPT_NAME` n'affecte que le *reverse*, pas la résolution d'URL |

## Comportement

### Routage derrière nginx

L'application est servie sous `/bibliofelia/`. nginx **retire le préfixe**
(`proxy_pass http://bibliofelia:8001/;`) ; `FORCE_SCRIPT_NAME=/bibliofelia`
fait que Django reconstruit tous les liens et redirections avec le préfixe.

- `/bibliofelia/` → conteneur web (UI + API REST)
- `/bibliofelia/static/` → `alias` nginx sur le volume `staticfiles`
- `/bibliofelia/media/` → `alias` nginx sur le volume `media`

### Conteneurs

- `bibliofelia` (web) : Django + gunicorn, port interne 8001, `entrypoint.sh`
  (migrations + seed + `compilemessages` + `collectstatic`), healthcheck.
- `bibliofelia-worker` : `qcluster` django-q2 ; démarre **après** que `web`
  soit `healthy` (`depends_on: condition: service_healthy`) et **sans**
  `entrypoint.sh` (évite une course aux migrations sur SQLite).

## Spécification technique

### Côté BibliOfelia (ce dépôt)

1. `config/settings/base.py` — nouveau réglage env `SECURE_COOKIES` (bool,
   défaut `True`).
2. `config/settings/prod.py` — `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`,
   HSTS pilotés par `SECURE_COOKIES`.
3. `scripts/entrypoint.sh` — ajout de `collectstatic --noinput`.
4. `docker-compose.yml` — référence prod self-contained corrigée (web +
   worker, réseau propre, plus de container backup ni de docker secret).

### Côté keebee (`C:\WORK\keebee`)

Documenté dans `keebee/docs/specs/FEAT-029-bibliofelia.md` :

- `setup/app.py` : entrée `bibliofelia` dans `APPS`, `_prepare_bibliofelia()`
  (git clone), `_create_dirs`, `_write_env` (`BIBLIOFELIA_SECRET_KEY`),
  `_report_health`, container map ; `bibliofelia-worker` ajouté aux services.
- `setup/templates/index.html` : carte à cocher BibliOfelia (badge Optionnel).
- `docker-compose.yml` : services `bibliofelia` + `bibliofelia-worker`.
- `nginx/conf.d/ofelia-locations.inc` : bloc `location /bibliofelia/`.
- `portal/index.html` : tuile BibliOfelia.
- `healthcheck/app.py` : entrée BibliOfelia.
- `bootstrap.sh` : `apt install avahi-daemon avahi-utils`.

## Impact sur l'existant

- Aucun changement de comportement en dev (`SECURE_COOKIES` défaut `True`,
  `docker-compose.dev.yml` inchangé).
- `collectstatic` au boot ajoute quelques secondes au démarrage du conteneur
  web — acceptable, garantit un statique frais après chaque mise à jour.
- Débloque Task #19 (bind-mount avahi) et Task #16 (lookup ISBN bout-en-bout
  testable sur la Pi).

## Test

- `pytest` dans Docker — non-régression (les réglages dev sont inchangés).
- Déploiement réel sur la Pi `192.168.0.147` : wizard keebee → coche
  BibliOfelia → build → accès `/bibliofelia/` → wizard de premier démarrage.
- Test Val : portail → tuile BibliOfelia → wizard → connexion bibliothécaire.
