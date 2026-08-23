# FEAT-078 — Export Excel de tout le catalogue

**Statut** : DONE
**Sprint** : 30
**Demande** : Val, 2026-08-23 — « une fenêtre export qui exporte toute la base
en excel avec tous les champs supportés par l'import ».

## Contexte

L'écran **Avancé → Inventaire → Catalogage Excel** (FEAT-050/053) savait faire
entrer des données (vérifier un fichier, importer un fichier) mais pas les faire
sortir. Un bibliothécaire qui voulait relire son fonds, le corriger en masse ou
simplement en garder une copie hors ligne n'avait qu'un export CSV enfoui dans
les rapports (`reports:catalog_csv`, FEAT-040), dont les colonnes ne
correspondent **pas** à celles que l'import sait relire.

FEAT-078 ferme la boucle : le fichier produit ici est exactement celui que
FEAT-079 (mise à jour d'exemplaires) sait relire.

## Comportement

Une 3ᵉ carte sur `catalog:excel_catalog_index` : **« Exporter le catalogue »**.
Elle annonce le nombre d'exemplaires que le fichier contiendra, liste les
colonnes, et propose un lien de téléchargement direct.

- **Une ligne par exemplaire**, pas par notice. L'emplacement, l'état, la
  provenance et le code externe appartiennent à l'exemplaire : une notice à
  trois exemplaires sort sur trois lignes, dont les colonnes de fiche sont
  identiques. C'est dit explicitement sur la carte.
- Tri : titre de notice, puis code interne — les exemplaires d'un même livre
  se suivent.
- Rôle **librarian + superadmin** (`WRITE_ROLES`), comme le reste de l'écran.
- Nom du fichier : `catalogue-AAAA-MM-JJ.xlsx`.

### Colonnes (`apps/catalog/excel_export.py::EXPORT_COLUMNS`)

| Colonne | Source | Note |
|---|---|---|
| `OFELIA_CODE` | `Item.ean13` | code-barres de l'étiquette (290…) |
| `INTERNAL_ID` | `Item.internal_id` | code lisible OFL-… |
| `EXTERNAL_CODE` | `Item.external_code` | FEAT-063 |
| `ISBN` | `isbn_13` sinon `isbn_10` | |
| `TITLE` | `record.title` | |
| `AUTHOR` | auteurs joints par `; ` | séparateur attendu par l'import |
| `CATEGORY` | `category.name` | champ traduit (modeltranslation) |
| `CATEGORY_ABBR` | `category.abbreviation` | cote, répétée sur chaque ligne |
| `TYPE` | `get_document_type_display()` | libellé traduit |
| `EDITOR` | `record.publisher` | |
| `YEAR` | `record.publication_year` | nombre, pas texte |
| `LANGUAGE` | `record.language` | code (`fr`, `es`…) |
| `TAGS` | tags joints par `, ` | séparateur attendu par l'import |
| `CONDITION` | `item.get_state_display()` | libellé traduit |
| `PROVENANCE` | `provenance.code` | |
| `LOCATION` | `location.code` | |

En-têtes en gras, `freeze_panes = "A2"`, largeurs de colonne posées — sans quoi
le fichier s'ouvre sur seize colonnes de 8 caractères où rien n'est lisible.

## Spec technique

- `apps/catalog/excel_export.py` — `EXPORT_COLUMNS`, `items_queryset()`,
  `export_row(item)`, `build_catalog_workbook() -> bytes`.
- Vue `catalog:excel_catalog_export` (`apps/catalog/views.py`) →
  `HttpResponse` `Content-Disposition: attachment`.
- Template `templates/catalog/excel_catalog/_export_form.html`.

### Décisions

**Export synchrone, pas un job django-q2.** Contrairement à la vérification,
l'export ne fait aucun appel réseau : c'est une lecture de base. Sur un
catalogue Ofelia (jusqu'à 3000 ouvrages en cible, quelques milliers
d'exemplaires) il tient largement dans le `--timeout 60` de gunicorn. Passer par
la file aurait ajouté un job, une page d'attente et un fichier stocké dans
`media/` pour quelques secondes de travail.

**`openpyxl` en mode `write_only` + `.iterator(chunk_size=500)`.** Les lignes
partent au fichier au fil de l'itération plutôt que de s'empiler en mémoire :
sur une Box à 4 Go, un gros catalogue n'a pas à tenir deux fois en RAM.

**Libellés traduits plutôt que codes internes pour TYPE et CONDITION.** C'est
le fichier d'un bibliothécaire, pas un export machine : il doit y lire
« Livre » / « Bon », pas `book` / `good`. Conséquence obligatoire côté relecture,
traitée dans FEAT-079 : `_resolve_document_type` / `_resolve_item_state`
acceptent désormais les libellés de **toutes** les langues de l'instance, et
`_resolve_category` cherche le nom de catégorie dans tous les champs
`name_<lang>`. Sans ça, un fichier exporté en espagnol serait revenu avec
`TYPE_UNKNOWN` et `CATEGORY_UNKNOWN` sur chaque ligne — l'export ne
fonctionnerait qu'en français.

**Exemplaires seulement.** Une notice sans exemplaire (cas rare : l'import en
crée toujours un) n'a pas de ligne. L'ajouter aurait produit, à chaque
aller-retour, une ligne sans code d'identification donc une erreur en mise à
jour — du bruit permanent pour un cas qui n'existe pas en pratique.

## Impact

- Aucune migration, aucun modèle touché.
- Aucune modification de l'import existant, **sauf** deux résolutions rendues
  insensibles à la langue (catégories, tags) — strictement plus permissives
  qu'avant, donc sans régression.

## Tests

`apps/catalog/tests/test_excel_export.py` — 8 tests : en-têtes = colonnes
d'import, une ligne par exemplaire, chaque champ transporté, cellules vides pour
les relations absentes, séparateurs `; ` / `, `, vue (type MIME, en-tête
`attachment`), refus au rôle `readonly`.

Le test d'aller-retour vit dans `test_excel_update.py`
(`test_exported_file_reimports_without_a_single_change`) : il protège les deux
features à la fois.
