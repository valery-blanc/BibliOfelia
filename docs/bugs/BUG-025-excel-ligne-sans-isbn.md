# BUG-025 — Import Excel : ligne sans ISBN escamotée sans erreur

**Status:** FIXED
**Date:** 2026-08-03

## Symptôme

Import Excel de 105 lignes vers l'emplacement T2 : **104 notices** au catalogue.
Une ligne perdue, et **aucune erreur** nulle part — ni bandeau, ni compteur, ni
avertissement. Le job affichait « Total 104 / Traitées 104 / Erreurs 0 », donc
parfaitement cohérent avec lui-même : la ligne n'avait jamais existé de son point
de vue.

## Reproduction

Instance grand-saconnex, job `ExcelCatalogJob #1`, fichier
`Collection_L483731.xlsx` : 105 lignes de données, dont la **ligne 85**
(« Ruiz, Miguel — L'art de vivre et de mourir ») a une **cellule ISBN vide**,
toutes les autres colonnes remplies.

## Cause racine

`run_import_job` :

```python
if not raw_isbn:
    continue          # ← sortie silencieuse : ni total, ni report, ni errors
```

L'intention était de sauter les lignes vides que `openpyxl` compte souvent
au-delà des données réelles. Mais le test « pas d'ISBN » englobait aussi les
lignes **remplies** sans ISBN. `total` n'étant incrémenté qu'après ce `continue`,
le job ignorait jusqu'à l'existence de la ligne.

Le mode VERIFY, lui, traite correctement ces lignes (il bascule sur la passe 2
titre + auteur) : seul l'IMPORT était concerné.

## Fix appliqué

`apps/catalog/excel_catalog.py` — on distingue les deux cas :

- **ligne entièrement vide** → toujours ignorée en silence (comportement voulu) ;
- **ligne avec du contenu mais sans ISBN** → comptée dans `total` et `processed`,
  `errors += 1`, entrée de rapport `ISBN_MISSING` accompagnée d'un `label`
  « Auteur — Titre » (`_row_label`) pour identifier le livre à cataloguer à la
  main.

Les lignes à **ISBN invalide** (`ISBN_INVALID`, déjà comptées) reçoivent le même
`label`.

Côté UI (`templates/catalog/excel_catalog/detail.html`), demande Val « il faut
rajouter une erreur pour les ISBN manquants ou invalides » :

- **bandeau rouge** en tête de job dès `errors > 0` en mode import — « N lignes
  non importées », avec l'explication (l'import est indexé par ISBN) ;
- dans le tableau des avertissements, une phrase par code (`ISBN_MISSING` /
  `ISBN_INVALID`) et le libellé auteur — titre de la ligne.

L'import reste **indexé par ISBN** : une ligne sans ISBN ne peut pas être
matérialisée par `finalize_scan_session`. Le fix rend la perte visible et
actionnable, il ne crée pas la notice.

## Vérification

`apps/catalog/tests/test_excel_catalog.py` :
- `test_import_job_reports_row_without_isbn` (total 3, errors 1, entrée
  `ISBN_MISSING` avec le bon numéro de ligne et le bon libellé, 2 lignes
  importées) ;
- `test_import_job_ignores_fully_empty_rows` (pas de bruit sur les lignes vides).

## Section spec impactée

`SPEC_BIBLIOFELIA.md` §6.12 (catalogage Excel — mode import).
