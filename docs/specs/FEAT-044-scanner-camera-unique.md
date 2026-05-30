# FEAT-044 — Scanner caméra navigateur en mode unique (retrait OfeliaScan du flux site)

Statut : **DONE — validé Val 2026-05-30** (Chrome Android : excellent ; Firefox Android & Safari iOS : fonctionnel via QuaggaJS ; boutons scan ajoutés sur catalogue/membres + champ ISBN ; layout dashboard revu).
Sprint : 16
Spec : `SPEC_BIBLIOFELIA.md` §6.10 (sous-section « Scanner caméra navigateur »)
Remplace l'approche de : `FEAT-024-scanner-camera-navigateur.md` (caméra = fallback d'OfeliaScan)

## Contexte

FEAT-023/024 avaient câblé les 4 boutons « Scanner » du site (dashboard,
prêt-carte, prêt-livre, retour) en mode **OfeliaScan d'abord**, la caméra du
navigateur servant de fallback. En pratique, sur un mobile sans OfeliaScan
installé, le clic « Scanner » déclenchait un deep-link `ofeliascan://…` qui ne
faisait **rien de visible** : la caméra ne s'ouvrait jamais (rapporté par Val
le 2026-05-30).

Décision Val : **inverser la logique**. Les boutons du site n'utilisent plus
que la **caméra du navigateur**. OfeliaScan reste réservé au **catalogage** et
au **récolement en masse** (FEAT-021), non touchés.

## Cause racine du « la caméra ne se lance jamais »

`navigator.mediaDevices.getUserMedia` exige un **contexte sécurisé**
(`window.isSecureContext` : HTTPS ou `localhost`). L'ancien `scan-handoff.js`
ne tentait la caméra que si ce contexte était présent, et **basculait
silencieusement sur OfeliaScan** sinon (et même en cas d'échec caméra). Sans
l'app installée, le deep-link était un cul-de-sac silencieux.

Le nouveau comportement **n'a plus de fallback silencieux** : si la caméra ne
peut pas démarrer, un **message d'erreur explicite** s'affiche sous le bouton
avec la raison exacte, ce qui transforme un échec muet en diagnostic lisible.

> ⚠️ Contrainte incontournable : en **HTTP LAN** (`http://192.168.0.147/…`) la
> caméra **ne peut pas** démarrer, c'est une règle de sécurité du navigateur,
> aucun JS ne la contourne. L'accès doit être en **HTTPS**. Val accède à la
> box via le **domaine HTTPS externe** → la caméra fonctionne. Faire marcher la
> caméra aussi en LAN nécessiterait un **HTTPS local sur la box** (cert /
> mkcert servi par nginx) — chantier séparé côté keebee, hors de ce sprint.

## Comportement

| Condition au clic | Résultat |
|---|---|
| HTTPS + `getUserMedia` + module chargé | → modal viseur caméra s'ouvre |
| Page non sécurisée (HTTP) | → erreur « Caméra indisponible — Accès caméra impossible : la page n’est pas en HTTPS. Saisissez le code à la main. » |
| Navigateur sans `getUserMedia` | → erreur « …Ce navigateur ne permet pas l’accès à la caméra… » |
| Permission refusée (`NotAllowedError`) | → erreur « …Permission caméra refusée… » |
| Pas de caméra (`NotFoundError`) | → erreur « …Aucune caméra détectée… » |
| Caméra occupée (`NotReadableError`) | → erreur « …déjà utilisée par une autre application… » |
| Lib `html5-qrcode` KO | → erreur « …Le scanner n’a pas pu être chargé… » |
| Utilisateur Annule / Esc / clic hors modal | → bouton restauré, pas de message (cancel explicite) |

Le message d'erreur reste affiché 12 s (vs 6 s pour un message neutre) et est
coloré en `--burgundy` pour être visible.

## Correctif mobile « le modal clignote et se ferme » (2026-05-30)

Premier test Val sur mobile HTTPS : le modal **clignotait** (apparaissait
puis se fermait aussitôt), la caméra ne démarrait jamais, **sans message
d'erreur**. Cause : sur écran tactile, le **même tap** qui ouvre le modal
plein écran (`position: fixed; inset: 0`) est re-livré (« ghost click ») à
l'overlay fraîchement placé sous le doigt → le handler « clic hors carte =
fermer » se déclenche immédiatement → fermeture instantanée traitée comme une
*annulation explicite* (donc pas de `onUnavailable`, pas de message).

Correctif dans `scan-camera.js` : garde temporelle `DISMISS_GUARD_MS = 600`.
Toute demande de fermeture (clic hors carte, bouton Annuler/×, touche Échap)
survenant dans les 600 ms suivant l'ouverture est **ignorée**. Au-delà, la
fermeture fonctionne normalement.

Diagnostic : les callbacks `onUnavailable(reason, detail)` propagent le **nom
d'erreur brut** du navigateur (`NotAllowedError`, `NotReadableError`…). Le
message d'erreur sous le bouton est **persistant** (le message neutre, lui,
s'efface après 6 s). Le détail technique brut part en `console.warn` (support),
le message à l'écran reste lisible pour le bibliothécaire. *(Un panneau de log
visible à l'écran avait servi au diagnostic pendant la mise au point ; il a été
retiré avant le commit.)*

