# FEAT-095 — Filtrer par plusieurs emplacements

**Status:** DONE
**Date:** 2026-09-17
**Validé:** 2026-09-17 (Val)

## Context

Le catalogue propose une liste déroulante « Tous emplacements » qui n'accepte
qu'un seul rayon. Pour imprimer les étiquettes d'une salle (A1 et A2, sans
le reste) ou chercher deux rayons à la fois, il faut lancer deux recherches.
Val veut **garder la liste déroulante** et pouvoir y cocher **plusieurs**
emplacements — sans que ça devienne un choix multiple là où on **affecte**
un exemplaire à un rayon.

Règle : **plusieurs emplacements pour une recherche, un seul pour une
affectation.**

## Inventory

### Recherche (multi)

| Écran | Aujourd'hui | Après |
|---|---|---|
| Catalogue, barre de filtres | `<select>` unique, « Tous emplacements » | même allure, cases à cocher dans la liste |
| Étiquettes codes Ofelia | champ texte `A1` | même widget que le catalogue |
| Étiquettes de tranche | idem (base commune `_picker_base.html`) | idem |

### Affectation (un seul, inchangé)

- Barre d'action du catalogue (« Affecter » un emplacement aux notices)
- Catalogage caméra / douchette : défaut du lot et « Appliquer aux lignes cochées »
- Formulaire d'exemplaire (créer / modifier)
- Récolement : périmètre « Un emplacement » (cible du relocate)
- Colonne Excel `LOCATION` (une cellule = un code)

## Behavior

- **Aucun emplacement coché** (libellé « Tous emplacements ») : pas de
  filtre, y compris les exemplaires sans rayon.
- **Un ou plusieurs cochés** : union. Une notice passe si **au moins un**
  de ses exemplaires est dans l'un des rayons. Un exemplaire sans rayon
  disparaît.
- Cocher tous les rayons un par un n'est **pas** équivalent à « Tous » :
  les livres sans emplacement restent hors filtre.
- L'ancienne URL d'impression `?location=A1` (code, pas l'id) continue de
  marcher.
- Query string : `?location=3&location=7` (ids). La pagination et
  « tous les résultats » reconstruisent la même recherche.

## Technical spec

- Widget `templates/partials/_location_filter.html` : `<details>` qui
  ressemble à `select.filter-select`, panneau de cases. JS
  `static/js/location-filter.js` : libellé du bouton, « Tous » exclusif,
  fermeture au clic dehors.
- `selected_location_ids(params)` dans `apps/catalog/views.py` :
  `getlist("location")`, ids numériques, repli sur le code (A1).
- `filtered_records` / `filtered_items` : `location_id__in=…`.
- Impression : `_picker_context` utilise le même helper et le même widget.

## Side effects

| Risque | Traitement |
|---|---|
| Affectation multi par accident | les `<select>` d'affectation ne changent pas |
| `params.get("location")` ne voit que la dernière valeur | passer à `getlist` |
| Signet `?location=A1` des étiquettes | le helper accepte encore le code |
| Cases `name="location"` dans le GET et le POST du catalogue | deux formulaires distincts, pas de collision |

## Implementation

- `apps/catalog/location_filter.py` — `selected_location_ids`
- Widget `templates/partials/_location_filter.html` + `static/js/location-filter.js`
  + styles dans `ofelia.css`
- Catalogue et pickers d'étiquettes branchés ; affectations inchangées
- Compteur de résultats au-dessus du tableau (étiquettes, liste des membres),
  comme sur le catalogue. Le bouton de la liste d'emplacements a le même fond
  blanc (`--paper`) que les autres filtres.

