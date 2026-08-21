# BUG-027 — Provenance absente de plusieurs écrans

**Status:** DONE
**Date:** 2026-08-20

## Symptôme

Retour de test Val (2026-08-20) : après FEAT-064, la provenance n'apparaît pas
là où on l'attend.

1. **Fiche notice** — le tableau des exemplaires ne montre pas la provenance.
2. **Page d'import Excel** — la liste des colonnes acceptées ne mentionne pas
   `PROVENANCE` (ni `EXTERNAL_CODE`, ni `CATEGORY_ABBR`), alors que l'import les
   traite. La fonctionnalité existe mais reste invisible.
3. **Formulaire d'exemplaire** — signalé manquant, mais le champ **est** présent.

## Reproduction

1. Ouvrir une notice ayant des exemplaires → colonnes Code interne, Code Ofelia,
   Code externe, Emplacement, État, Statut. Pas de provenance.
2. Ouvrir `/catalog/excel-catalog/` → l'encadré « Importer dans BibliOfelia »
   s'arrête à `CONDITION`.

## Cause racine

FEAT-064 a ajouté la provenance au modèle, aux formulaires, au catalogue et aux
actions de masse, mais pas aux écrans de **consultation** ni à la
**documentation en ligne des colonnes d'import**. Les trois colonnes ajoutées
au Sprint 28 (`EXTERNAL_CODE`, `PROVENANCE`, `CATEGORY_ABBR`) n'ont été
documentées que dans le guide utilisateur et la SPEC, pas dans l'écran lui-même.

Point 3 : faux positif. `ItemForm.Meta.fields` contient bien `provenance` et le
template rend tous les champs. Ce qui a trompé l'œil : **aucune provenance
n'existait en base**, le menu déroulant ne proposait donc que la ligne vide.

## Fix appliqué

- `record_detail.html` : colonne **Provenance** dans le tableau des exemplaires.
- `excel_catalog/_import_form.html` : les 3 colonnes du Sprint 28 ajoutées à la
  liste, avec leur description.
- `ItemForm` : quand aucune provenance n'existe, l'aide du champ pointe vers
  l'écran de création plutôt que d'afficher un menu vide sans explication.
- Audit des autres écrans montrant un exemplaire (picker d'impression, rapports,
  récolement, API OfeliaScan) — cf. § Écrans audités.

## Écrans audités

| Écran | Provenance | Décision |
|---|---|---|
| Fiche notice (tableau exemplaires) | manquait | **ajoutée** |
| Picker d'impression d'étiquettes | absente | ajoutée (utile pour trier un fonds avant impression) |
| Catalogue mode exemplaires | présente | — |
| Confirmation de suppression d'exemplaires | présente | — |
| Formulaire d'exemplaire | présente | aide améliorée |
| Rapport de récolement | absente | non ajoutée : le rapport pointe des codes, pas des attributs |
| Exemplaires inactifs (rapports) | absente | non ajoutée : la colonne n'aide pas à décider d'un pilon |
| API OfeliaScan | absente | non ajoutée : hors contrat, l'app mobile ne l'affiche pas |

## Spec impactée

SPEC §6.1 (fiche notice), §6.12 (colonnes d'import).

## Vérification

- `record_detail.html` : colonne **Provenance** ajoutée après Emplacement.
- `labels_picker.html` : colonne ajoutée aussi (utile pour trier un fonds avant
  d'imprimer ses étiquettes).
- `excel_catalog/_import_form.html` : `EXTERNAL_CODE`, `PROVENANCE` et
  `CATEGORY_ABBR` annoncés avec leur description.
- `ItemForm.__init__` : quand la table `Provenance` est vide, l'aide du champ
  renvoie vers Avancé → Provenances au lieu d'un menu muet.
- Tests : couverts par `test_provenance.py` et les tests d'écran existants ;
  suite complète **620 passed**.
