# FEAT-023 — Scan handoff single-scan OfeliaScan

Statut : **EN COURS** (2026-05-23) — code BibliOfelia livré, contrat Android à
implémenter dans le repo OfeliaScan.
Sprint : 7
Task : #21 (cf. `docs/tasks/TASKS.md`)
Spec : `SPEC_BIBLIOFELIA.md` §6.10 (sous-section « Handoff single-scan »)

## Contexte

Les boutons « Scanner » du site web BibliOfelia (prêt carte/livre, retour
livre, banner du dashboard) n'étaient que des champs de saisie texte
décorés d'une icône code-barres. Le bibliothécaire devait taper l'ISBN/le
code Ofelia à la main.

OfeliaScan (Android) existe et sait scanner, mais en mode **session de lot**
(FEAT-021) : ouvrir une session → scanner N livres → POST batch → finalize.
Cela ne convient pas pour un scan unitaire inline, où le résultat doit
revenir immédiatement dans la page web.

FEAT-023 ajoute un protocole **single-scan + retour de valeur** :

- la page web crée un *handoff* (token UUID + TTL 5 min),
- ouvre un deep-link `ofeliascan://scan-one?token=...`,
- OfeliaScan scanne **un** code et POST le résultat (JWT) à la box,
- la page web poll le résultat et l'injecte dans le champ correspondant.

Cible v1 : bibliothécaires Android avec OfeliaScan installé. Pour iOS / Android
sans l'app, l'intent échoue silencieusement, le champ texte reste disponible
(saisie manuelle, comportement actuel — pas de régression).

## Architecture côté BibliOfelia

### Modèle `apps/api/models.py:ScanHandoff`

```python
class ScanHandoff(Model):
    token        = UUIDField(default=uuid4, unique=True, editable=False)
    created_by   = FK(User, on_delete=CASCADE, related_name="scan_handoffs")
    target_kind  = CharField(choices=auto|book|card, default=auto)
    state        = CharField(choices=pending|completed|cancelled, default=pending)
    value        = CharField(blank=True, max_length=64)
    value_kind   = CharField(blank=True, max_length=20)   # ean13|isbn|card|item|manual
    created_at   = DateTimeField(default=now)
    expires_at   = DateTimeField()                         # created_at + 5 min
    completed_at = DateTimeField(null=True, blank=True)
    completed_by = FK(User, null=True, on_delete=SET_NULL, related_name="+")
```

État `expired` calculé à la volée si `state=pending` et `expires_at < now`.
Index `(state, expires_at)` pour nettoyage périodique éventuel.

