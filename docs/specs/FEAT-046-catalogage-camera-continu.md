# FEAT-046 — Catalogage en scan caméra continu

**Status:** DONE (validé Val 2026-05-31, déployé Box)
**Date:** 2026-05-31
**SPEC:** §6.1 / §6.10

## Contexte

Suite de FEAT-045 (récolement caméra continu). On remplace OfeliaScan par la
**caméra du navigateur** pour le **catalogage** : le bibliothécaire scanne en
rafale les codes-barres ISBN (EAN-13 `978…`/`979…`) des livres, relit/édite les
notices détectées, puis les envoie au catalogue.

Brique réutilisée : les modèles `ScanSession` / `ScanItem` (catalog) et le
service `finalize_scan_session()` (api), créés pour OfeliaScan (FEAT-021), qui
font déjà *lookup ISBN → matche une notice existante ou la crée → ajoute les
exemplaires*. Le moteur caméra continu de FEAT-044/045 (`scan-camera.js`,
`openCamera(btn, {continuous, onCode, onClose})` + `continuousFeedback`) est
réutilisé tel quel (bande de décodage centrale assombrie incluse).

**Contrainte connue (héritée FEAT-044/045)** : `getUserMedia` exige un contexte
sécurisé (HTTPS). En LAN HTTP la caméra ne démarre pas → un champ de **saisie
manuelle** d'ISBN reste disponible sur le hub.

## Décisions (Val, 2026-05-31)

1. **Notice existante (match ISBN) → on n'ajoute que des exemplaires.** La notice
   existante n'est jamais modifiée (titre/auteur/catégorie conservés).
2. **Rattachement à la session de catalogage** : chaque exemplaire créé pointe
   sur sa `ScanSession` (`Item.catalog_session`). But : pouvoir **réimprimer
   uniquement les étiquettes des exemplaires de cette session**, sans réimprimer
   ce qui a été catalogué avant.
3. **Pendant le scan** : on affiche le **titre + auteur** si le lookup ISBN les
   trouve, **sinon ISBN + langue**.
4. **« exemplaire X » en gros** dans le viseur quand on crée un exemplaire
   supplémentaire (même ISBN re-scanné après > 3 s).
5. **Caméra** identique au récolement : la bande qui décode reste claire, le
   reste est assombri.
6. **Défauts par lot** (catégorie + emplacement) choisis au démarrage,
   **surchargeables par ligne** sur le hub.

## Comportement

### `/catalog/scan/new/` — démarrer un lot

