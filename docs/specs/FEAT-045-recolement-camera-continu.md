# FEAT-045 — Récolement en scan caméra continu

**Status:** IN PROGRESS
**Date:** 2026-05-30
**SPEC:** §6.5

## Contexte

Demande de Val (`temp.txt`, 2026-05-30) : remplacer OfeliaScan par la **caméra
du navigateur** pour le récolement. Le moteur de scan caméra continu (double
moteur html5-qrcode/Quagga, EAN-13 + checksum + préfixe + consensus) est déjà
livré pour les boutons « Scanner » du site (FEAT-044) ; on l'étend en **mode
continu** et on refond le workflow de récolement autour.

Le catalogage caméra fait l'objet d'un sprint séparé (FEAT-046).

**Contrainte connue** : la caméra exige un contexte sécurisé (HTTPS). En LAN
HTTP sur la box, elle ne démarre pas (item ouvert Sprint 16). Décision Val :
coder maintenant, tester sur accès HTTPS, traiter le HTTPS LAN à part. Un champ
de saisie manuelle reste disponible en repli sur la page de rapport.

## Comportement

### `/inventory/new/` — périmètre

- Scope réduit à **Tout le fonds** (défaut) ou **Un emplacement**. Le scope
  **Catégorie est retiré** de l'UI (l'énum `InventoryScope.CATEGORY` et le champ
  `scope_category` restent en base pour ne pas casser les sessions existantes et
  `build_report`, mais ne sont plus proposés).
- Le champ Emplacement est **grisé** tant que le scope est « Tout le fonds » ;
  il devient obligatoire dès qu'on choisit « Un emplacement ».
- Le bouton **« Lancer l'inventaire »** crée la session (statut `open`) et
  redirige vers `/inventory/<pk>/report/?scan=1`, où la caméra peut démarrer
  d'un tap (geste utilisateur requis par iOS/getUserMedia).

### `/inventory/<pk>/report/` — hub de pointage + rapport

La page de rapport devient le **seul** écran de pointage :

- Panneau de scan en tête : bouton **« Lancer l'inventaire »** (si 0 pointage)
  / **« Continuer l'inventaire »** (si ≥ 1 pointage), classe `.js-scan-inventory`.
  Au clic → caméra en **mode continu** : le viseur reste ouvert, chaque code
  Ofelia confirmé (checksum + préfixe + consensus 2 lectures) est envoyé au
  serveur, un bip + un compteur live confirment le pointage, puis le scan
  reprend. Bouton **« Terminer »** pour fermer le viseur.
- Compteur live « X pointés / Y attendus » + liste des derniers scans
  (reconnu / déjà pointé / inconnu du catalogue).
- Champ de **saisie manuelle** d'un code (repli hors caméra), même endpoint.
- À la fermeture du viseur, la page se recharge pour rafraîchir les tableaux de
  divergences (présents / manquants / hors périmètre / inconnus).
