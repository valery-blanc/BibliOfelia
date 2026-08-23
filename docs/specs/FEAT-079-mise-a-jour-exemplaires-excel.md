# FEAT-079 — Mise à jour d'exemplaires depuis un fichier Excel

**Statut** : DONE
**Sprint** : 30
**Demande** : Val, 2026-08-23 — « fenêtre "mise à jour des exemplaires" :
fonctionnement idem de la fenêtre import mais pour mettre à jour un ou plusieurs
exemplaires (pas de création de nouveaux exemplaires). Dans ce cas là le champ
obligatoire est le code Ofelia OU le code externe (au moins l'un des 2 doit être
renseigné, en cas de conflit c'est le code Ofelia qui compte : donc on met à
jour le code externe pour l'exemplaire retrouvé par son code Ofelia si les 2
info sont présentes). »

## Contexte

L'import Excel (FEAT-050/053) est indexé par **ISBN**. Il sait donc créer, et
il sait écraser les champs d'une notice existante retrouvée par son ISBN — mais
il ne sait pas viser **un exemplaire précis**, ni traiter un livre sans ISBN, ni
garantir qu'il ne créera rien. Corriger en masse l'emplacement, l'état ou le
code externe d'un fonds déjà catalogué était donc impossible sans risquer de
dupliquer la bibliothèque.

Avec FEAT-078 (export), la boucle se ferme : exporter → corriger dans Excel →
renvoyer par cette fenêtre.

## Comportement

4ᵉ carte sur `catalog:excel_catalog_index` : **« Mettre à jour des
exemplaires »**. Même formulaire d'upload que l'import, même page de suivi de
job, même tableau d'avertissements.

### La règle qui structure le mode : on ne crée jamais rien

Aucune notice, aucun exemplaire, aucune catégorie, aucun emplacement, aucune
provenance n'est créé. Une ligne dont l'exemplaire n'est pas retrouvé est
**comptée en erreur et listée dans le rapport**, jamais transformée en nouveau
livre. C'est cette garantie qui permet de renvoyer un export corrigé sans
crainte. (Seule exception assumée, héritée de l'import : les **tags** absents
sont créés — un tag est une étiquette libre, pas une entité du référentiel.)

### Identification de l'exemplaire

Colonnes clés, dont **au moins une** doit être présente dans le fichier (sinon
le fichier est refusé à l'upload, sans créer de job) :

- `OFELIA_CODE` — accepte indifféremment l'**EAN13 « 290… »** (le code-barres de
  l'étiquette) et le **code interne « OFL-… »** (le code lisible imprimé à côté).
  Alias d'en-tête : `CODE_OFELIA`, `CODE OFELIA`, `OFELIA`, `EAN13`, `EAN_13`.
- `INTERNAL_ID` — colonne dédiée au code interne, lue si `OFELIA_CODE` est vide.
  Alias : `CODE_INTERNE`, `CODE INTERNE`, `INTERNALID`, `ID_OFELIA`.
- `EXTERNAL_CODE` — code Ofelia externe (FEAT-063), normalisé avant recherche
  (`BCF-1329 8781x` = `BCF13298781X`). Alias : ceux de FEAT-063.

Résolution, ligne par ligne :

| Cas | Comportement |
|---|---|
| Code Ofelia seul | exemplaire retrouvé par EAN13 puis par code interne |
| Code externe seul | exemplaire retrouvé par `external_code` |
| **Les deux** | **le code Ofelia identifie l'exemplaire**, et le code externe de la ligne **lui est appliqué** (c'est la façon d'attribuer des codes externes en masse) |
| Code Ofelia inconnu | `OFELIA_CODE_UNKNOWN`, ligne **ignorée** |
| Code externe inconnu (et pas de code Ofelia) | `EXTERNAL_CODE_UNKNOWN`, ligne ignorée |
| Aucun des deux sur la ligne | `NO_KEY`, ligne ignorée |
| Ligne entièrement vide | ignorée en silence (openpyxl en compte après les données) |

**Un code Ofelia inconnu ne retombe pas sur le code externe.** Il signale une
ligne qui désigne mal son exemplaire : mieux vaut la signaler que modifier au
jugé un autre livre.

### Champs modifiables

Toutes les colonnes de l'import, plus `LOCATION` et `ISBN` (en import, ISBN est
la clé et LOCATION n'est posée qu'à la création — ici ce sont des champs comme
les autres) :

