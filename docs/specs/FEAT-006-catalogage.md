# FEAT-006 — Catalogage

Statut : **DONE — tests écrits, non exécutés** (2026-05-21)
Sprint : 2
Task : #6 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.1

## Périmètre

### Notices (`apps/catalog/`)

- `record_list` — liste paginée + recherche FTS5 + filtres catégorie / langue /
  type de document. Tri par pertinence si recherche, sinon par titre.
- `record_detail` — métadonnées, exemplaires, accès réservation.
- `record_create` / `record_edit` — `BibliographicRecordForm`. Auteurs saisis
  en texte libre (séparés par `;`) → `get_or_create` d'`Author`. Champs avancés
  repliables (`<details>` piloté par `always_show_advanced`).
- `record_delete` — suppression bloquée si exemplaires actifs, sinon suppression
  réelle (la notice CASCADE ses exemplaires).

### Lookup ISBN (`apps/catalog/openlibrary.py`)

`isbn_lookup` : endpoint HTMX. Le bouton « Récupérer » d'un formulaire notice
appelle OpenLibrary (`httpx`, timeout configurable) et renvoie le formulaire
pré-rempli. Échec réseau → message + saisie manuelle.

### Exemplaires

- `item_create` — `ItemBulkCreateForm` : création groupée (champ `copies`,
  1 à 20). Chaque exemplaire reçoit `internal_id` + `ean13` (générés par
  `Item.save()`).
- `item_edit` — édition d'un exemplaire.
- `item_discard` — suppression logique : statut → `discarded` (bloqué si prêté
  ou réservé).

## Écarts / décisions

- **Pas de champ `discarded`** : la SPEC §6.1 évoquait un champ booléen ; le
  modèle `Item` (FEAT-002) porte déjà un statut `discarded` dans son enum
  `ItemStatus`. La suppression logique d'exemplaire = passage à ce statut. Pour
  une notice, pas de suppression logique : suppression réelle gardée par
  l'absence d'exemplaires actifs.
- **Import batch OfeliaScan** (§6.1) : hors périmètre — dépend de l'API REST
  (Task #16).
- **Lookup ISBN hors-ligne** : la mise en file d'attente (`pending`) quand la
  box est hors-ligne n'est pas implémentée — dépend de la détection de
  connectivité (§7.3). En v1, échec réseau = saisie manuelle.

## Tests (`apps/catalog/tests/`)

- `test_openlibrary.py` : parsing, erreur réseau, ISBN inconnu/invalide.
- `test_forms.py` : auteurs depuis texte, ISBN vide → NULL, ISBN malformé,
  réutilisation d'auteur, limite `copies`.
- `test_views.py` : liste visible en lecture seule, création interdite en
  lecture seule, création de notice, création groupée d'exemplaires, mise au
  rebut (et blocage si prêté), suppression de notice (et blocage si exemplaires).
