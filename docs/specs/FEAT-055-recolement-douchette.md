# FEAT-055 — Récolement (inventaire) à la douchette USB + guide catalogage douchette

**Status:** EN TEST
**Date:** 2026-07-09

## Context

FEAT-054 a introduit le support des **douchettes USB** (lecteurs de code-barres en
mode clavier HID) via un wedge global (`static/js/scan-wedge.js`) et une page
dédiée « Catalogage par douchette ». Le périmètre couvrait **prêt / retour /
consultation** (via `data-wedge-primary`) et le **catalogage douchette**, mais
**pas le récolement** (page rapport d'inventaire).

Deux manques constatés (questions Val, 2026-07-09) :

1. **Le récolement ne fonctionne pas à la douchette — pire, il est cassé.** Sur la
   page rapport (`/inventory/<pk>/report/`), le champ de saisie manuelle
   (`inv-manual-form input[name=ean]`) n'avait **pas** `data-wedge-primary`. Le
   wedge global, ne trouvant aucun champ primaire sur cette page, appliquait son
   **fallback** : navigation vers `core:search?q=<code>`. Résultat : un scan
   douchette **quittait** la page de récolement (vers la recherche) et
   n'enregistrait **jamais** le pointage. Seules la caméra et la frappe clavier
   humaine lente fonctionnaient.
2. **Le catalogage douchette (FEAT-054) n'était pas documenté** dans le guide
   utilisateur (`docs/user-guide/`) — la tuile existait dans l'app mais aucune
   page ne l'expliquait.

## Behavior

### Récolement à la douchette

Le champ de saisie manuelle de la page rapport porte désormais
`data-wedge-primary autofocus`. Comportement :

- Une douchette scanne un code Ofelia (290) → le wedge reconnaît la rafale HID,
  **remplit ce champ** et **soumet le formulaire** `inv-manual-form`.
- Le handler `submit` de `scan-inventory.js` (déjà existant) intercepte
  (`preventDefault`), lit la valeur, appelle `handleCode()` → **POST
  `inventory:add_scan`** (JSON), met à jour le **compteur** et la **liste live**,
  vide le champ et le re-focus. **La page n'est jamais quittée.**
- **Aucun clic requis** (l'écoute wedge est globale, phase de capture).
- **Dé-duplication** : réutilise le `Set` client de `scan-inventory.js` (codes
  déjà pointés ignorés en silence).
- **Coexistence caméra** : quand le modal caméra est ouvert
  (`body.scan-camera-open`, bouton « Lancer l'inventaire »), le wedge **se
  retire** → pas de double pointage. La caméra reste le mode par défaut ; la
  douchette est un mode parallèle (utile en LAN HTTP où la caméra est indisponible
  faute de HTTPS).
- **Réassignation automatique (FEAT-033) inchangée** : le backend
  (`inventory:add_scan`) applique la même logique quel que soit le mode d'entrée
  (caméra / douchette / manuel).

### Guide utilisateur

- Nouvelle page **« Cataloguer avec la douchette »**
  (`docs/user-guide/docs/inventaire/catalogage-douchette.md`) × 4 langues (FR/EN/
  ES/MG), ajoutée à la nav MkDocs (rubrique Catalogue) + `nav_translations`.
- Section **« Avec une douchette USB »** ajoutée à `inventaire/recolement.md`
  × 4 langues.

## Technical spec

- `templates/inventory/session_report.html` : ajout de `data-wedge-primary
  autofocus` sur `#inv-manual-form input[name=ean]`. **Seul changement de code.**
- Aucune modification JS : `scan-wedge.js` (routage `findPrimaryTarget` →
  `input[data-wedge-primary]`) et `scan-inventory.js` (handler `inv-manual-form`
  `submit` → `handleCode`) fonctionnent tels quels. Le wedge remplit + `requestSubmit()` ;
  le handler AJAX prend le relais.
- Aucune migration, **aucune nouvelle chaîne d'app** (attribut HTML seul) → gate
  `i18n_check.py` reste à 0.

## Impact on existing code

- `templates/inventory/session_report.html` (1 attribut)
- `docs/specs/SPEC_BIBLIOFELIA.md` §6.5 + en-tête
- `docs/user-guide/docs/inventaire/catalogage-douchette.{,en,es,mg}.md` (nouveau)
- `docs/user-guide/docs/inventaire/recolement.{,en,es,mg}.md` (section douchette)
- `docs/user-guide/mkdocs.yml` (nav + nav_translations ×3)
- `docs/tasks/TASKS.md`

## Tests

- Le pointage à la douchette réutilise le chemin `inventory:add_scan` déjà couvert
  par `apps/inventory/tests/test_views.py` / `test_services.py` (POST manuel =
  même endpoint). Pas de nouveau backend à tester. Vérification fonctionnelle :
  scan douchette sur la page rapport → l'exemplaire est pointé, la page ne bouge
  pas, le compteur monte.