- `?scan=1` met le bouton en évidence (pas d'ouverture automatique).

Un code scanné **doit appartenir au catalogue** pour être validé (pas d'ajout
d'exemplaire). Un code inconnu est tout de même enregistré et remonte dans
« Codes inconnus du système » du rapport, mais le feedback live le signale.

### Suppression de `/inventory/<pk>/`

La page de détail (`session_detail`) et son formulaire de pointage manuel
unitaire sont **supprimés**. Toutes les redirections (`create`, `reopen`)
pointent désormais vers `report`. La liste des sessions ouvre les sessions en
cours sur `report`.

## Spec technique

### Endpoint de pointage (JSON)

`POST /inventory/<pk>/scan/` (`inventory:add_scan`, librarian/superadmin) —
body `ean=<code>` + header `X-CSRFToken`. Réponse JSON :

```json
{
  "ok": true,
  "created": true,
  "known": true,
  "ean": "2900000000017",
  "item": {"internal_id": "OFL-...", "title": "…", "location_code": "A1"},
  "counts": {"expected": 120, "scanned": 47}
}
```

- `created=false` si l'EAN était déjà pointé dans la session (idempotent via la
  contrainte `unique(session, ean13)` existante).
- `known=false` si l'EAN ne matche aucun `Item` (item = null).
- Refuse si la session n'est pas `open` (HTTP 409).

### Mode continu du scanner (`static/js/scan-camera.js`)

`openCamera(btn, opts)` accepte `opts.continuous=true` + `opts.onCode(value)` :
après une lecture confirmée, au lieu de fermer le modal, on émet `onCode`, on
joue un bip (WebAudio), on incrémente un compteur dans le viseur, on applique un
**cooldown** (~1,8 s) puis on réarme le consensus pour la lecture suivante. Le
serveur étant idempotent, un même livre tenu en vue ne crée pas de doublon. En
mode continu le bouton « Annuler » devient « Terminer ».

### Contrôleur de page (`static/js/scan-inventory.js`)

Chargé uniquement sur `session_report.html` (via `extra_head`). Câble le bouton
`.js-scan-inventory` → `BibliOfelia.scan.openCamera(btn, {continuous, onCode})`,
poste chaque code à l'endpoint, met à jour le compteur live + la liste des
derniers scans, gère le repli saisie manuelle, et recharge la page à la
fermeture du viseur. Config (URL endpoint, csrfToken, i18n) injectée en JSON.

## Impact sur l'existant

- `apps/inventory/forms.py` : `scope_type` limité à ALL/LOCATION, `scope_category`
  retiré des champs, `clean()` simplifié.
- `apps/inventory/views.py` : `add_scan` → JSON ; `session_create`/`session_reopen`
  redirigent vers `report` ; suppression de `session_detail`.
- `apps/inventory/urls.py` : suppression de la route `detail`.
- `templates/inventory/session_list.html` : sessions ouvertes → `report`.
- `templates/inventory/session_form.html` : sous-titre sans OfeliaScan + JS
  grise/active l'emplacement.
- `templates/inventory/session_report.html` : panneau de scan + compteurs live +
  saisie manuelle + chargement `scan-inventory.js`.
- `templates/inventory/session_detail.html` : **supprimé**.
- `static/js/scan-camera.js` : mode continu.
- `static/js/scan-inventory.js` : **nouveau**.
- `templates/base.html` : chaînes i18n du mode continu (« Terminer », compteur).
- Aucune migration (modèle inchangé).

## Itération 2 (retours Val, test Pi 2026-05-30)

- **Dé-duplication par code** : set client `seen` (pré-rempli des EAN déjà en
  base, donc le « Continuer » en tient compte) → re-présenter un exemplaire déjà
  pointé est ignoré en silence (plus de doublons dans la liste, compteur =
  nombre réel). Les codes Ofelia étant **par exemplaire**, deux copies d'un même
  titre restent deux scans distincts légitimes.
- **Bip + vibration** (`navigator.vibrate`) uniquement sur une nouvelle
  trouvaille. `scan-camera.js` n'émet plus de feedback automatique en mode
  continu : il appelle `onCode` ; le contrôleur fournit le feedback via
  `BibliOfelia.scan.continuousFeedback({count, label})`.
- **« exemplaire N »** dans le viseur : l'endpoint renvoie `copy_index` (rang de
  l'exemplaire de la notice pointé dans la session) ; label
  « Titre — Auteur · exemplaire N ». Cooldown abaissé 1,8 s → 0,8 s.
- **Rapport refait** : `build_report` ajoute `by_record` (notices triées
  auteur/titre, chaque code Ofelia marqué `found`). Le template remplace la table
  « manquants » (avec statut + « Marquer perdu ») par une liste **par notice**
  avec pastilles vert (trouvé) / rouge (manquant). Vue/URL/test
  `resolve_missing` **supprimés**.

## Itération 3 (retour Val — plusieurs codes dans le champ)

Surligner précisément le code trouvé n'est pas fiable à travers les deux moteurs
(coordonnées non exposées uniformément). On restreint donc la **zone de
décodage à une bande centrale (~1/4 de hauteur)** : un seul code-barres y tient
→ pas d'ambiguïté. `qrbox` (html5-qrcode, ombrage intégré) + `inputStream.area`
top/bottom 37 % (Quagga, + guide `.scan-camera-band` : bande claire, haut/bas
assombris par un grand `box-shadow`). Réduire seulement l'affichage ne
suffirait pas (les moteurs décodent le flux complet, pas l'image rognée).

## i18n

Nouvelles chaînes EN/ES/MG via `scripts/translations_sprint18.py` + gate
`scripts/i18n_check.py` → 0.
