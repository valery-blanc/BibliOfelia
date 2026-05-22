# FEAT-016 — API REST OfeliaScan (auth, appairage, lookup ISBN)

Statut : **DONE — tests écrits et exécutés (15 verts), en attente test fonctionnel Val** (2026-05-22)
Sprint : 3
Task : #16 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.10 — contrat figé par `SPEC-CORR-001-contrat-api-box.md`

## Contexte

L'application Android OfeliaScan (découverte mDNS + appairage + lookup ISBN) est
prête et attend une box conforme au contrat `SPEC-CORR-001`. Cette tâche
implémente côté BibliOfelia les endpoints d'authentification, d'appairage, de
diagnostic et de lookup ISBN. Si la box respecte le contrat à la lettre,
OfeliaScan n'a aucune modification à faire.

## Périmètre

### Endpoints (`apps/api/views.py` + `apps/api/urls.py`)

Tous montés sous `/api/v1/`, **sans slash final** (OfeliaScan concatène les
chemins relatifs à une base URL dont le slash final est significatif).

| Méthode + chemin        | Auth | Throttle | Rôle |
|-------------------------|------|----------|------|
| `POST /auth/login`      | non  | `auth`   | username/password → 4 champs OAuth |
| `POST /auth/refresh`    | non  | `auth`   | rotation du refresh token |
| `POST /auth/logout`     | oui  | `auth`   | liste noire des refresh tokens |
| `GET /pairing/info`     | non  | —        | découverte avant appairage |
| `GET /health`           | oui  | —        | diagnostic (`status` garanti) |
| `GET /isbn/{isbn}`      | oui  | `isbn`   | cache local puis fallback OpenLibrary |

### Authentification (`apps/api/serializers.py`)

SimpleJWT renvoie `{access, refresh}` par défaut ; le contrat exige les noms
OAuth 2.0. Deux serializers personnalisés règlent ça :

- `OAuthTokenObtainSerializer` — `/auth/login` : émet
  `{access_token, refresh_token, token_type: "Bearer", expires_in: <int s>}`.
- `OAuthTokenRefreshSerializer` — `/auth/refresh` : champ d'entrée
  `refresh_token` ; rejoue la rotation SimpleJWT (`ROTATE_REFRESH_TOKENS` +
  `BLACKLIST_AFTER_ROTATION`, déjà actifs dans `SIMPLE_JWT`) et renvoie les
  mêmes 4 champs, dont un **nouveau** `refresh_token`.

`/auth/logout` met sur liste noire tous les `OutstandingToken` de l'utilisateur
courant (app `rest_framework_simplejwt.token_blacklist`, déjà installée).

> Limite connue : un refresh token issu d'une rotation (`set_jti`) ne crée pas
> d'`OutstandingToken` ; `/auth/logout` ne le révoque donc pas individuellement.
> Comportement hérité de SimpleJWT, sans impact sur le parcours d'appairage.

### Lookup ISBN (`apps/api/views.py:IsbnLookupView`)

1. Normalisation de l'ISBN ; longueur ≠ 10/13 → `404`.
2. Recherche dans le catalogue local (`BibliographicRecord` par `isbn_13`
   puis `isbn_10`) → `source: "cache"`, `cached: true`.
3. Sinon fallback `apps.catalog.openlibrary.lookup_isbn` → `source: "openlibrary"`,
   `cached: false`.
4. Sinon `404` au format d'erreur uniforme.

Le champ est `publication_year` (entier ou `null`), `isbn` est toujours ré-émis.

### Diagnostic

`GET /health` renvoie `{status: "ok", version, disk_free_mb, last_backup_at}`.
`disk_free_mb` est calculé via `shutil.disk_usage` ; `last_backup_at` provient
du `Setting` du même nom (alimenté par Task #14, `null` tant que non défini).

### Format d'erreur

`apps/api/exceptions.py:api_exception_handler` (déjà en place) normalise toutes
les exceptions DRF en `{"error": {"code", "message", "details"}}`. Le `404`
ISBN est construit explicitement au même format.

## Réglages (`config/settings/base.py`)

- `BIBLIOFELIA_VERSION` (défaut `0.1.0-dev`) — exposé par `/pairing/info` et `/health`.
- `API_BASE_PATH` (défaut `/biblio/api/v1/`) — valeur renvoyée dans `api_base`.
  Le contrat OfeliaScan attend `/biblio/api/v1/` (slash final inclus).
- `box_name` / `library_name` sont lus depuis `Setting` (renseignés par le
  wizard de premier démarrage, Task #15) ; défauts `OfeliaBox` / `BibliOfelia`.

## Impact sur l'existant

- **Endpoint `/health` déplacé et sécurisé.** L'ancienne vue publique
  `apps.core.views.health` (routes `core:health` et `api:health` non
  authentifiées) est **supprimée**. Le contrat impose un `/health`
  authentifié → nouvelle `HealthView` DRF. `apps/core/views.py` et
  `apps/core/urls.py` nettoyés en conséquence.
- **Healthcheck Docker** repointé de `/api/v1/health/` vers `/api/v1/pairing/info`
  (public, touche la BD) puisque `/health` exige désormais un JWT.
- **`SetupRequiredMiddleware`** : `ALLOWED_PATHS` réduit à `{/static/, /media/}`
  (les anciennes entrées `/health/` n'ont plus de route).
- Aucun changement de modèle → aucune migration.

## Point ouvert — routage nginx (Task #18)

Le contrat fige `api_base = /biblio/api/v1/`, alors que la route nginx de
l'UI BibliOfelia est `/bibliofelia/` (`/biblio/` étant le Koha de keebee). La
cohabitation est possible : nginx fait du *longest-prefix match*, donc
`location /biblio/api/v1/ { proxy_pass bibliofelia; }` peut coexister avec
`location /biblio/ { proxy_pass koha; }`. `API_BASE_PATH` est configurable par
variable d'environnement pour absorber la décision finale au déploiement.

## Tests (`apps/api/tests/test_api.py`)

15 tests (DRF `APIClient`), tous verts : champs OAuth, mauvais identifiants,
rotation + liste noire du refresh token, logout, `/pairing/info` public,
`/health` protégé, lookup ISBN cache / fallback OpenLibrary (moqué) / 404.
`conftest.py` vide le cache entre tests pour réinitialiser les compteurs de
throttling. Suite complète : **132 passed**.
