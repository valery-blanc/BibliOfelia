# FEAT-069 — Affectation en masse directement depuis le catalogue

**Status:** DONE
**Date:** 2026-08-20

## Contexte

Affecter une catégorie ou un emplacement à un lot de notices demande
aujourd'hui trois écrans : cocher, valider, choisir sur une page de
confirmation, revenir. Pour une bibliothécaire qui reclasse un rayon, c'est
trois fois trop.

Demande Val (2026-08-20) : « plus besoin de page supplémentaire pour les
affectations en masse, tout se fait sur la page catalogue ».

## Comportement

La barre d'action qui apparaît dès qu'une case est cochée reçoit des menus
déroulants et un bouton **Affecter**. Chaque menu vaut **« Ne pas modifier »**
par défaut : on ne touche qu'à ce qu'on a explicitement choisi.

- **« X notices sélectionnées »** → menus **Catégorie** et **Emplacement**.
  La catégorie s'applique aux notices, l'emplacement à **tous leurs
  exemplaires** (comportement FEAT-041 conservé).
- **« X exemplaires sélectionnés »** → menu **Provenance**, appliqué aux
  exemplaires cochés.

Répartition voulue par Val : catégorie et emplacement se pilotent depuis la
notice, la provenance depuis l'exemplaire — c'est le niveau auquel chaque
information appartient réellement.

Chaque menu propose aussi une entrée explicite **« — (vider) »**, pour retirer
une affectation sans avoir à passer par chaque fiche.

Les boutons de **suppression en masse** ne changent pas : ils gardent leur page
de confirmation, parce qu'une suppression mérite qu'on relise la liste.

## Spec technique

- `record_bulk_assign` (nouvelle vue POST) remplace les 4 vues
  `record_bulk_assign_category(_confirm)` / `record_bulk_assign_location(_confirm)` :
  lit `category` et `location`, ignore les valeurs `keep`, applique en une
  transaction, renvoie un message récapitulant ce qui a été fait.
- `item_bulk_assign` remplace `item_bulk_assign_provenance(_confirm)`.
- Sentinelle : `""` = vider, `"keep"` = ne pas modifier. Sans sentinelle
  explicite, « ne pas modifier » et « vider » seraient indiscernables.
- Templates supprimés : `record_bulk_assign_category.html`,
  `record_bulk_assign_location.html`, `item_bulk_assign_provenance.html`.
- Le formulaire de la page catalogue poste vers ces vues via `formaction`, comme
  les boutons de suppression.

## Impact sur l'existant

- `apps/catalog/views.py`, `urls.py`.
- `templates/catalog/record_list.html`, `templates/catalog/_item_results.html`.
- Tests `apps/catalog/tests/test_bulk_assign.py` (FEAT-041) réécrits sur la
  nouvelle vue.

## Implémentation

- `record_bulk_assign` (catégorie + emplacement) et `item_bulk_assign`
  (provenance) remplacent les 6 vues précédentes ; 3 templates de confirmation
  supprimés.
- Sentinelle `keep` : `request.POST.get(field, _KEEP)` — et **non**
  `get(field) or _KEEP`. La chaîne vide est un choix explicite (« vider ») ;
  la confondre avec l'absence rendait le vidage impossible (attrapé en test).
- `back_qs` : un champ caché renvoie l'utilisateur sur le catalogue **avec ses
  filtres**, sinon reclasser un rayon oblige à refiltrer après chaque lot.
- CSS `.bulk-assign` (grille responsive dans la barre d'action).
- Tests : `apps/catalog/tests/test_bulk_assign.py` réécrit (19 cas), dont un qui
  vérifie que les anciennes routes de confirmation n'existent plus.
