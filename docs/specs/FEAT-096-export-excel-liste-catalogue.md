# FEAT-096 — Export Excel de la liste catalogue

**Status:** DONE
**Date:** 2026-09-18
**Sprint:** 37

## Context

La page Catalogue sait déjà filtrer notices et exemplaires (FEAT-073,
FEAT-095). L'export Excel existant (FEAT-078) sort **tout** le fonds, avec
toutes les colonnes d'import, depuis Avancé → Catalogage Excel. Pour
travailler sur **la recherche en cours** (un rayon, une classification, un
fonds prêté), il n'y avait pas de bouton sur la liste.

Val, 2026-09-18 : *« page catalogue, rajouter un bouton export excel qui
exporte en excel la liste des notice ou des exemplaires qui est affichée
avec en plus des colonnes affichées la colonne emplacement. »*

## Behavior

- Un bouton **Export Excel** à côté du compteur de résultats, visible dès
  qu'il y a au moins une ligne.
- Le fichier reprend **le mode et les filtres courants** (texte, classification,
  type, langue, emplacement(s), provenance, tag). La pagination est ignorée :
  toutes les pages de la recherche sortent, pas seulement les 25 visibles.
- **Mode notices** : une ligne par notice. Colonnes = Titre, Auteur(s),
  Classification, Ex., **Emplacement**.
- **Mode exemplaires** : une ligne par exemplaire. Colonnes = Titre,
  Auteur(s), Classification, Code Ofelia, Code Ofelia externe, Provenance,
  **Emplacement**.
- **Emplacement** n'est pas une colonne de l'écran ; il est **ajouté** dans
  le fichier. En mode notice, les codes des exemplaires de la fiche sont
  joints (`A1, B2`). En mode exemplaire, c'est le rayon de cette ligne.
- Rôles : les mêmes que la page (`librarian`, `superadmin`, `readonly`).
- Nom du fichier : `catalogue-notices-AAAA-MM-JJ.xlsx` ou
  `catalogue-exemplaires-AAAA-MM-JJ.xlsx`.
- Ce n'est **pas** le fichier d'aller-retour de FEAT-078/079. Les en-têtes
  sont les libellés de l'écran, traduits.

## Technical spec

- `apps/catalog/list_export.py` — construction du classeur (`write_only`,
  freeze_panes, largeurs).
- Vue `catalog:catalog_list_export` (`GET /catalog/export.xlsx`), mêmes
  query params que `record_list`.
- `filtered_records()` / `filtered_items()` réutilisés tels quels.
- Bouton dans `templates/catalog/record_list.html` (lien GET + `base_qs`).

## Impact on existing code

Aucun changement à FEAT-078, à l'import, ni aux colonnes affichées à
l'écran.

## Implementation

- `apps/catalog/list_export.py` — classeur `write_only`, mêmes filtres que
  `record_list`, emplacement joint en mode notice.
- Vue `catalog:catalog_list_export`, URL `catalog/export.xlsx`.
- Bouton dans `templates/catalog/record_list.html` (compteur + lien `base_qs`).
- Tests : `apps/catalog/tests/test_list_export.py` (10).
- i18n : `scripts/translations_sprint37.py` — gate 0.
- Guide : `docs/user-guide/docs/catalogue/recherche.md` × 4 langues.

Déployé 2026-09-18 : Fez sanjuan + grand-saconnex (healthy), image de
secours Avignon, Box Canaima (healthy). Guide sur docs.bibliofelia.org.
Validé Val le 2026-09-18.
