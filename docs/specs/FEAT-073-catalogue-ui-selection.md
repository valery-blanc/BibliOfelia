# FEAT-073 — Catalogue : deux boutons de recherche, sélection étendue, provenance lisible

**Status:** DONE
**Date:** 2026-08-21

## Contexte

Retours de test Val (2026-08-21) sur la page catalogue livrée en FEAT-064/069 :

1. La case **« Chercher les exemplaires »** oblige à comprendre qu'il faut
   cocher *puis* filtrer. Deux boutons disent directement ce qu'on obtient.
2. « Tout cocher » ne coche que la **page courante** (25 lignes), sans le dire.
   Sur un fonds de 900 exemplaires, croire qu'on a tout sélectionné avant une
   suppression est un piège.
3. Le filtre et les colonnes affichent le **code** de la provenance (`BM-GE`),
   alors que le nom complet (« Prêt Bibliothèque de Genève ») est ce qui parle.

## Comportement

### Deux boutons au lieu d'une case

La barre de filtres se termine par **« Rechercher des notices »** et
**« Rechercher des exemplaires »**. Les deux soumettent le même formulaire avec
les mêmes filtres ; seul le mode de résultat change.

Le bouton du mode courant est mis en avant, l'autre reste discret : on voit
d'un coup d'œil ce qu'on est en train de regarder. **Sans clic, rien ne change**
— arriver sur la page affiche toujours les notices, sans filtre.

### Deux cases « tout sélectionner »

Au-dessus de la liste, deux cases :

- **Sélectionner les résultats visibles** — les lignes de la page courante ;
- **Sélectionner tous les résultats** — l'intégralité de la recherche, pages
  suivantes comprises. Le libellé annonce le nombre exact (« Sélectionner les
  912 résultats »).

Cocher l'une décoche l'autre : ce sont deux intentions différentes, pas deux
niveaux qui s'additionnent.

Quand « tous les résultats » est coché, l'action ne porte plus sur des cases
mais sur **la recherche elle-même** : le formulaire transmet les filtres
courants et le serveur reconstruit le même queryset. La barre d'action le dit
explicitement (« 912 résultats de la recherche »), et la page de confirmation de
suppression rappelle le nombre avant de valider.

### Provenance en toutes lettres

Le filtre, la colonne du mode exemplaire, le menu d'affectation et les pages de
confirmation affichent le **nom complet** de la provenance, et lui seul :
répéter le code devant n'allongeait que les menus et les colonnes. Le code
reste la clé de saisie (colonne `PROVENANCE` de l'import Excel) et le repli
d'affichage quand aucun nom n'a été renseigné.

## Spec technique

- `record_list.html` : `<button name="mode" value="records">` et
  `value="items">` remplacent la case à cocher. `items_mode` reste piloté par
  `request.GET["mode"]`, inchangé côté vue.
- `select_all` : champ caché posé à `1` par la case « tous les résultats ». Les
  vues d'action (`record_bulk_assign`, `item_bulk_assign`, `*_bulk_delete*`)
  appellent `_selected_pks(request)`, qui renvoie soit les `ids` cochés, soit
  **le queryset filtré complet** reconstruit à partir des filtres transmis.
- Les filtres voyagent dans le POST (`back_qs`, déjà présent depuis FEAT-069) :
  la vue les relit avec `QueryDict` et réapplique `filtered_records()` /
  `filtered_items()`, extraits de `record_list` pour être réutilisables.
- `Provenance.__str__` est déjà « code — label » ; les templates passent de
  `{{ prov.code }}` à `{{ prov }}`.

## Impact sur l'existant

- `apps/catalog/views.py` (extraction des filtres, `_selected_pks`),
  `templates/catalog/record_list.html`, `_item_results.html`,
  `item_bulk_delete.html`, `record_bulk_delete.html`.
- `templates/catalog/provenance_list.html` (déjà en toutes lettres, vérifié).

## Implémentation

- `filtered_records()` / `filtered_items()` extraites de `record_list` : les
  actions de masse reconstruisent **exactement** la même recherche. Sans cette
  extraction, « sélectionner tous les résultats » n'aurait pu porter que sur la
  page visible.
- `_selected_pks(request, kind)` : `ids` cochés, ou tout le queryset filtré si
  `select_all=1`. Les filtres voyagent dans `back_qs`, relu en `QueryDict`.
- `templates/catalog/_select_all.html` : partial partagé par les deux modes. La
  case « tous les résultats » n'apparaît qu'à partir de 2 pages — sinon elle
  ferait doublon. Cocher l'une décoche l'autre, et cocher une ligne annule la
  sélection étendue : ce sont des intentions distinctes, pas des niveaux qui
  s'additionnent.
- La barre d'action affiche « N résultats de la recherche » au lieu du compteur
  de cases quand la sélection est étendue.
- **Pages de confirmation** : les identifiants sont réinjectés en clair plutôt
  que de rejouer la recherche à la validation — ce qui a été confirmé est
  exactement ce qui sera supprimé, même si le catalogue bouge entre-temps. Seul
  l'**affichage** est plafonné (`PREVIEW_LIMIT = 100`), avec une ligne « … et N
  autres non affichés ici ».
- Provenance : `Provenance.__str__` renvoie `label or code`, et `{{ prov }}`
  remplace `{{ prov.code }}` dans le filtre, les colonnes, les menus
  d'affectation et les confirmations.
- Les deux boutons de mode sont groupés dans `.search-modes` (ils restaient
  séparés quand la barre de filtres passait à la ligne) et portent deux fonds
  pleins de la charte — bordeaux pour le mode courant, olive pour l'autre.
  Un `btn--ghost` s'y fondait dans le fond de page.
- Tests : `apps/catalog/tests/test_catalog_selection.py` (19 cas).