Mini-formulaire : **emplacement par défaut** + **catégorie par défaut** + libellé
optionnel. « Démarrer le catalogage » crée une `ScanSession` (état `open`) et
redirige vers le hub `?scan=1` (la caméra démarre d'un tap — geste requis iOS).

### `/catalog/scan/<pk>/` — hub de scan + édition

- **Panneau de scan** en tête : bouton **« Scanner des livres »** (classe
  `.js-scan-cataloging`). Au clic → caméra **mode continu** ; chaque code confirmé
  (checksum + préfixe + consensus) est posté à `scan_add`.
  - **Code ISBN (978/979)** : crée/incrémente un `ScanItem` (cf. règle ci-dessous).
  - **Code Ofelia exemplaire (290)** : refusé — déjà catalogué (feedback live).
  - **Carte membre (291)** : refusée — pas un livre.
- **Règle de dédup / exemplaires multiples** (différente du récolement, car
  l'ISBN identifie l'édition, pas l'exemplaire) :
  - 1er scan d'un ISBN → `ScanItem` créé, `copy_count=1`, lookup titre/auteur.
  - même ISBN re-vu **≤ 3 s** après le dernier (livre tenu en vue, refire du
    moteur) → **ignoré**, `copy_count` inchangé (mais l'horodatage est rafraîchi).
  - même ISBN re-présenté **> 3 s** après → **`copy_count += 1`** (2ᵉ, 3ᵉ
    exemplaire). Le viseur affiche **« exemplaire X »** en gros.
  - Comme le moteur réémet un code tenu en vue toutes les ~0,8 s, l'horodatage
    « dernier vu » est rafraîchi à chaque émission : un livre simplement maintenu
    ne franchit jamais le seuil de 3 s. Seul un retrait + re-présentation le fait.
- **Tableau des items scannés**, éditables avant envoi : ISBN, **titre**,
  **auteur(s)**, **langue**, **catégorie** (défaut du lot), **emplacement**
  (défaut du lot), **état**, **nb d'exemplaires**, suppression de ligne.
  Bouton « appliquer la catégorie / l'emplacement à toutes les lignes ».
- **Actions** :
  - **« Enregistrer »** : persiste les éditions, la session reste ouverte (on
    peut continuer à scanner).
  - **« Envoyer au catalogue »** : persiste les éditions puis
    `finalize_scan_session()` — création des notices/exemplaires. Redirige vers
    l'impression des étiquettes filtrée sur cette session.

### Finalisation (`finalize_scan_session`)

Inchangée dans son principe (matching ISBN → matche ou crée), avec deux ajouts :
- chaque `Item` créé reçoit `catalog_session = session` (décision #2) ;
- pour une **nouvelle** notice, `category` est posée depuis le `ScanItem` ; une
  notice **matchée** n'est pas touchée (décision #1).

Titre : si le `ScanItem` a un titre (lookup en ligne ou saisi), il est utilisé ;
sinon placeholder language-neutral `ISBN:<isbn> - <date>` (rattrapable par
l'enrichissement FEAT-031).

### Impression ciblée des étiquettes

`printing:labels` accepte `?catalog_session=<pk>` : la liste ne montre que les
exemplaires de cette session. Après « Envoyer au catalogue », on y arrive
directement → « tout sélectionner » → PDF / CUPS.

## Spec technique

### Modèles (`apps/catalog/models.py`) — migration `0008`

- `Item.catalog_session` → `FK(ScanSession, null=True, blank=True,
  on_delete=SET_NULL, related_name="created_items")`. SET_NULL : supprimer une
  session ne doit jamais supprimer les exemplaires (la session n'est qu'un
  regroupement).
- `ScanItem.category` → `FK(Category, null=True, blank=True, SET_NULL)`.
- `ScanSession.default_location` → `FK(Location, null=True, blank=True, SET_NULL)`.
- `ScanSession.default_category` → `FK(Category, null=True, blank=True, SET_NULL)`.

### Endpoint de scan (JSON)

`POST /catalog/scan/<pk>/add/` (`catalog:scan_add`, librarian/superadmin) —
body `ean=<code>` + `X-CSRFToken`. Réponse :

```json
{
  "ok": true,
  "action": "created|incremented|ignored|rejected",
  "isbn": "9782070368228",
  "scanitem_id": 12,
  "copy_count": 2,
  "title": "…",          // ou "" si lookup KO
  "author": "…",
  "language": "fr",
  "label": "exemplaire 2" // libellé prêt à afficher
}
```

- `rejected` si le code n'est pas un ISBN livre (290 = déjà catalogué, 291 =
  carte membre, autre préfixe). 409 si session non `open`.
- Le lookup ISBN (`apps/catalog/openlibrary.py:lookup_isbn`) est tenté à la
  création (timeout court ; None si box hors-ligne → titre vide).

### Contrôleur de page (`static/js/scan-cataloging.js`)

Chargé sur `scan_session.html` (extra_head). Câble `.js-scan-cataloging` →
`openCamera(btn, {continuous, onCode, onClose})`. **Pas de set `seen`** côté
client (contrairement au récolement) : tous les codes sont postés, c'est le
serveur qui décide ignoré/incrément/création (règle des 3 s). Sur `created` →
feedback titre/auteur ; sur `incremented` → **« exemplaire X » en gros**
(`continuousFeedback` + emphase CSS sur `#scan-camera-last`). Repli saisie
manuelle. Recharge la page à la fermeture du viseur.

## Impact sur l'existant

- `apps/catalog/models.py` : 4 champs (migration `0008`).
- `apps/api/services.py` : `_add_copies` pose `catalog_session` ; `_create_record`
  pose `category`.
- `apps/catalog/forms.py` : `ScanCatalogSessionForm`.
- `apps/catalog/views.py` + `urls.py` : 6 vues + routes `/catalog/scan/...`.
- `templates/catalog/` : `scan_session_form.html`, `scan_session.html`,
  `scan_session_list.html`.
- `static/js/scan-cataloging.js` : **nouveau**.
- `apps/printing/views.py` + `templates/printing/labels_picker.html` : filtre
  `catalog_session`.
- `templates/catalog/record_list.html` + `templates/core/advanced.html` : entrée
  « Cataloguer en scannant ».
- `static/css/ofelia.css` : styles hub + emphase « exemplaire X ».
- `scan-camera.js` : **inchangé** (réutilisé).

## i18n

Nouvelles chaînes EN/ES/MG via `scripts/translations_sprint19.py` + gate
`scripts/i18n_check.py` → 0.

## Tests

`apps/catalog/tests/test_cataloging.py` (13 cas) : création de session, `scan_add`
(created / ignored <3 s / incremented >3 s / rejected 290-291 / 409 closed /
pas de doublon d'ISBN), suppression de ligne, finalize (nouvelle notice avec
catégorie + `catalog_session` sur l'exemplaire ; notice existante → +1 exemplaire
sans modif de la notice), permissions, filtre impression par session.

## Itérations post-test (Val, 2026-05-31)

1. **Hub simplifié + mobile** : titre / auteur / langue passés en **lecture
   seule** (auteur au-dessus du titre, colonne large) ; catégorie / emplacement /
   état modifiables **uniquement par lot** via cases à cocher (par ligne + « tout
   cocher ») et panneau « Modifier les lignes cochées » ; Ex. (nb d'exemplaires)
   et corbeille inchangés ; scroll horizontal mobile (`.cat-scan-wrap`,
   `min-width` table). `scan_session_commit` ne persiste plus que catégorie /
   emplacement / état / nb d'exemplaires.
2. **BUG doublons d'ISBN** : un même ISBN re-scanné créait 2 lignes. Cause :
   `ATOMIC_REQUESTS = True` enveloppait `scan_add` dans une transaction tenue
   ouverte par le lookup HTTP (lent) → ligne créée invisible aux POST concurrents
   (3 workers gunicorn). Fix : `@transaction.non_atomic_requests` (autocommit) +
   création de la ligne **avant** le lookup + réconciliation déterministe
   (`_bump_existing`, garde l'`id` min) + garde client `inFlight` dans
   `scan-cataloging.js`. Test `test_scan_add_no_duplicate_isbn_line`.
3. **Titres FR manquants** : `lookup_isbn` (OpenLibrary seule) ratait ~la moitié
   des livres FR. Nouveau `lookup_isbn_multi()` (`apps/catalog/openlibrary.py`) :
   interroge en parallèle les 4 sources FEAT-031 (`sources/__init__.py:SOURCES`)
   et prend le 1er titre non vide (ordre OL → Google Books → BnF → BNE).
   `_clean_multi_result()` coupe le titre SRU au premier ` / ` (mention de
   responsabilité collée). `scan_add` utilise désormais ce lookup. La BnF est la
   source qui sauve le FR (sans clé) ; Google Books requiert une clé API.
