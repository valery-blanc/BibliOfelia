# SPEC-CORR-001 — Correction du contrat API box (BibliOfelia §6.10)

Statut : **APPLIQUÉ** — intégré dans `SPEC_BIBLIOFELIA.md` §6.10 le 2026-05-22
Version : 1.0
Date : 2026-05-22
Cible : `C:\WORK\BibliOfelia\docs\specs\SPEC_BIBLIOFELIA.md` §6.10
  « Webservice OfeliaScan (API REST) »
Auteur : OfeliaScan (client de l'API)

---

## 0. Mode d'emploi

Ce document **ne modifie pas** la spec BibliOfelia. Il décrit les corrections
à y appliquer pour que `§6.10` devienne un **contrat exploitable** entre la box
et l'application Android OfeliaScan.

Chaque section ci-dessous est rédigée pour **remplacer ou compléter** le
paragraphe correspondant de `§6.10`. Le rédacteur de BibliOfelia peut copier
les blocs tels quels.

---

## 1. Problème constaté

`§6.10` décrit les endpoints en notation informelle (ex. `{access, refresh}`)
au lieu de schémas JSON exacts. Trois conséquences pour l'appairage :

1. **`GET /pairing/info`** — la spec liste `{box_name, version, library_name}`,
   mais OfeliaScan attend **en plus** le champ `api_base`. Sans lui, la
   désérialisation échoue → « Tester » et « Appairer » échouent.
2. **`POST /auth/login`** — la spec annonce une réponse `{access, refresh}`,
   OfeliaScan lit `{access_token, refresh_token, ...}`. Noms incompatibles
   → login impossible.
3. **Découverte mDNS** — OfeliaScan recherche le service `_bibliofelia._tcp.`
   sur le réseau local ; `§6.10` ne spécifie nulle part que la box doit le
   publier. Sans cela, la découverte automatique ne renvoie jamais rien.

Les corrections ci-dessous figent le contrat. **Les noms de champs retenus
sont ceux qu'OfeliaScan implémente déjà** : si BibliOfelia applique cette
spec corrective à la lettre, **OfeliaScan n'a aucune modification à faire**.

---

## 2. Conventions générales (à ajouter en tête de §6.10)

- **Base URL** : `http://<box-ip>/biblio/api/v1/` — le slash final est
  significatif (le client concatène les chemins relatifs).
- **Encodage** : JSON UTF-8, `Content-Type: application/json`.
- **Nommage des champs** : `snake_case` pour tous les champs JSON.
- **Dates** : chaînes ISO 8601 UTC (`2026-05-22T14:30:00Z`).
- **Authentification** : JWT Bearer. Tous les endpoints exigent l'en-tête
  `Authorization: Bearer <access_token>`, **sauf** `GET /pairing/info` et la
  publication mDNS (§7), qui doivent rester accessibles sans token pour
  permettre la découverte avant appairage.
- **Champs additionnels** : la box peut renvoyer des champs non listés ici ;
  le client les ignore. Les champs **listés comme requis ci-dessous doivent
  toujours être présents** (un champ requis absent fait échouer le client).

---

## 3. Authentification

### 3.1 `POST /auth/login`

Authentification non requise.

**Requête :**
```json
{ "username": "alice", "password": "secret" }
```

**Réponse `200` :**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

| Champ           | Type    | Requis | Notes                                  |
|-----------------|---------|--------|----------------------------------------|
| `access_token`  | string  | oui    | JWT court (≈1 h)                       |
| `refresh_token` | string  | oui    | JWT long (90 j, cf. §6.10)             |
| `token_type`    | string  | oui    | toujours `"Bearer"`                    |
| `expires_in`    | integer | oui    | durée de vie de l'access token, en s   |

> **Correction** : la spec disait `{access, refresh}`. Le contrat retient les
> noms **OAuth 2.0 standard** (`access_token`, `refresh_token`, `token_type`,
> `expires_in`). Django SimpleJWT renvoie `{access, refresh}` par défaut →
> BibliOfelia doit fournir un **serializer/vue personnalisé** qui ré-émet ces
> quatre champs.

**Erreurs :** `401` si identifiants invalides (cf. §5 format d'erreur).

### 3.2 `POST /auth/refresh`

Authentification non requise (le refresh token fait foi).

**Requête :**
```json
{ "refresh_token": "<jwt>" }
```

**Réponse `200` :** identique à `/auth/login` (les quatre mêmes champs).

> **Correction** : la spec disait requête `{refresh}` → réponse `{access}`.
> Le contrat impose :
> - le champ de requête est `refresh_token` ;
> - la réponse renvoie **aussi un nouveau `refresh_token`** : activer la
>   **rotation des refresh tokens** côté SimpleJWT
>   (`ROTATE_REFRESH_TOKENS = True`, `BLACKLIST_AFTER_ROTATION = True`).
>   Cela uniformise la réponse avec `/auth/login` et améliore la sécurité
>   (l'ancien refresh token est invalidé).

### 3.3 `POST /auth/logout`

Authentification requise (`Authorization: Bearer <access_token>`).

**Requête :** corps vide.
**Réponse `204` :** corps vide.

Effet : la box met sur liste noire le(s) refresh token(s) de l'utilisateur
courant (nécessite l'app `rest_framework_simplejwt.token_blacklist`).

> **Correction** : `§6.10` ne précisait pas le mode d'authentification.
> Le contrat impose : pas de corps de requête, l'utilisateur est identifié
> par l'access token de l'en-tête.

---

## 4. Pairing

### 4.1 `GET /pairing/info`

**Authentification non requise** (endpoint de découverte).

**Réponse `200` :**
```json
{
  "box_name": "OfeliaBox-Tulear",
  "library_name": "Bibliothèque de Tuléar",
  "version": "1.4.0",
  "api_base": "/biblio/api/v1/"
}
```

| Champ          | Type   | Requis | Notes                                       |
|----------------|--------|--------|---------------------------------------------|
| `box_name`     | string | oui    | nom d'instance de la box                    |
| `library_name` | string | oui    | nom de la bibliothèque (affiché à l'usager) |
| `version`      | string | oui    | version logicielle BibliOfelia              |
| `api_base`     | string | oui    | chemin de base de l'API, slash final inclus |

> **Correction** : la spec listait `{box_name, version, library_name}`. Le
> contrat **ajoute `api_base`**, requis. BibliOfelia doit l'inclure dans la
> réponse de la vue `/pairing/info`. Valeur attendue : `"/biblio/api/v1/"`.

### 4.2 `POST /pairing/claim`

Hors périmètre de cette correction (flux QR code, reporté côté OfeliaScan).
À spécifier dans une correction ultérieure si le flux est activé.

---

## 5. Diagnostic — `GET /health`

Authentification requise.

**Réponse `200` :**
```json
{
  "status": "ok",
  "version": "1.4.0",
  "disk_free_mb": 12480,
  "last_backup_at": "2026-05-21T03:00:00Z"
}
```

| Champ            | Type    | Requis | Notes                                   |
|------------------|---------|--------|-----------------------------------------|
| `status`         | string  | oui    | `"ok"` ou `"degraded"`                  |
| `version`        | string  | non    | version logicielle                      |
| `disk_free_mb`   | integer | non    | espace disque libre (Mo)                |
| `last_backup_at` | string  | non    | date ISO 8601 de la dernière sauvegarde |

> **Correction** : `§6.10` décrivait le contenu en prose (« espace disque,
> version, dernière sauvegarde ») sans schéma. Le contrat impose **au moins
> le champ `status`** (string). OfeliaScan ne lit que `status` et `version` ;
> les autres champs sont facultatifs mais recommandés pour le tableau de bord.
> Sans `status`, l'indicateur « box joignable » de l'écran Paramètres reste
> bloqué sur « injoignable » (sans planter l'app).

---

## 6. Métadonnées — `GET /isbn/{isbn}`

Authentification requise.

**Réponse `200` :**
```json
{
  "isbn": "9782070612758",
  "title": "L'Étranger",
  "authors": ["Albert Camus"],
  "publisher": "Gallimard",
  "publication_year": 1972,
  "language": "fra",
  "cover_url": "http://<box-ip>/biblio/media/covers/...",
  "source": "cache",
  "cached": true
}
```

| Champ              | Type           | Requis | Notes                                   |
|--------------------|----------------|--------|-----------------------------------------|
| `isbn`             | string         | oui    | ISBN demandé, ré-émis tel quel          |
| `title`            | string \| null | non    |                                         |
| `authors`          | string[]       | non    | tableau vide si inconnu                 |
| `publisher`        | string \| null | non    |                                         |
| `publication_year` | integer\| null | non    | **et non `year`**                       |
| `language`         | string \| null | non    | code langue (ex. `fra`)                 |
| `cover_url`        | string \| null | non    |                                         |
| `source`           | string \| null | non    | `cache` / `openlibrary` / …             |
| `cached`           | boolean        | non    | ignoré par OfeliaScan                   |

**Réponse `404`** si l'ISBN est introuvable (cf. §5 format d'erreur).

> **Correction** : `§6.10` écrivait `year` ; le contrat retient
> **`publication_year`** (cohérent avec la base BibliOfelia et OfeliaScan).
> Le champ `isbn` doit **toujours** être présent dans la réponse `200`.

---

## 7. Découverte mDNS / DNS-SD (nouveau — à ajouter à §6.1 ou §6.10)

`§6.10` ne spécifie aucun mécanisme de découverte. OfeliaScan (FEAT-006)
recherche la box via mDNS. **La box doit publier un service DNS-SD.**

### 7.1 Service à publier

| Propriété      | Valeur                                              |
|----------------|-----------------------------------------------------|
| Type de service| `_bibliofelia._tcp.`                                |
| Port           | port HTTP de l'API (par défaut `80`)                |
| Nom d'instance | nom de la box (= `box_name` de `/pairing/info`)     |
| Domaine        | `.local`                                            |

### 7.2 Enregistrements TXT (recommandés)

Pour permettre au client d'afficher la bibliothèque **sans appel HTTP** :

```
library_name=Bibliothèque de Tuléar
version=1.4.0
api_base=/biblio/api/v1/
```

> OfeliaScan v1 n'exploite pas encore les TXT records (il résout host:port
> puis valide via « Tester »). Les publier dès maintenant prépare une
> évolution OfeliaScan où la liste des box découvertes affiche directement
> le nom de la bibliothèque.

### 7.3 Implémentation côté box (Raspberry Pi 5)

- Installer `avahi-daemon` sur l'hôte (Raspberry Pi OS), **pas dans le
  conteneur Docker** — ou exécuter le conteneur en `network_mode: host`.
- Déposer un fichier de service Avahi, généré au provisioning avec le nom
  réel de la bibliothèque :

```xml
<!-- /etc/avahi/services/bibliofelia.service -->
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name replace-wildcards="yes">OfeliaBox-%h</name>
  <service>
    <type>_bibliofelia._tcp</type>
    <port>80</port>
    <txt-record>library_name=Bibliothèque de Tuléar</txt-record>
    <txt-record>version=1.4.0</txt-record>
    <txt-record>api_base=/biblio/api/v1/</txt-record>
  </service>
</service-group>
```

- Le wizard de premier démarrage (`§11.3`) doit régénérer ce fichier avec le
  nom de bibliothèque saisi, puis recharger Avahi.

---

## 8. Format d'erreur (confirmation)

`§6.10` indique déjà : `{error: {code, message, details}}`. À conserver et
appliquer uniformément. OfeliaScan ne lit pas le corps d'erreur en v1 (il se
base sur le code HTTP) ; le format reste néanmoins requis pour la cohérence
et les évolutions.

```json
{ "error": { "code": "invalid_credentials", "message": "…", "details": {} } }
```

Codes HTTP attendus par OfeliaScan : `401` (identifiants), `403` (accès
refusé), `404` (ressource/box introuvable), `5xx` (erreur box).

---

## 9. Récapitulatif des actions côté BibliOfelia

1. Réécrire `§6.10` avec les schémas JSON exacts ci-dessus (§3 à §6, §8).
2. `POST /auth/login` et `/auth/refresh` : serializer personnalisé émettant
   `access_token` / `refresh_token` / `token_type` / `expires_in`.
3. Activer `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` (SimpleJWT)
   et l'app `token_blacklist` (pour `/auth/logout`).
4. `GET /pairing/info` : ajouter le champ `api_base`.
5. `GET /health` : garantir le champ `status`.
6. `GET /isbn/{isbn}` : nommer le champ `publication_year` ; toujours
   renvoyer `isbn`.
7. Ajouter à la spec (et au déploiement) la **publication mDNS Avahi**
   `_bibliofelia._tcp.` (§7).

## 10. Récapitulatif côté OfeliaScan

**Aucune modification de code requise** si BibliOfelia applique cette
correction : les DTOs (`AuthResponse`, `RefreshRequest`, `PairingInfoDto`,
`HealthResponse`, `IsbnLookupResponse`) et le client Retrofit sont déjà
conformes au contrat ci-dessus. Le parseur JSON est configuré en
`ignoreUnknownKeys = true` → les champs box supplémentaires sont tolérés.

Seule évolution **optionnelle** future : lire les TXT records mDNS (§7.2)
dans `NsdDiscoveryService` pour enrichir `DiscoveredBox.libraryName`.
