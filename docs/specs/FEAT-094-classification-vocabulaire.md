# FEAT-094 — Vocabulaire « classification » / « code de classification »

**Status:** DONE
**Date:** 2026-09-15
**Validé:** 2026-09-17 (Val)

## Context

Sur une notice catalogue, le bibliothécaire voit aujourd'hui le label
**« Catégorie »** pour le nom (ex. « Jeunesse Documentaire ») et
**« Abréviation »** pour la cote courte (ex. « JE DOC »). Ces deux mots
prêtent à confusion :

- « Catégorie » désigne aussi les **catégories d'usagers** (Adulte, Enfant…)
  — un objet différent, géré depuis Tarifs.
- « Abréviation » décrit le mécanisme (on raccourcit un nom) plutôt que le
  rôle du champ : c'est le **code de classification** imprimé sur la tranche.

Val demande un vocabulaire unique, partout où le bibliothécaire le lit :
interface, import Excel, catalogage, menu Avancé, documentation, i18n.

## Vocabulary

| Avant | Après | Exemple |
|---|---|---|
| Catégorie (d'une notice) | **Classification** | Jeunesse Documentaire |
| Abréviation / cote de catégorie | **Code de classification** | JE DOC |
| Catégorie d'usager | inchangé | Adulte, Enfant |

Les rapports du fonds (FEAT-093) disent déjà **« Rayon »** pour le même
objet, côté comité. Ce mot reste : il nomme le meuble, pas le champ de la
notice.

## Inventory (measured, 2026-09-15)

### In scope — catalog `Category` shown to a librarian

**Fiche et listes catalogue**

- `templates/catalog/record_detail.html` — dt « Catégorie » + pastille de cote
- `templates/catalog/record_list.html` — filtre, colonne, barre d'affectation
- `templates/catalog/_item_results.html` — colonne des exemplaires
- `templates/catalog/_record_form.html` — champ du formulaire (label via modèle)
- `templates/catalog/scan_session.html` — colonnes et lot « Catégorie »
- `apps/catalog/models.py` — `Category` verbose_name, `abbreviation`,
  `parent`, `BibliographicRecord.category`
- `apps/catalog/forms.py` — `CategoryForm`, `ScanCatalogSessionForm.default_category`
- `apps/catalog/views.py` — messages create/edit/delete, bulk assign
- `apps/core/tests/test_form_labels.py` — assert « Catégorie »

**Avancé → Classifications**

- `templates/core/advanced.html` — carte « Catégories » + sous-titre cote
- `templates/catalog/category_list.html` / `category_form.html` /
  `category_confirm_delete.html`

**Excel**

- Colonnes exportées `CATEGORY` / `CATEGORY_ABBR`
  (`apps/catalog/excel_export.py`)
- Import / mise à jour (`apps/catalog/excel_catalog.py`) — en-têtes,
  alias, codes d'avertissement `CATEGORY_UNKNOWN` / `CATEGORY_ABBR_ORPHAN`
- Aide à l'écran : `templates/catalog/excel_catalog/_import_form.html`,
  `_export_form.html`, `_update_form.html`

**Impression**

- `templates/printing/spine_labels_picker.html` — colonnes « Catégorie »
  et « Cote imprimée »
- `apps/printing/views.py` — message « catégorie abrégée »
- `templates/core/advanced.html` — sous-titre étiquettes de tranche

**Rapports / historique**

- `apps/reports/builders/worklists.py` — colonne « Catégorie » des livres
  inactifs (pas celle des usagers)
- `templates/members/member_history.html` + `apps/members/views.py` —
  « Statistiques par catégorie » / « Sans catégorie » = classification
  des livres empruntés

**Récolement (hors UI depuis FEAT-045, encore en base)**

- `apps/inventory/models.py` — `InventoryScope.CATEGORY` « Une catégorie »,
  `scope_category` verbose_name

**Paramètres**

- `apps/core/forms.py` — aide durée de prêt « catégorie de document »

**Guide utilisateur (× 4 langues)**

- `docs/user-guide/docs/catalogue/categories.md` (+ en/es/mg)
- `ajouter-livre`, `recherche`, `operations-lot`
- `inventaire/catalogage-excel`, `catalogage-scan`, `catalogage-douchette`
- `impressions/etiquettes`
- `premiers-pas/langue.md` (mélange classifications / catégories d'usagers)
- `docs/user-guide/mkdocs.yml` — entrée de nav « Catégories »

**SPEC** — §5.2 Category, §6.1 catalogue, §6.7 étiquettes, §6.12 Excel.

### Out of scope — leave « catégorie »

- Tout ce qui parle d'une **catégorie d'usager** : `MemberCategory`,
  tarifs, fiche usager, cartes, filtres membres, rapports « Qui emprunte,
  par catégorie d'usager », « Les catégories d'usager ».
- Le mot **catégorie** des graphes (barre groupée par catégorie = notion
  statistique, pas le modèle `Category`).
- **Abréviation** d'une langue (`fr`) et **abréviation** du fuseau (`CEST`).
- Identifiants internes : modèle `Category`, champ `abbreviation`, URLs
  `/catalog/categories/`, clés JSON API `category` / `scope_type=category`
  (contrat OfeliaScan, cf. `feedback_ofeliascan_contract.md`).
- Codes machine d'import `CATEGORY_UNKNOWN` et `CATEGORY_ABBR_ORPHAN`
  (déjà dans des fichiers et des tests ; les alias d'en-tête suffisent).

## Behavior

1. Toute chaîne visible qui désigne `catalog.Category` dit **classification**
   (pluriel **classifications**).
2. Toute chaîne visible qui désigne `Category.abbreviation` dit **code de
   classification**.
3. L'export Excel écrit `CLASSIFICATION` (le nom) et `CLASSIFICATION_CODE`
   (l'abréviation). L'import et la mise à jour **acceptent les anciens
   noms** `CATEGORY` / `CATEGORY_ABBR` (et les alias déjà en place :
   `ABREVIATION`, `CAT_ABBR`…).
4. Les URLs, le modèle, l'API et les codes d'avertissement ne bougent pas.
5. Les catégories d'usagers ne bougent pas.

## Technical spec

- Changer les `verbose_name` / `{% trans %}` / `_()` listés ci-dessus.
  Une migration `AlterField` / `AlterModelOptions` documente le nouvel
  état Django ; le schéma SQLite ne change pas.
- Excel : `EXPORT_COLUMNS` adopte les nouveaux en-têtes. `_COLUMN_ALIASES`
  ajoute `classification` → `category` et `classification_code` (plus
  `code_de_classification`, `code de classification`) → `category_abbr`.
  `run_import_job` résout la colonne catégorie via `_resolve_column`, pas
  `headers.get("category")` — sinon un fichier exporté avec le nouvel
  en-tête serait lu comme « sans classification ».
- i18n : nouvelles msgid FR, script `scripts/translations_sprint35.py`,
  gate `i18n_check.py` à 0.
- Tests : labels du formulaire notice, en-têtes d'export, aller-retour
  ancien et nouvel en-tête Excel, vocabulaire de l'écran Classifications.

## Side effects

| Risque | Traitement |
|---|---|
| Fichiers Excel déjà produits avec `CATEGORY` | Alias d'import : ils continuent de fonctionner. |
| Export → mise à jour d'un fichier **ancien** | Les deux jeux d'en-têtes sont lus. Un fichier **nouveau** se relit tout seul. |
| Signets `/catalog/categories/` | Conservés. |
| OfeliaScan `scope_type=category` | Inchangé (contrat API). |
| msgid Django « Catégorie » partagée catalogue / usagers | On **ne traduit pas** cette msgid : on change la chaîne source côté catalogue seulement. Les pages usagers gardent « Catégorie ». |
| Deux colonnes « Code » et « Code de classification » sur l'écran de gestion | Préexistant (FEAT-071 : code = cote pour les 20 classifications Ofelia). Hors périmètre. |
| Rapports « Rayon » | Laissés. Vocabulaire comité, pas champ de notice. |
| Captures du guide | Les pages catalogue / Avancé / Excel montreront le nouveau mot. Les PNG ne sont pas refaits dans ce sprint (comme les captures rapports, déjà périmées). |

## Impact on existing code

Voir l'inventaire. Pas de changement de schéma métier, pas de recopie de
données, pas de commande de migration de contenu.

## Implementation

- Libellés UI + `verbose_name` Django (migrations `catalog/0021` et
  `inventory/0005`, schéma inchangé).
- Excel : `EXPORT_COLUMNS` = `CLASSIFICATION` / `CLASSIFICATION_CODE` ;
  `_COLUMN_ALIASES` relit `CATEGORY` / `CATEGORY_ABBR` et les alias déjà
  en place ; `run_import_job` résout la colonne via `_resolve_column`.
- i18n : `scripts/translations_sprint35.py` (40 chaînes + 2 pluriels × 3
  langues). Gate `i18n_check.py` = 0.
- Tests : 1062 passed sur Fez (`ofelia/bibliofelia:dev`).
- Déployé Fez (sanjuan + grand-saconnex), image de secours Avignon, Box
  Canaima, guide `docs.bibliofelia.org` et guide de la Box.
- Validé Val le 2026-09-17.
