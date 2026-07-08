# FEAT-054 — Support douchette USB (keyboard-wedge global) + catalogage douchette

**Status:** DONE
**Date:** 2026-07-08

## Context

La Box accueille des postes équipés d'une **douchette USB** (lecteur de
code-barres en mode clavier HID). Jusqu'ici, le site ne « comprenait » un scan
douchette que si l'utilisateur avait **cliqué dans un champ** au préalable
(saisie clavier + submit natif). Deux limites remontées par Val (`temp.txt`,
2026-07-08, poste Bruxelles) :

1. une touche de la salve fuit vers le navigateur → **BUG-020** (ouverture
   parasite de la page des téléchargements) ;
2. il faut **cliquer dans un champ** avant de pouvoir scanner.

En complément, Val veut un **catalogage par douchette** : même finalité que le
catalogage par scan caméra (FEAT-046), mais piloté par la douchette du poste qui
affiche BibliOfelia, sans caméra.

## Behavior

### Wedge global (toutes les pages)

Un écouteur clavier au niveau du **document** reconnaît la signature d'un scan
douchette et le traite lui-même :

- **Détection** : une douchette émet des frappes avec des intervalles très
  courts (~1–5 ms/char) et se termine par `Entrée`. On considère « scan » une
  salve dont les frappes sont espacées de moins de `MAX_INTERKEY_MS` (~35 ms),
  d'au moins `MIN_LEN` caractères (≥ 3), terminée par `Entrée`. La frappe
  humaine (intervalles > 35 ms, irrégulière) ne déclenche jamais le wedge.
- **Suppression des fuites** : dès la 2ᵉ frappe rapide, `preventDefault()` en
  phase de capture ; l'`Entrée` terminale est aussi neutralisée. Une fenêtre de
  garde post-scan (~250 ms) avale un éventuel suffixe/CR-LF traînant. → plus
  aucune touche n'atteint un raccourci navigateur (**corrige BUG-020**).
- **Aucun clic requis** : l'écoute étant globale, le scan est capté quel que soit
  l'élément focalisé (répond à la 2ᵉ question de `temp.txt`).

### Routage contextuel du code capté

Le wedge **contrôle entièrement** le code (il ne s'appuie jamais sur la saisie
native dans le champ ; il écrase la valeur du champ cible si besoin) :

1. **Un champ de scan est focalisé** (input texte marqué scan/`data-wedge-primary`)
   ou la page déclare un champ primaire → on **remplit ce champ + submit** son
   formulaire. C'est le cas des pages **Prêt / Retour / Consultation** (le champ
   carte/livre est déjà `autofocus`) : la douchette **alimente le prêt/retour**
   (décision Val), et de la page **Catalogage par douchette** (POST vers
   `scan_add`).
2. **Aucun champ de scan pertinent** → navigation vers `core:search?q=<code>` :
   le serveur (`classify_query`) route vers la **fiche notice** (290 / ISBN /
   977-ISSN) ou la **fiche membre** (291).

Exclusions : `<textarea>`, champs `contenteditable`, champs mot de passe, et
lorsqu'un modal caméra est ouvert → le wedge se met en retrait (comportement
natif). Les raccourcis avec `Ctrl/Alt/Meta` ne sont jamais captés.

### Catalogage par douchette (nouvelle page dédiée)

Nouvelle entrée **Avancé → Inventaire → « Catalogage par douchette »**, parallèle
au « Catalogage scan » (caméra). Réutilise intégralement le backend existant
(`ScanSession` + `scan_add`, FEAT-021/046) :

- création d'une session de catalogage marquée « douchette » ;
- page dédiée : champ de saisie ISBN **autofocus** marqué `data-wedge-primary`,
  liste live des titres détectés (rendu réutilisé de `scan-cataloging.js`),
  bouton « Valider le lot » ; pas de dépendance caméra ;
- chaque code scanné (par la douchette, via le wedge) est POSTé à `scan_add`
  (mêmes règles : created / incremented « exemplaire X » / rejected 290-291).

## Technical spec