Migration : `apps/api/migrations/0001_initial.py` (l'app n'avait pas de
table jusqu'ici).

### Endpoints

Tous sous le préfixe `/api/v1/`, **sans slash final** (convention SPEC §6.10).

#### `POST /scan-handoff` — création (web → box)

- Auth : session (cookie navigateur) OU JWT — en pratique session.
- Permission : `librarian` ou `superadmin`. Un `contributor_api` (OfeliaScan)
  ne crée pas de handoff (il les consomme). Retourne `403 forbidden` sinon.
- CSRF enforced via `SessionAuthentication`. Le JS lit `csrftoken` cookie et
  envoie `X-CSRFToken`.
- Body : `{"target_kind"?: "auto"|"book"|"card"}` (défaut `auto`).
- Réponse `201` :

  ```json
  {
    "token": "uuid",
    "state": "pending",
    "target_kind": "auto",
    "value": "",
    "value_kind": "",
    "created_at": "2026-05-23T15:30:00Z",
    "expires_at": "2026-05-23T15:35:00Z",
    "completed_at": null,
    "deep_link": "ofeliascan://scan-one?token=<uuid>&kind=<auto|book|card>"
  }
  ```

#### `GET /scan-handoff/{token}` — polling navigateur

- Auth : session OU JWT.
- Permission : créateur du handoff uniquement ; superadmin voit tout. Sinon
  `404` (pas de fuite d'existence).
- Réponse `200` : même schéma que la création **sans `deep_link`** ; `state`
  vaut `pending|completed|cancelled|expired` (calculé), `value`/`value_kind`
  remplis si `completed`.

#### `POST /scan-handoff/{token}` — callback OfeliaScan

- Auth : JWT requis (l'app n'a pas de cookie de session).
- Permission : tout JWT authentifié peut soumettre — le token UUID **est** la
  capability. La confidentialité du deep-link et la durée de vie courte
  (5 min, single-use) suffisent en LAN ; HTTPS attendu en production
  externe (cf. FEAT-024).
- Body : `{"value": "9782070612758", "kind": "ean13"|"isbn"|"card"|"item"|"manual"}` ou
  `{"cancelled": true}` si l'utilisateur abandonne le scan.
- Si `cancelled=false` (défaut), `value` non vide requis (sinon `400`).
- Réponses :
  - `200` : succès, état passe à `completed` (ou `cancelled`) ; renvoie l'état complet.
  - `409 already_completed` si un POST précédent a déjà terminé le handoff.
  - `410 expired` si `expires_at < now` (TTL dépassé).
  - `404` si token inconnu.

### Frontend JS

`static/js/scan-handoff.js` — script chargé sur toutes les pages
authentifiées (`base.html`). Détecte tout élément `.js-scan-handoff` au
clic et orchestre le handoff. Markup déclaratif via `data-*` :

| Attribut | Rôle | Exemple |
|---|---|---|
| `data-scan-target` | sélecteur du `<input>` à pré-remplir avec la valeur scannée | `"input[name=ean]"` |
| `data-scan-kind` | indication UI pour OfeliaScan | `"book"`, `"card"`, `"auto"` |
| `data-scan-autosubmit` | si `"true"`, soumet le formulaire englobant après remplissage | `"true"` |
| `data-scan-dispatch-url` | URL de redirection (mode dashboard) ; le JS ajoute `?q=<value>` | `"{% url 'core:search' %}"` |

Comportement client :

1. clic → POST `/api/v1/scan-handoff` (target_kind) → reçoit `token` + `deep_link`
2. `window.location.href = deep_link` → Android bascule sur OfeliaScan si installé
3. polling `GET /api/v1/scan-handoff/<token>` toutes les 700 ms (timeout
   client 120 s)
4. à réception de `state=completed` :
   - si `dispatch-url` fourni → redirige vers `<dispatch-url>?q=<value>`
     (le navigateur réutilise la recherche globale `core:search` qui
     classifie le code et redirige vers la bonne page — fiche notice,
     fiche membre, ou liste catalogue)
   - sinon → injecte `value` dans le champ ciblé, puis `requestSubmit()`
     du formulaire si `autosubmit=true`
5. `cancelled` ou `expired` → bouton réactivé, message muet, l'utilisateur
   peut retaper à la main dans le champ texte (qui reste visible).

CSRF : le cookie `csrftoken` est `HttpOnly` (`CSRF_COOKIE_HTTPONLY=True`,
§9) donc inaccessible au JS. Le token est lu depuis le rendu de
`{% csrf_token %}`, injecté dans `#scan-handoff-config`, et posé en header
`X-CSRFToken` sur le POST de création (SessionAuthentication l'exige).
Même pattern qu'`hx-headers` pour HTMX dans `base.html`. Les GET et le
POST OfeliaScan ne sont pas concernés (JWT bypass). Voir BUG-011.

### Boutons câblés (v1)

| Page | Bouton | `data-scan-target` | `data-scan-kind` | Action |
|---|---|---|---|---|
| `loans/lend.html` | « Scanner la carte » | `input[name=card]` | `card` | autosubmit form `action=set_member` |
| `loans/lend.html` | « Scanner un livre » | `input[name=ean]` | `book` | autosubmit form `action=add_item` |
| `loans/return.html` | « Enregistrer le retour » | `input[name=ean]` | `book` | autosubmit form `action=add_item` |
| `core/dashboard.html` | banner « Scanner une carte ou un livre » | — | `auto` | redirige vers `core:search?q=<value>` (dispatch automatique 290/291/ISBN/texte par `classify_query`) |

Le récolement (`inventory/session_detail.html`) n'est **pas** câblé : il est
déjà couvert par le flux bulk OfeliaScan (FEAT-021).

## Contrat côté OfeliaScan (Android) — à implémenter

### Intent filter

```xml
<intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="ofeliascan" android:host="scan-one" />
</intent-filter>
```

Le navigateur de la box envoie l'utilisateur sur
`ofeliascan://scan-one?token=<UUID>&kind=<auto|book|card>`.

### Comportement attendu

1. Récupérer `token` (obligatoire) et `kind` (indicatif UI).
2. Vérifier que l'app est appairée à une box (sinon afficher un toast
   « Appairez OfeliaScan à votre box avant de scanner » et fermer).
3. Ouvrir l'écran **scan unique** :
   - selon `kind`, adapter le libellé (« Scannez la carte », « Scannez un
     livre », « Scannez un code »).
   - viseur caméra classique (ZXing/MLKit), accepte ean13 + isbn + code39.
   - bouton « Annuler ».
4. Au scan réussi : `POST <box_base_url>/api/v1/scan-handoff/<token>` (le
   slash final n'est PAS attendu sur ce chemin, comme tous les autres
   chemins OfeliaScan), Authorization JWT déjà stocké, body :

   ```json
   {"value": "<code scanné>", "kind": "ean13|isbn|card|item|manual"}
   ```

   - `kind=card` si valeur commence par `291` (code Ofelia carte membre)
   - `kind=item` si commence par `290` (code Ofelia exemplaire)
   - `kind=ean13` pour un EAN-13 quelconque (ISBN typiquement)
   - `kind=isbn` pour un ISBN-10 (10 chiffres + X final)
   - `kind=manual` si saisie clavier de secours

5. Au tap « Annuler » : `POST` avec `{"cancelled": true}`.

6. Après le POST (succès ou annulation), rendre la main au navigateur via
   `Intent.ACTION_MAIN` avec `CATEGORY_HOME` ou simplement `finish()` (le
   navigateur reste en tâche de fond et l'utilisateur revient via le sélecteur
   système ou Android le ramène automatiquement). Le navigateur poll, voit
   `state=completed` ou `cancelled` et termine le flux.

### Réponses possibles de la box

- `200 OK` : handoff complété, OK.
- `409 already_completed` : un autre client a déjà répondu — OfeliaScan
  affiche « Scan ignoré : déjà traité ».
- `410 expired` : le navigateur a abandonné depuis longtemps — afficher
  « Scan trop tardif » et fermer.
- `404` : token inconnu — afficher « Lien expiré ou invalide ».

### Sécurité

- Token bearer single-use, TTL 5 min ; non rejouable.
- LAN privé ; HTTPS sera requis pour FEAT-024 (scanner caméra navigateur).
- Aucune donnée sensible dans le deep-link (juste un UUID opaque).

## Tests

`apps/api/tests/test_scan_handoff.py` — 18 cas verts :

- création par librarian (session) / 401 anonyme / 403 contributor_api
- polling par créateur / superadmin (any) / 404 autre user / 401 anonyme
- `state=expired` calculé après TTL
- callback JWT : valeur, normalisation (`normalize_code`), annulation,
  double soumission `409`, post-TTL `410`, body invalide `400`, anonyme `401`
- round-trip complet librarian/scanner

## Hors périmètre v1

- **FEAT-024** (sprint suivant) : scanner caméra navigateur (html5-qrcode)
  pour iOS et Android-sans-OfeliaScan. Nécessite HTTPS sur la box.
- Nettoyage périodique des handoffs expirés : la table reste petite (TTL
  5 min, quelques entrées par jour) ; on ajoutera une tâche django-q2
  quotidienne si nécessaire.
- Pas de notification push à OfeliaScan : c'est l'utilisateur qui ouvre
  l'app via le deep-link, pas l'inverse.

## Doc

- `SPEC_BIBLIOFELIA.md` §6.10 : nouvelle sous-section « Handoff single-scan ».
- Version SPEC incrémentée.
- `TASKS.md` Sprint 7 ajouté.
