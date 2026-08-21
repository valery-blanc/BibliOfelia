# FEAT-067 — Catégorie abrégée + écran de gestion des catégories

**Status:** DONE
**Date:** 2026-08-19

## Contexte

Le rangement en rayon se fait sur une abréviation courte lisible sur la tranche
du livre : « Romans fiction pour adolescents » devient `RO FI ADO`. Cette
abréviation doit vivre à côté de la catégorie et suivre le livre jusqu'à
l'étiquette de tranche (FEAT-068).

Second constat : les catégories ne sont aujourd'hui modifiables que dans
`/admin/`, jamais montré aux bibliothécaires. Sans écran de gestion,
l'abréviation ne serait pas saisissable par eux.

## Comportement

### Abréviation

Champ **« Abréviation »** sur la catégorie (décision Val 2026-08-19 : portée
par la catégorie, pas par la notice — une seule saisie, aucune divergence
possible entre deux livres de la même catégorie). Jusqu'à 20 caractères,
facultatif. Toutes les notices de la catégorie en héritent ; elle s'affiche sur
la fiche de la notice à côté du nom de catégorie.

Les 16 catégories du seed reçoivent une abréviation par défaut (`ENF-ALB` →
`ENF ALB`, `ADU-ROM` → `ADU ROM`, …), posée **uniquement à la création** :
comme pour les traductions, `seed_defaults` ne réécrit jamais une valeur déjà
saisie.

### Écran de gestion des catégories

**Catalogue → Catégories** (rôle bibliothécaire) : liste (code, nom,
abréviation, parent, nombre de notices), création, modification, suppression.
Supprimer une catégorie ne supprime aucune notice : les notices concernées se
retrouvent sans catégorie (`SET_NULL`, comportement déjà en place). Le nombre
de notices touchées est annoncé sur l'écran de confirmation.

### Import Excel

Colonne **`CATEGORY_ABBR`** (alias `ABBREVIATION`, `ABREVIATION`,
`CATEGORIE_ABREGEE`) : renseigne l'abréviation de la catégorie de la ligne,
résolue comme aujourd'hui par la colonne `CATEGORY`. Sans colonne `CATEGORY`
résolue, l'abréviation n'a pas de cible : avertissement
`CATEGORY_ABBR_ORPHAN`, la ligne s'importe quand même.

## Spec technique

- `Category.abbreviation` — `CharField(max_length=20, blank=True)`. Non
  traduit : une cote de rayon est physique, elle ne change pas avec la langue
  de l'interface.
- `CategoryForm` + vues `category_list` / `category_create` / `category_edit` /
  `category_delete`, calquées sur les emplacements (FEAT-032).
- `seed_defaults` : 8e colonne dans `CATEGORIES`, appliquée aux créations et
  backfillée si vide.
- Import : `CATEGORY_ABBR` dans `IMPORT_OVERRIDE_COLUMNS`, écrite sur la
  `Category` résolue au moment de la lecture de la ligne.

## Impact sur l'existant

- `apps/catalog/models.py` (+ migration), `forms.py`, `views.py`, `urls.py`.
- `apps/core/management/commands/seed_defaults.py`.
- `apps/catalog/excel_catalog.py`.
- Templates : nouveaux `catalog/category_list.html`, `category_form.html`,
  `category_confirm_delete.html` ; `catalog/record_detail.html`.

## Implémentation

- `Category.abbreviation` (20 car., non traduite) — migration `catalog/0015`.
- `CategoryForm` + vues `category_list/create/edit/delete`, calquées sur les
  emplacements ; entrée « Catégories » dans **Avancé**. La suppression annonce
  le nombre de notices qui perdront leur catégorie (aucune notice supprimée).
- `seed_defaults` : 8e colonne `abbreviation` sur les 16 catégories, posée à la
  création et backfillée si vide — une cote saisie à la main n'est jamais
  écrasée.
- Import Excel : `CATEGORY_ABBR` (+ alias), écrite sur la `Category` résolue par
  la colonne `CATEGORY` ; `CATEGORY_ABBR_ORPHAN` si aucune catégorie n'est
  résolue.
- Cote affichée en pastille sur la fiche notice.
- Tests : `apps/catalog/tests/test_categories.py` (14).