`TITLE`, `AUTHOR`, `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `EDITOR`, `YEAR`,
`LANGUAGE`, `TAGS`, `CONDITION`, `PROVENANCE`, `LOCATION`, `ISBN`,
`EXTERNAL_CODE`.

**Sémantique reprise de l'import (FEAT-053)** : une cellule remplie remplace la
valeur existante ; **une cellule vide laisse la valeur en place**. Le fichier ne
sert donc pas à effacer un champ — c'est ce qui permet de renvoyer un export
avec deux colonnes corrigées sans réécrire tout le reste. `AUTHOR` et `TAGS`
remplacent (pas de fusion).

Les champs de **notice** (titre, auteur, éditeur…) valent pour tous les
exemplaires de cette notice : deux lignes du même livre qui corrigent le titre
différemment, la dernière gagne.

### Avertissements par ligne

| Code | Effet |
|---|---|
| `OFELIA_CODE_UNKNOWN`, `EXTERNAL_CODE_UNKNOWN`, `NO_KEY` | ligne non appliquée (`errors++`) |
| `ROW_ERROR` | erreur technique sur cette ligne, les autres passent (`errors++`) |
| `ISBN_INVALID` | ISBN de longueur ∉ {10,13} non repris, reste de la ligne appliqué |
| `ISBN_CONFLICT` | ISBN-13 déjà porté par une autre notice — non repris (la contrainte d'unicité aurait fait tomber le lot entier), reste appliqué |
| `EXTERNAL_CODE_DUPLICATE` | code déjà porté par un autre exemplaire — non repris, reste appliqué |
| `EXTERNAL_CODE_INVALID`, `TYPE_UNKNOWN`, `CONDITION_UNKNOWN`, `YEAR_INVALID`, `CATEGORY_UNKNOWN`, `PROVENANCE_UNKNOWN`, `LOCATION_UNKNOWN`, `CATEGORY_ABBR_ORPHAN` | valeur ignorée, reste de la ligne appliqué |

Un avertissement **n'est pas** une erreur : `errors` ne compte que les lignes
qui n'ont rien pu appliquer. La page de détail affiche un bandeau rouge
« N lignes non appliquées » dès `errors > 0`, comme l'import le fait pour
`ISBN_MISSING` (BUG-025).

### Compteurs

Deux nouveaux champs sur `ExcelCatalogJob` : **`updated`** (lignes qui ont
changé quelque chose) et **`unchanged`** (exemplaire retrouvé, rien à changer).
Sans ce partage, « 300 lignes traitées » ne dit pas si le fichier a eu un effet.
Chaque champ est comparé avant écriture, donc `updated` compte des changements
réels, pas des lignes lues.

## Spec technique

- `ExcelJobMode.UPDATE = "update"` + `ExcelCatalogJob.updated` / `.unchanged`
  → migration `catalog/0020_excel_update_mode`.
- `apps/catalog/excel_catalog.py` :
  - `UPDATE_KEY_COLUMNS`, `UPDATE_OVERRIDE_COLUMNS`, alias d'en-tête ;
  - `validate_xlsx` : branche UPDATE (au moins une colonne clé, alias compris) ;
  - `_find_item_by_ofelia_code`, `_apply_item_update`, `run_update_job` ;
  - dispatch dans `run_excel_catalog_job`.
- Vue `catalog:excel_catalog_update` (POST, `WRITE_ROLES`) → même
  `_start_excel_job` que l'import.
- Templates `_update_form.html` + branches `mode == "update"` de `detail.html`.

### Robustesse

- **Une transaction par ligne** : une ligne qui casse est signalée `ROW_ERROR`
  et le reste du fichier passe. Un lot de 500 lignes ne se perd pas sur une.
- **Référentiels chargés une fois** pour tout le fichier (emplacements,
  provenances) — pas une requête par ligne.
- **Sauvegarde partielle toutes les 10 lignes**, comme le mode VERIFY : la page
  de suivi avance visiblement et un plantage ne perd pas tout.
- `save(update_fields=…)` : seuls les champs réellement modifiés sont écrits.

### Résolutions rendues insensibles à la langue

Conséquence directe de FEAT-078, qui exporte des libellés traduits alors que le
job tourne dans le **worker django-q2**, en français :

- `_translated_label_aliases()` — libellés de `DocumentType` / `ItemState` dans
  toutes les langues de l'instance → valeur. Construit une fois par processus.
- `_resolve_category()` — cherche le nom dans **tous** les champs `name_<lang>`
  de modeltranslation, puis à défaut par **code** de catégorie.
- `_get_or_create_tag()` — même recherche multi-langue avant de créer, sinon un
  fichier espagnol recréerait chaque tag en double avec le libellé espagnol
  logé dans le champ français.

Ces trois helpers servent **aussi à l'import**, qui en bénéficie sans rien
perdre (ils sont strictement plus permissifs).

## Impact

- 1 migration (`0020`), sans effet sur les données existantes.
- Import inchangé, sauf les résolutions ci-dessus.
- Aucun effet sur le catalogage par scan, l'API ou le récolement.

## Tests

`apps/catalog/tests/test_excel_update.py` — 35 tests : validation (colonne clé
requise, alias FR), résolution par EAN13 / code interne / colonne dédiée / code
externe normalisé, priorité du code Ofelia avec application du code externe,
les trois erreurs d'identification, non-création vérifiée par comptage
(`_counts()`), tous les champs appliqués, cellule vide non destructive, ISBN
modifiable et conflit d'ISBN, code externe déjà pris, emplacement et catégorie
inconnus non bloquants, libellés lus dans les 4 langues (paramétré), catégorie
retrouvée par nom traduit et par code, remplacement (pas fusion) d'AUTHOR/TAGS,
compteur `unchanged`, aller-retour export → mise à jour sans un seul changement,
et un garde-fou de cohérence : toute colonne d'export doit être relisable par la
mise à jour.
