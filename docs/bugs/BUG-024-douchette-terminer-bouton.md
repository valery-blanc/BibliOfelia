# BUG-024 — Bouton « Terminer et voir le lot » inutile après rechargement

**Status:** FIXED
**Date:** 2026-08-03

## Symptôme

Page `/fr/catalog/scan/<pk>/` (catalogage douchette). On scanne, on clique sur
« Terminer et voir le lot » : la page se recharge et affiche bien la liste des
livres modifiables par lot — mais le bouton « Terminer et voir le lot » est
toujours là, désormais sans objet (il recharge une page déjà à jour).

## Reproduction

1. Avancé → Inventaire → Catalogage par douchette → démarrer un lot.
2. Scanner un livre.
3. Cliquer « Terminer et voir le lot ».
4. Le tableau apparaît **et** le bouton reste affiché au-dessus.

## Cause racine

Le bouton a été ajouté à FEAT-054 itér. 2 : en mode douchette la page ne se
recharge jamais (les scans arrivent en AJAX sur `catalog:scan_add`), donc le
tableau rendu par le serveur restait vide. Le bouton est un simple lien de
rechargement — mais il était rendu **inconditionnellement**, y compris quand la
liste venait tout juste d'être rendue.

## Fix appliqué

- `templates/catalog/scan_session.html` : le bloc est enveloppé dans
  `<div id="cat-refresh-wrap" hidden>` dès que le serveur a rendu au moins une
  ligne — le bouton n'apparaît donc plus sur une liste à jour.
- `static/js/scan-cataloging.js` : `revealRefresh()` retire l'attribut `hidden`
  au premier scan effectif (`created` / `incremented`). On garde ainsi le moyen
  de rafraîchir dès que la liste redevient périmée, sans l'afficher pour rien.

Un scan `ignored` (double-lecture) ou `rejected` (code 290/291) ne réaffiche pas
le bouton : la liste n'a pas changé.

## Vérification

`apps/catalog/tests/test_cataloging.py::test_douchette_hub_hides_refresh_button_when_list_is_fresh`
(lot vide → bouton visible ; après un scan → `hidden`).

## Section spec impactée

`SPEC_BIBLIOFELIA.md` §6.1 (catalogage à la douchette).
