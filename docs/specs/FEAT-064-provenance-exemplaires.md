# FEAT-064 — Provenance des exemplaires + recherche par exemplaire

**Status:** DONE
**Date:** 2026-08-19

## Contexte

Une partie du fonds n'appartient pas à la bibliothèque : livres prêtés par une
autre bibliothèque, dépôts temporaires, dons fléchés. Le jour où il faut les
rendre, il faut pouvoir retrouver **exactement** les exemplaires concernés et
les sortir du catalogue en un geste.

Le cas difficile est le fonds mélangé : une même notice peut avoir un
exemplaire acheté par Ofelia **et** un exemplaire prêté par une autre
bibliothèque. Une recherche qui ne renvoie que des notices ne sait pas montrer
cette différence — d'où la recherche par exemplaire demandée en même temps.

## Comportement

### Le champ provenance

Liste gérée (décision Val 2026-08-19), pas de texte libre : les provenances
sont des objets nommés, comme les emplacements. Écran
**Catalogue → Provenances** (rôle bibliothécaire) : liste avec le nombre
d'exemplaires rattachés, création, modification, suppression.

Une provenance encore utilisée par au moins un exemplaire **ne peut pas être
supprimée** : le message indique combien d'exemplaires la portent et invite à
les traiter d'abord. C'est le garde-fou qui évite d'effacer par erreur la
seule trace de « à qui appartient ce livre ».

Sur l'exemplaire : champ facultatif, modifiable à l'unité comme en masse.

### Affectation en masse

- **Au catalogage** : le lot de scan porte une *provenance par défaut*
  (à côté de la catégorie et de l'emplacement par défaut), appliquée à tous
  les exemplaires créés par le lot.
- **À l'import Excel** : colonne `PROVENANCE` (code ou libellé). Inconnue →
  avertissement `PROVENANCE_UNKNOWN`, l'import continue sans elle.
- **Depuis le catalogue** : sélection d'exemplaires → « Affecter une
  provenance ».

### Recherche par exemplaire

Case à cocher **« Chercher les exemplaires »** dans la barre de filtres du
catalogue. Cochée :

- une ligne de résultat **par exemplaire** (3 exemplaires d'une même notice =
  3 lignes) ;
- la colonne « Ex. » (nombre d'exemplaires) disparaît, remplacée par
  **Code Ofelia**, **Code Ofelia externe** et **Provenance** ;
- le filtre provenance s'applique aux exemplaires eux-mêmes ;
- les actions de masse portent sur les exemplaires cochés : « Affecter une
  provenance » et « Supprimer les exemplaires » (superadmin).

Décochée, le catalogue se comporte exactement comme avant (une ligne par
notice, colonne « Ex. »). Le filtre provenance reste utilisable : il retient
alors les notices ayant **au moins un** exemplaire de cette provenance.

### Rendre les livres d'une autre bibliothèque

Le mode exemplaire est le chemin prévu (décision Val 2026-08-19) : filtrer sur
la provenance, tout cocher, supprimer. On voit la liste avant de valider, et la
suppression réutilise le chemin FEAT-027 déjà éprouvé — prêts en cours passés
en `LOST`, réservations annulées, codes Ofelia mis en tombstone (FEAT-043) donc
jamais réattribués.

## Spec technique

- Modèle `Provenance` (app `catalog`) : `code` (20, unique), `label` (120),
  `notes`. `__str__` = `« code — label »`.
- `Item.provenance` — FK nullable, `on_delete=PROTECT` (adossé au garde-fou
  ci-dessus), `related_name="items"`.
- `ScanSession.default_provenance` — FK nullable `SET_NULL`, appliquée dans
  `apps/api/services.py:_add_copies`.
- `catalog.views.record_list` : paramètre `mode=items` → requête sur `Item`
  (`select_related("record", "location", "provenance")`), pagination sur les
  exemplaires. La recherche plein texte reste indexée sur les notices : en mode
  exemplaire on filtre `record_id__in=<ids FTS>`.
- Suppression en masse d'exemplaires : `catalog.views.item_bulk_delete_confirm`
  / `item_bulk_delete`, réservées à `SUPERADMIN`, réutilisant la logique de
  `item_delete`.

## Impact sur l'existant

- `apps/catalog/models.py` (+ migration), `forms.py`, `views.py`, `urls.py`,
  `admin.py`.
- `apps/api/services.py` (`_add_copies`), `apps/catalog/excel_catalog.py`.
- Templates : `catalog/record_list.html` (les deux modes), nouveaux
  `catalog/provenance_list.html`, `provenance_form.html`,
  `provenance_confirm_delete.html`, `item_bulk_delete.html`,
  `item_bulk_assign_provenance.html` ; `catalog/record_detail.html`,
  `catalog/scan_session_form.html`.

## Implémentation

- Modèle `Provenance` (code, label, notes) + `Item.provenance` (PROTECT) +
  `ScanSession.default_provenance` (SET_NULL) — migration `catalog/0014`.
- Écran **Catalogue → Provenances** (`provenance_list/create/edit/delete`) :
  le compteur d'exemplaires est un lien vers la recherche filtrée ; la
  suppression est refusée tant qu'un exemplaire porte la provenance, avec un
  bouton « Voir ces exemplaires ».
- Provenance du lot appliquée dans `api.services._add_copies` ; colonne Excel
  `PROVENANCE` résolue par code **ou** libellé (`PROVENANCE_UNKNOWN` sinon).
- `catalog.views.record_list` : `mode=items` bascule la requête sur `Item`.
  Emplacement et provenance filtrent la ligne affichée en mode exemplaire, et
  « au moins un exemplaire » en mode notice. Le plein texte reste indexé sur
  les notices (`record_id__in`).
- `templates/catalog/_item_results.html` : desktop + mobile, cases à cocher pour
  les bibliothécaires, lecture seule sinon.
- Actions de masse : `item_bulk_assign_provenance` (bibliothécaire) et
  `item_bulk_delete` (superadmin) — prêts en cours clos en `LOST`, réservations
  servies annulées, historique effacé, tombstones FEAT-043 posés avec
  `reason=bulk_delete`.
- Tests : `apps/catalog/tests/test_provenance.py` (26).
