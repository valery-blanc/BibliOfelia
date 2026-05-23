# FEAT-024 — Scanner caméra navigateur (fallback hors OfeliaScan)

Statut : **EN ATTENTE TEST VAL** (2026-05-23)
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

## Choix utilisateur (toggle)

À côté de chaque bouton `.js-scan-handoff` (et en coin haut-droit du banner
dashboard), un chevron ouvre un mini-popover listant deux modes :

1. **Application OfeliaScan** (défaut) — comportement FEAT-023 inchangé.
2. **Caméra de l'appareil** — ouvre le scanner navigateur.

Le choix est mémorisé en **`localStorage`** (clé
`bibliofelia.scan-mode`, valeurs `ofeliascan|camera`) — donc **device-scoped**.
Un même librarian utilisant volontiers iPad puis téléphone Android voit
chaque appareil retenir indépendamment son mode.

États du popover :
- Sélectionné : puce ● + fond cream.
- Option Caméra grisée + tooltip « Nécessite HTTPS — accédez via internet. »
  si `window.isSecureContext === false`.

Si le mode mémorisé est `camera` mais l'utilisateur revient en HTTP LAN, le
clic déclenche un flashMessage explicatif et **retombe automatiquement
sur OfeliaScan** pour ce clic — la préférence stockée n'est pas modifiée
(elle redeviendra effective dès que l'utilisateur sera de nouveau en HTTPS).

## Architecture frontend

### Fichiers livrés

| Fichier | Rôle |
|---|---|
| `static/js/html5-qrcode.min.js` | Lib vendorée v2.3.8 (375 KB, Apache-2.0). |
| `static/js/scan-handoff.js` | *Modifié* — court-circuit vers caméra si mode=`camera` & `isSecureContext`. Expose `window.BibliOfelia.scan = {applyResult, flashMessage, setBusy, readMode}` pour réutilisation. |
| `static/js/scan-camera.js` | Lazy-load lib, modal viseur, démarrage `Html5Qrcode` (`facingMode: environment`, formats EAN-13/EAN-8/UPC/CODE_128/CODE_39/QR/ITF), arrêt à la première détection. |
| `static/js/scan-mode-toggle.js` | Injecte chevron + popover sur chaque `.js-scan-handoff`, persistance localStorage, détection `isSecureContext`. |
| `static/css/ofelia.css` | *Étendu* — `.scan-split`, `.scan-mode-toggle`, `.scan-mode-popover`, `.scan-camera-modal` (full-screen mobile, 480 px desktop), print hide. |
| `templates/base.html` | *Modifié* — charge les 3 JS en `defer`, injecte `#scan-mode-i18n` avec 13 chaînes traduites. |

Les 3 templates métier (`loans/lend.html` × 2 boutons, `loans/return.html`,
`core/dashboard.html`) **ne sont pas touchés** : `scan-mode-toggle.js`
détecte les `.js-scan-handoff` au `DOMContentLoaded` et auto-wrap chaque
bouton dans un `<div class="scan-split">` (ou pose un overlay absolu pour le
banner dashboard). Pour les boutons `btn--block`, la classe
`.scan-split--block` est ajoutée automatiquement pour conserver la largeur 100 %.

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

13 nouvelles chaînes ajoutées dans `templates/base.html` (injection JSON
`#scan-mode-i18n`), traduites en `en` / `es` / `mg`. FR = msgid par défaut
(convention du projet).

## Vérification

1. `docker compose -f docker-compose.dev.yml exec web python manage.py check` → 0 issue.
2. `pytest` → 179 passed (non-régression, aucun nouveau test backend nécessaire).
3. Déploiement Pi : `git pull` + rebuild conteneurs. Pas de migration. Le
   `collectstatic` de `scripts/entrypoint.sh` publie les nouveaux JS/CSS.
4. Test Val :
   - **HTTP LAN** (`http://192.168.0.147/bibliofelia/`) → toggle chevron
     ouvre le popover, option « Caméra » grisée avec tooltip HTTPS.
   - **HTTPS externe** → basculer sur Caméra → cliquer un bouton Scanner →
     autoriser caméra → scanner un livre réel → champ rempli + form soumis.
   - Test sur les 4 entrées + non-régression OfeliaScan (mode par défaut).
   - Test iOS Safari (valider le décodage via BarcodeDetector / fallback ZXing).

## Hors périmètre futur

- Nettoyage automatique localStorage à la déconnexion (faible valeur).
- Préférence côté serveur (compte utilisateur) : envisageable v2 si demande.