## Décodage : double moteur + fiabilisation (mise au point 2026-05-30)

La mise en fonctionnement réelle a nécessité plusieurs correctifs successifs,
tous conservés :

1. **Chargement de la lib (404 en prod)** — `scan-camera.js` codait
   `"/static/js/html5-qrcode.min.js"` en dur, sans le préfixe `FORCE_SCRIPT_NAME`
   (`/bibliofelia/`) **ni le hash** de `ManifestStaticFilesStorage`
   (`html5-qrcode.min.<hash>.js`) → 404 → la lib ne se chargeait jamais (échec
   masqué auparavant par le fallback OfeliaScan). **Fix** : l'URL de la lib est
   injectée par le template via `{% static %}` dans
   `#scan-camera-config` (`libUrl`, `quaggaUrl`), qui résout préfixe + hash.

2. **Permission caméra iOS Safari** — iOS exige que `getUserMedia` soit appelé
   **dans le geste utilisateur**. Le lazy-load de la lib (fetch) cassait ce
   contexte → `NotAllowedError`. **Fix** : `primeCameraPermission()` demande la
   permission **synchroniquement dans le tap**, avant de charger la lib ; la
   permission accordée persiste pour la session. *(Si la permission a été
   refusée une fois, iOS la mémorise : Réglages → Safari → Caméra → « Demander ».)*

3. **Double moteur de décodage** (le point clé pour la qualité) :
   - `BarcodeDetector` natif dispo (Chrome/Edge Android, Chrome desktop) →
     **html5-qrcode** avec `experimentalFeatures.useBarCodeDetectorIfSupported`
     → décodage quasi natif, rapide et fiable.
   - sinon (Safari iOS, Firefox Android, qui **n'ont pas** `BarcodeDetector`) →
     **QuaggaJS** (`static/js/quagga.min.js`, @ericblade/quagga2 v1.8.4, 143 Ko,
     MIT, vendoré local), spécialisé 1D/EAN, nettement meilleur que le repli
     ZXing-JS d'html5-qrcode en conditions difficiles. `numOfWorkers: 0`
     (décodage thread principal, robuste hors-ligne).
   - Le navigateur recommandé aux bibliothécaires reste **Chrome Android**.

4. **Fiabilité du résultat** (commune aux 2 moteurs, `handleRead`) :
   - **EAN-13 uniquement** (`formatsToSupport=[EAN_13]` / `readers:["ean_reader"]`) —
     désactiver ITF/CODE_128/QR élimine les lectures parasites (ex. un ITF de
     20 chiffres décodé à tort en faux ISBN).
   - **Clé de contrôle EAN-13 valide** + **préfixe plausible** `290/291/978/979`
     (Ofelia exemplaire/carte, ISBN) — un chiffre mal lu casse l'un ou l'autre.
   - **Consensus** : 2 lectures identiques d'affilée avant acceptation.
   - **Haute résolution** caméra (`videoConstraints` / `constraints` 1920×1080)
     → petits codes nets, décodage rapide.

5. **Ghost-click mobile** — cf. section précédente (`DISMISS_GUARD_MS = 600`).

### ISBN-10

Un ISBN-10 (10 chiffres) **n'existe pas comme code-barres** : les livres (même
anciens) portent un **EAN-13 « Bookland » `978…`**, qui est reconnu. Un ISBN-10
imprimé en texte seul se saisit à la main (le champ l'accepte ;
`looks_like_isbn10` valide sa clé mod-11). La caméra ne lit donc que de l'EAN-13,
ce qui couvre tous les codes-barres réellement présents sur les livres.

## Routage notice / membre (inchangé, déjà en place)

À la détection d'un code, `BibliOfelia.scan.applyResult(btn, {value})` :

- **Bouton dashboard** (`data-scan-dispatch-url="{% url 'core:search' %}"`) →
  redirige vers `core:search?q=<code>`. `global_search` (`apps/core/views.py:94`)
  + `classify_query` (`apps/core/search.py`) aiguillent : `290…` → **fiche
  notice** (`catalog:record_detail`), `291…` → **fiche membre**
  (`members:detail`), ISBN → notice, texte → liste catalogue.
