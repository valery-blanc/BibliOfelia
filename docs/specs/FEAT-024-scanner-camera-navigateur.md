# FEAT-024 — Scanner caméra navigateur (fallback hors OfeliaScan)

Statut : **DONE — validé Val 2026-05-23** (caméra interne OK sur Android Firefox HTTPS, fallback OfeliaScan automatique en HTTP LAN, Chrome Android sans Play Store, bouton Annuler fonctionnel)
Sprint : 7
Task : #22 (cf. `docs/tasks/TASKS.md`)
Spec : `SPEC_BIBLIOFELIA.md` §6.10 (sous-section « Scanner caméra navigateur »)

## Contexte

FEAT-023 a câblé les 4 boutons « Scanner » (dashboard, prêt-carte,
prêt-livre, retour) sur un handoff single-scan vers **OfeliaScan Android**.
Trois cas restent non couverts :

- **iOS** (pas d'OfeliaScan disponible),
- **Android sans l'app installée**,
- **Poste fixe desktop avec webcam** à la banque d'accueil.

FEAT-024 ajoute un **scanner caméra navigateur** via la lib locale
[`html5-qrcode`](https://github.com/mebjas/html5-qrcode) (Apache-2.0,
375 Ko minifié, utilise l'API native `BarcodeDetector` + fallback ZXing-JS
embarqué). Le bibliothécaire choisit son mode via un **toggle persistant**
attaché à chaque bouton « Scanner ».

## Contrainte HTTPS

`navigator.mediaDevices.getUserMedia` exige `window.isSecureContext`
(HTTPS ou `localhost`). La box est déjà servie en HTTPS quand on y accède
via le domaine externe (ZeroTier / reverse proxy déjà configuré).

**Décision** (Val 2026-05-23) : aucun certificat auto-signé installé sur
les téléphones. La feature ne fonctionne **que quand on a accès à internet**
(donc en HTTPS). En LAN HTTP, le mode reste explicitement indisponible —
l'option apparaît grisée dans le toggle avec un tooltip explicatif.

## Sélection automatique du mode (révision Val 2026-05-23)

Pas de toggle UI — le bouton « Scanner » essaie **toujours d'abord la
caméra interne** (on reste dans la page) et **bascule automatiquement sur
OfeliaScan** quand la caméra n'est pas dispo. Aucun choix à faire pour le
bibliothécaire.

Détection au clic :

| Condition | Résultat |
|---|---|
| HTTPS + `mediaDevices.getUserMedia` dispo | → modal caméra ouvert |
| HTTP LAN, ou navigateur sans `getUserMedia` | → handoff OfeliaScan direct |
| Caméra refusée (`NotAllowedError`), absente (`NotFoundError`), occupée (`NotReadableError`), ou lib KO | → modal fermé silencieusement + handoff OfeliaScan + flashMessage « Caméra indisponible — ouverture d’OfeliaScan. » |
| Utilisateur clique « Annuler » / Esc / hors modal | → bouton restauré, pas de fallback (cancel explicite) |

Le module `scan-camera.js` expose `openCamera(btn, {onUnavailable})` ; le
callback est invoqué uniquement pour les erreurs techniques, pas pour un
cancel utilisateur.

### Diagnostic verbose

Quand la caméra ne peut pas démarrer, le **flashMessage affiche la raison
exacte** (« HTTPS requis (URL en http:) », « navigateur sans
getUserMedia », « module scan-camera.js non chargé », etc.). Idem pour
les erreurs `Html5Qrcode` : `permission-denied`, `no-camera`,
`camera-busy`, `lib-load-failed`. La même info est aussi loggée dans la
console JS (`[scan] camera support: {...}`). Cela a permis d'identifier
en quelques secondes le cas Val (cache navigateur servant l'ancien JS).

### Chrome Android — éviter le Play Store

L'intent URL générée côté serveur est complétée côté client par
`S.browser_fallback_url=<page courante>` avant `;end`. Si OfeliaScan
n'est pas installé, Chrome navigue vers la page courante (= reste sur
BibliOfelia) **au lieu de rediriger vers le Play Store**.

### Bouton « Annuler » pendant l'attente OfeliaScan

Pendant la phase `setBusy(true)` du handoff, un lien « Annuler »
s'affiche sous le bouton. Le clic stoppe immédiatement le polling et
restaure le bouton — utile quand l'utilisateur revient manuellement sur
la page sans qu'OfeliaScan ait POST. Tracking par `WeakMap<btn, {intervalId}>`.

## Architecture frontend

### Fichiers livrés

| Fichier | Rôle |
|---|---|
| `static/js/html5-qrcode.min.js` | Lib vendorée v2.3.8 (375 KB, Apache-2.0). |
| `static/js/scan-handoff.js` | *Modifié* — click handler : caméra d'abord (si dispo) sinon OfeliaScan. Expose `window.BibliOfelia.scan = {applyResult, flashMessage, setBusy, startHandoff, cameraSupported}`. |
| `static/js/scan-camera.js` | Lazy-load lib, modal viseur, démarrage `Html5Qrcode` (`facingMode: environment`, formats EAN-13/EAN-8/UPC/CODE_128/CODE_39/QR/ITF). Erreurs techniques → callback `onUnavailable` (le caller fait le fallback OfeliaScan). |
| `static/css/ofelia.css` | *Étendu* — `.scan-camera-modal` uniquement (full-screen mobile, 480 px desktop). |
| `templates/base.html` | *Modifié* — charge les 2 JS en `defer`, injecte `#scan-mode-i18n` (5 chaînes : modal_title, cancel, hint, opening, scanned). |

Les 3 templates métier (`loans/lend.html` × 2 boutons, `loans/return.html`,
`core/dashboard.html`) **ne sont pas touchés** : le `.js-scan-handoff` reste
le seul sélecteur, comportement transparent pour le bibliothécaire.

### Modal caméra

- Overlay full-screen `position: fixed; inset: 0` avec fond noir 78 %.
- Carte centrée 480 px max desktop, full-height sur mobile (< 480 px).
- Viseur `aspect-ratio: 3/2`, vidéo en `object-fit: cover`.
- Configuration `Html5Qrcode` : `fps: 10`, `qrbox: 80 % de la dimension minimale`,
  `aspectRatio: 1.5`.
- À la première détection : `scanner.stop()` → fermeture modal →
  `BibliOfelia.scan.applyResult(btn, {value})` (mêmes hooks que FEAT-023 :
  `data-scan-target`, `data-scan-autosubmit`, `data-scan-dispatch-url`).
- Bouton « Annuler », clic hors carte, touche `Escape` → ferme le modal et
  restaure le bouton.
- Erreurs gérées :
  - `NotAllowedError` (permission refusée) → message « Permission caméra refusée. »
  - `NotFoundError` (pas de caméra) → message « Aucune caméra détectée sur cet appareil. »
  - Lib échouée au lazy-load → message « Impossible de charger le scanner. »
  - Aucune image n'est envoyée au serveur, décodage 100 % local.

## Sécurité

- Décodage local pur (BarcodeDetector ou ZXing-JS) — pas de fuite réseau de
  l'image caméra.
- `MediaStream` arrêté (`track.stop()`) à la détection ou au cancel.
- Permission caméra demandée par le navigateur à chaque ouverture du modal
  (UX standard, pas de stockage côté app).
- Aucune nouvelle surface API côté Django (pas d'endpoint, pas de migration).

## Périmètre v1

Câblés (héritent de FEAT-023) :

| Page | Bouton |
|---|---|
| `core/dashboard.html` | banner « Scanner une carte ou un livre » |
| `loans/lend.html` | « Scanner la carte » (kind=card) |
| `loans/lend.html` | « Scanner un livre » (kind=book) |
| `loans/return.html` | « Enregistrer le retour » (kind=book) |

Hors périmètre :

- Récolement (`inventory/session_detail.html`) — reste sur le flux bulk
  OfeliaScan (FEAT-021).
- Pages de catalogage / recherche d'exemplaire — pas de bouton Scanner
  aujourd'hui, pas dans le périmètre.
- Cert auto-signé / mkcert — explicitement écarté.

## i18n

5 chaînes utiles ajoutées dans `templates/base.html` (injection JSON
`#scan-mode-i18n`) : `modal_title`, `cancel`, `hint`, `opening`, `scanned`.
Les 8 chaînes initialement prévues pour le toggle (modes, tooltip HTTPS,
errors caméra) restent traduites dans les `.po` (encore référencées par
`templates/base.html` au moment du `makemessages` initial — elles seront
nettoyées par un futur `makemessages -a --no-obsolete`). FR = msgid par
défaut (convention du projet).

## Vérification

1. `docker compose -f docker-compose.dev.yml exec web python manage.py check` → 0 issue.
2. `pytest` → 179 passed (non-régression, aucun nouveau test backend nécessaire).
3. Déploiement Pi : `git pull` + rebuild conteneurs. Pas de migration. Le
   `collectstatic` de `scripts/entrypoint.sh` publie les nouveaux JS/CSS.
4. Test Val :
   - **HTTP LAN** (`http://192.168.0.147/bibliofelia/`) → clic Scanner → on
     part directement sur le handoff OfeliaScan (caméra impossible sans HTTPS).
   - **HTTPS externe** → clic Scanner → la caméra interne s'ouvre dans la
     page, scan d'un livre réel → champ rempli + form soumis.
   - Test sur les 4 entrées.
   - Refuser la permission caméra une fois → vérifier le fallback automatique
     vers OfeliaScan + flashMessage.
   - Test iOS Safari (valider le décodage via BarcodeDetector / fallback ZXing).

## Hors périmètre futur

- Nettoyage automatique localStorage à la déconnexion (faible valeur).
- Préférence côté serveur (compte utilisateur) : envisageable v2 si demande.