- `static/js/scan-wedge.js` — module autonome, chargé partout via `base.html`.
  Constantes `MAX_INTERKEY_MS`, `MIN_LEN`, `POST_SCAN_GUARD_MS`. Config JSON
  injectée (`#scan-wedge-config` : URL `core:search`, seuils). Expose éventuels
  hooks via `window.BibliOfelia.wedge`.
- Routage : réutilise les attributs déclaratifs existants (`data-scan-target`,
  `data-scan-autosubmit`) et un nouveau `data-wedge-primary` posé sur les champs
  scan de lend/return/consultation + page catalogage douchette.
- Coexistence caméra : le wedge se désactive quand le modal caméra
  (`scan-camera.js`) est ouvert (drapeau partagé `window.BibliOfelia`).
- Backend catalogage douchette : nouvelle route `catalog:scan_douchette_*`
  (création + page), réutilise `scan_add`. Discriminant de mode sur `ScanSession`
  (flag/`input_mode`) OU template dédié rendant la même session — choix arrêté à
  l'implémentation (préférence : réutiliser le template de session avec un
  contexte `input_mode="douchette"` pour rester DRY).
- i18n : `scripts/translations_sprint23.py` (EN/ES/MG) + gate `i18n_check.py` → 0.

## Impact on existing code

- `static/js/scan-wedge.js` (nouveau)
- `templates/base.html` (chargement + config)
- `templates/loans/lend.html`, `return.html`, `consultation.html`
  (`data-wedge-primary` sur les champs autofocus)
- `apps/catalog/views.py` + `urls.py` (page catalogage douchette)
- `templates/catalog/` (page/variante douchette) + `templates/core/advanced.html`
  (tuile)
- SPEC §6.1 (scan douchette + routage) + §6.12 (catalogage douchette) + en-tête
- Résout **BUG-020**.

## Implementation notes (DONE — validé Val 2026-07-08)

- `static/js/scan-wedge.js` : écoute `keydown` en **capture** sur `document`.
  Constantes `MAX_INTERKEY_MS=50`, `MIN_LEN=3`, `GUARD_MS=300`, flush de secours
  `FLUSH_MS=max(60, MAX_INTERKEY+20)`. Ordre du handler (crucial — cf. BUG-020) :
  (1) **fenêtre de garde** post-scan d'abord (avale le `LF` traînant), (2) retrait
  si modal caméra ouvert, (3) terminateur `Entrée`/`Tab` en rafale → dispatch,
  (4) en rafale : `preventDefault`+`stopImmediatePropagation` sur **tout** (chiffres
  + Ctrl-combos), (5) hors rafale : 1er caractère bufferisé sans prévention.
- Modèle : `ScanInputMode` (`mobile`/`camera`/`douchette`) + `ScanSession.input_mode`
  (migration `catalog/0012`, défaut `camera`). API OfeliaScan crée en `mobile`.
- Vues : `_scan_session_create(request, input_mode)` factorisé →
  `scan_session_create` (caméra) + `scan_douchette_create` (douchette) ; `scan_session`
  passe `input_mode` au template. Route `catalog:scan_douchette_create`.
- Templates : `base.html` (config `#scan-wedge-config` + chargement JS) ;
  `lend.html`/`return.html` (`data-wedge-primary` sur les champs autofocus ;
  consultation n'a pas de champ scan → route vers recherche) ; `scan_session.html`
  (mode douchette : bouton caméra masqué, champ `data-wedge-primary autofocus`,
  bouton **« Terminer et voir le lot »** qui recharge la page pour révéler le
  tableau éditable + « Envoyer au catalogue », empty-state mode-aware) ;
  `scan_session_form.html` (titre/sous-titre douchette) ; `advanced.html` (tuile).
- Tests : 3 cas `apps/catalog/tests/test_cataloging.py` (input_mode camera/douchette
  + le hub douchette marque le champ primaire et masque le bouton caméra).
- i18n : `scripts/translations_sprint23.py` (12 chaînes × EN/ES/MG), gate → 0.
- Déployé Box 2026-07-08 (migration `0012`, rebuild, healthy).