- **Boutons prêt/retour + recherches catalogue/membres** (`data-scan-target`
  + `data-scan-autosubmit`) → remplissent le champ et soumettent le formulaire
  courant (`input[name=card]`, `input[name=ean]`, ou `input[name=q]`).
- **Champ ISBN du formulaire notice** (`data-scan-target="input[name=isbn_13]"`,
  sans autosubmit) → remplit l'ISBN, le bibliothécaire clique « Récupérer ».

Aucune modification serveur n'a été nécessaire : toute la logique de routage
préexistait (FEAT-023).

## Nouveaux boutons scan (demande Val)

Petit bouton scan rond (icône code-barres, fond burgundy, diamètre aligné sur
la hauteur de l'input via `.scan-inline-btn` : `align-self:stretch` +
`aspect-ratio:1`) ajouté à côté de chaque champ de saisie de code :

| Page | Champ | kind | Comportement |
|---|---|---|---|
| `catalog/record_list.html` | recherche `input[name=q]` (ISBN / code Ofelia) | auto | remplit + submit (recherche catalogue) |
| `members/member_list.html` | recherche `input[name=q]` (n° de carte) | card | remplit + submit (recherche membre) |
| `catalog/_record_form.html` | `input[name=isbn_13]` (ISBN-13) | book | remplit le champ |

Les boutons prêt/retour existaient déjà (FEAT-023), inchangés.

## Layout dashboard (demande Val)

La bannière « Scanner » et la barre de recherche globale sont **remontées en
haut** du dashboard (juste sous la topbar, après le « Bonjour », **au-dessus des
tuiles**). Ordre : greeting → scan → recherche → tuiles → notifications → KPIs…

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `static/js/scan-handoff.js` | **Réécrit** : retrait complet OfeliaScan (handoff, deep-link, polling, WeakMap…). Caméra = unique chemin ; échec → `showCameraError` (raison traduite + saisie manuelle, détail brut en `console.warn`). Conserve `applyResult`, `setBusy`, `flashMessage`, `cameraSupportInfo`. |
| `static/js/scan-camera.js` | **Réécrit** : double moteur html5-qrcode (BarcodeDetector) / QuaggaJS ; URL libs depuis `#scan-camera-config` ; `primeCameraPermission()` iOS ; garde ghost-click ; `handleRead` (EAN-13 + clé + préfixe + consensus) ; haute résolution. |
| `static/js/quagga.min.js` | **Nouveau** — @ericblade/quagga2 v1.8.4 vendoré local (MIT, 143 Ko, build-time only). |
| `templates/base.html` | Suppression `#scan-handoff-config`. Ajout `#scan-camera-config` (`libUrl`+`quaggaUrl`) et 9 chaînes d'erreur dans `#scan-mode-i18n`. |
| `static/css/ofelia.css` | Ajout `.scan-inline-btn` (cercle plein, hauteur = input). |
| `templates/core/dashboard.html` | Scan + recherche remontés au-dessus des tuiles. |
| `templates/catalog/record_list.html`, `members/member_list.html`, `catalog/_record_form.html` | Petit bouton scan inline à côté du champ code. |

Endpoints serveur `/scan-handoff[/{token}]` (FEAT-023) **laissés en place** mais
plus appelés par le site ; leur retrait (migrations, modèle `ScanHandoff`) est
hors périmètre.

## i18n

9 chaînes d'erreur dans `#scan-mode-i18n` + libellés des nouveaux boutons
(`Scanner le code-barres`, `Scanner la carte` — déjà existants). Traductions
EN/ES/MG via `scripts/translations_sprint16.py`. Gate `scripts/i18n_check.py` → 0.

## Sécurité

- Décodage 100 % local (BarcodeDetector natif, ZXing-JS ou QuaggaJS) — aucune
  image caméra envoyée au serveur.
- `MediaStream` arrêté (`stop()`) à la détection ou au cancel.
- Aucun nouvel endpoint, aucune migration.

## Vérification

1. `python scripts/i18n_check.py` → 0.
2. `pytest` (non-régression — aucun test backend impacté).
3. Déploiement Pi : rebuild Docker (templates/JS embarqués au build, cf.
   `project_pi_templates_baked`).
4. Test Val (**HTTPS externe**), validé 2026-05-30 :
   - Chrome Android : scan livre → notice, carte → membre, rapide et fiable.
   - Firefox Android & Safari iOS : fonctionnel via QuaggaJS (moins rapide que
     Chrome — limite navigateur, pas de `BarcodeDetector`).
   - Boutons scan catalogue / membres / champ ISBN OK.
   - Refus de permission → message d'erreur clair.

## Hors périmètre

- HTTPS local sur la box (pour la caméra en LAN HTTP) — chantier nginx/cert keebee.
- Retrait du modèle/endpoints `ScanHandoff` côté serveur.
- Catalogage et récolement OfeliaScan — inchangés.
