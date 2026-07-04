---
id: FEAT-053
title: Import Excel — affectation des métadonnées de la fiche
status: DONE
created: 2026-07-03
approved: 2026-07-03
implemented: 2026-07-03
owner: Val
---

# FEAT-053 — Import Excel : colonnes de métadonnées fiche/exemplaire

> Le mode **IMPORT** du Catalogage Excel (FEAT-050) ne matérialisait qu'une
> liste d'ISBN (+ `LOCATION`/`CATEGORY`). Cette feature ajoute la possibilité
> d'**affecter toutes les informations de la fiche catalogue** depuis des
> colonnes optionnelles du fichier. Si une colonne est présente et remplie,
> elle **écrase** l'information correspondante de la fiche — **y compris sur une
> notice déjà existante** (matchée par ISBN).

## Contexte / motivation

Les bibliothèques rejoignant Ofelia arrivent souvent avec un tableur déjà
renseigné (auteur, éditeur, année, type, tags…). FEAT-050 importait l'ISBN mais
laissait le reste à l'enrichissement en ligne (FEAT-031), inutilisable hors
connexion ou quand le fonds contient des ouvrages introuvables dans les bases
publiques. On veut pouvoir **injecter directement** les métadonnées du tableur.

## Périmètre

### Colonnes reconnues (toutes optionnelles)

| Colonne Excel | Cible | Notes |
|---|---|---|
| `TITLE` | `record.title` | notice neuve → titre posé directement (pas de placeholder `ISBN:…`) |
| `AUTHOR` | `record.authors` (M2M) | auteurs séparés par `;` — **remplacement** |
| `CATEGORY` | `record.category` | nom de catégorie existante (`name__iexact`) |
| `TYPE` | `record.document_type` | code interne ou libellé FR |
| `EDITOR` | `record.publisher` | |
| `YEAR` | `record.publication_year` | entier |
| `LANGUAGE` | `record.language` | code (ex. `fr`) |
| `TAGS` | `record.tags` (M2M) | tags séparés par `,` — **remplacement**, cap 10 × 40 car. |
| `CONDITION` | `Item.state` | état de l'exemplaire (fiche exemplaire) |

`TYPE` accepte : `book`/`Livre`, `magazine_issue`/`Revue`/`Magazine`,
`comic`/`BD / manga`/`Manga`, `newspaper`/`Journal`, `audio_cd`/`CD audio`,
`other`/`Autre`. `CONDITION` accepte : `new`/`Neuf`, `good`/`Bon`, `worn`/`Usé`,
`damaged`/`Abîmé`. La résolution est insensible à la casse et aux accents
(`_norm`). Valeur non reconnue → warning (`TYPE_UNKNOWN`/`CONDITION_UNKNOWN`),
champ **inchangé**. `YEAR` non entier → warning `YEAR_INVALID`, champ inchangé.

### Sémantique d'écrasement (décisions Val 2026-07-03)

- **Cellule vide** = on **conserve** l'existant (une colonne présente ne vide
  jamais un champ).
- **Cellule remplie** = on **écrase** le champ, même sur une notice préexistante.
- `AUTHOR` et `TAGS` : **remplacement** (on efface l'existant puis on pose la
  liste du fichier), pas de fusion.

> Extension volontaire du périmètre FEAT-050, qui plaçait explicitement « la
> mise à jour de notices existantes » hors périmètre (rôle de FEAT-031). Ici la
> mise à jour est **pilotée par le fichier** et bornée aux colonnes présentes.

### Hors périmètre

- Colonnes `SUBTITLE`/`SUMMARY`/couverture (restent gérées par l'enrichissement
  ou la saisie manuelle).
- Édition en ligne de l'Excel.
- Mode VERIFY inchangé.

## Spécification technique

Tout dans `apps/catalog/excel_catalog.py` (aucune migration, aucun modèle).

- `IMPORT_OVERRIDE_COLUMNS` — liste des 8 colonnes optionnelles (noms normalisés).
- `_DOCUMENT_TYPE_ALIASES` / `_ITEM_STATE_ALIASES` — dicts d'alias normalisés →
  `DocumentType` / `ItemState`. Résolveurs `_resolve_document_type` /
  `_resolve_item_state` (None si inconnu).
- `_split_multi(value, sep)` — découpe auteurs/tags, dédup, sans vide.
- `_parse_row_overrides(row, override_cols, resolved_category)` → `(overrides,
  warnings)` : ne retient **que** les colonnes présentes ET non vides. Le titre
  parsé alimente aussi `ScanItem.metadata_title` (notice neuve titrée
  directement, sans placeholder).
- `_apply_import_overrides(job, session, overrides_by_local)` : **après**
  `finalize_scan_session`, applique les overrides via
  `ScanItem.processing_result` (`record_id` + `copies_created`) dans une
  transaction dédiée. Scalaires via `record.save(update_fields=…)` ; `authors`/
  `tags` via `clear()` + `get_or_create` ; `state` via
  `Item.objects.filter(pk__in=…).update(state=…)`.

Le flux **caméra / OfeliaScan** (`finalize_scan_session`) n'est **pas** touché :
l'écrasement des notices existantes est propre à l'import Excel.

### UI

`templates/catalog/excel_catalog/_import_form.html` documente les 8 colonnes et
la règle d'écrasement (cellule vide = on garde l'existant).

## Tests

Ajoutés à `apps/catalog/tests/test_excel_catalog.py` :

- `test_import_overrides_new_record_all_fields` — toutes les colonnes sur une
  notice neuve (title/author/type/editor/year/language/tags/condition).
- `test_import_overrides_existing_record` — écrasement d'une notice existante ;
  AUTHOR/TAGS remplacés ; titre (colonne absente) préservé.
- `test_import_title_overwrites_existing` — TITLE écrase le titre existant.
- `test_import_no_title_column_uses_placeholder` — sans TITLE, placeholder `ISBN:…`.
- `test_import_empty_cell_keeps_existing` — cellule vide → existant conservé.
- `test_import_unknown_type_and_condition_warn` — warnings + champs par défaut.
- `test_import_invalid_year_warns` — `YEAR_INVALID`, année laissée `None`.
- `test_import_type_by_code` — TYPE par code interne (`audio_cd`).

## i18n

Nouvelles chaînes d'aide du formulaire IMPORT → EN/ES/MG via
`scripts/translations_sprint22.py`. Gate `scripts/i18n_check.py → 0` avant commit.

## Statut

- [x] Décisions Val (cellule vide = garder l'existant ; AUTHOR/TAGS = remplacer) — 2026-07-03
- [x] Code (`excel_catalog.py` + `_import_form.html`)
- [x] Tests (6 cas ajoutés)
- [x] Doc : SPEC §6.12 + en-tête ; ce fichier ; `TASKS.md`
- [x] Guide utilisateur (MkDocs ×4) : page `catalogage-excel` (colonnes + règle d'écrasement) ; rattrapage ISSN (FEAT-052) sur `catalogage-scan`, `glossaire`, `ajouter-livre`. Build `--strict` → 0 warning
- [ ] i18n gate `i18n_check.py` → 0
- [ ] Déploiement Box + test fonctionnel Val
- [ ] Commit après confirmation Val
