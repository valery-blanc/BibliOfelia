# FEAT-063 — Code Ofelia externe

**Status:** DONE
**Date:** 2026-08-19

## Contexte

Certains livres arrivent avec un code déjà attribué **hors de BibliOfelia** :
étiquette posée par une autre bibliothèque, par un donateur, par un catalogage
antérieur au projet. Recoller une étiquette Ofelia par-dessus est du travail
inutile et fait perdre la traçabilité côté propriétaire du livre.

Demande Val : pouvoir enregistrer ce code sur l'exemplaire et **le saisir ou le
scanner indifféremment du code Ofelia**, partout dans l'application.

## Comportement

### Le champ

`Exemplaire → Code Ofelia externe` : jusqu'à **20 caractères alphanumériques**
(ex. `BCF13298781X`). Facultatif. Unique quand il est renseigné : deux
exemplaires ne peuvent pas porter le même code externe, sinon un scan serait
ambigu. Plusieurs exemplaires sans code externe restent évidemment permis.

Saisie tolérante : espaces, tirets et points sont retirés, les minuscules
passent en majuscules. `bcf-1329 8781x` et `BCF13298781X` sont donc le même
code, à la saisie comme au scan.

### Où on peut le saisir

- Formulaire d'exemplaire (création et modification).
- Import Excel : colonne **`EXTERNAL_CODE`** (alias acceptés :
  `CODE_EXTERNE`, `CODE_OFELIA_EXTERNE`, `OFELIA_EXT`). Une cellule vide
  laisse l'existant intact. Un code déjà pris par un autre exemplaire est
  refusé pour la ligne, avec l'avertissement `EXTERNAL_CODE_DUPLICATE` au
  rapport ; un code trop long ou non alphanumérique donne
  `EXTERNAL_CODE_INVALID`.

### Où on peut le scanner ou le taper

Partout où un code d'exemplaire est attendu :

- barre de recherche globale ;
- recherche du catalogue ;
- prêt et retour ;
- récolement (douchette, caméra, saisie clavier) ;
- API `/api/v1/` (endpoint de résolution d'exemplaire).

Ces codes peuvent être imprimés en code-barres (Code 128 pour de
l'alphanumérique) : la douchette les envoie comme du texte, donc le même
chemin de code les traite.

### Ordre de résolution d'un code saisi

1. code Ofelia (EAN13 préfixe 290) → exemplaire ;
2. **code Ofelia externe** (correspondance exacte après normalisation) ;
3. carte membre (préfixe 291), ISSN (préfixe 977), ISBN ;
4. sinon, recherche plein texte.

Le code Ofelia garde la priorité : un code externe qui ressemblerait à un EAN13
Ofelia ne peut pas détourner un scan.

## Spec technique

- `Item.external_code` — `CharField(max_length=20, blank=True, db_index=True)`,
  chaîne vide quand absent (pas de NULL), avec
  `UniqueConstraint(fields=["external_code"], condition=~Q(external_code=""))` :
  unicité partielle, compatible SQLite.
- `apps/catalog/lookup.py` — `find_item(raw)` : point unique de résolution d'un
  code d'exemplaire, réutilisé par les prêts, le récolement, la recherche et
  l'API. `normalize_external_code(raw)` applique la normalisation ci-dessus.
- `apps/core/search.py` reste sans accès base : la classification de requête ne
  change pas, c'est `find_item` qui consulte la table.
- Import Excel : `EXTERNAL_CODE` rejoint `IMPORT_OVERRIDE_COLUMNS`, appliqué
  aux exemplaires du lot dans `_apply_import_overrides`.

## Impact sur l'existant

- `apps/catalog/models.py`, migration additive.
- `apps/catalog/forms.py` (`ItemForm`, `ItemBulkCreateForm` — en création
  groupée le code externe n'est proposé que pour 1 exemplaire, un code unique
  ne pouvant pas être dupliqué).
- `apps/catalog/lookup.py` (nouveau), `apps/catalog/views.py`,
  `apps/core/views.py`, `apps/loans/views.py`, `apps/inventory/services.py`,
  `apps/api/views.py`.
- `apps/catalog/excel_catalog.py`.
- Templates : `catalog/record_detail.html`, `catalog/item_form.html`,
  `printing/labels_picker.html`.

## Implémentation

- `Item.external_code` (20 car.) + contrainte partielle
  `item_external_code_unique_not_blank` — migration `catalog/0013`.
- `apps/catalog/lookup.py` : `normalize_external_code`, `is_valid_external_code`,
  `find_item`. `find_item` sort sans interroger la base quand la chaîne ne peut
  être ni un code Ofelia ni un code externe (texte libre) — la recherche globale
  l'appelle à chaque requête.
- Câblé dans : `core.views.global_search`, `catalog.views.record_list`,
  `loans.views` (prêt + retour), `inventory.services.record_scan`,
  `api.views` (batch de récolement OfeliaScan).
- Récolement : le pointage est stocké sous le **code Ofelia** de l'exemplaire
  retrouvé, quelle que soit l'étiquette lue — scanner les deux étiquettes du
  même livre ne compte qu'une fois.
- `ItemForm.clean_external_code` normalise et refuse un code déjà pris avec un
  message lisible (l'unicité base reste le filet de sécurité).
  `ItemBulkCreateForm` refuse « code externe + plusieurs exemplaires ».
- Import Excel : `EXTERNAL_CODE` (+ alias via `_resolve_column`), avertissements
  `EXTERNAL_CODE_INVALID` / `EXTERNAL_CODE_DUPLICATE` (doublon dans le fichier
  **ou** code déjà porté en base), expliqués dans le rapport du job.
- Tests : `apps/catalog/tests/test_external_code.py` (33) + 2 dans
  `apps/loans/tests/test_views.py`.
