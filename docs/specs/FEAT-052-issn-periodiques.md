---
id: FEAT-052
title: Support des périodiques ISSN (code-barres 977)
status: DONE
created: 2026-07-03
approved: 2026-07-03
implemented: 2026-07-03
owner: Val
---

# FEAT-052 — Support des périodiques ISSN

> La bibliothèque accueille des **revues / magazines**. Leur code-barres EAN-13
> commence par **977** (préfixe ISSN) et non 978/979 (ISBN). On les catalogue
> désormais exactement comme un livre : scan en catalogage caméra continu →
> lookup multi-sources du titre → notice de type **Revue** portant l'ISSN →
> impression d'étiquette Ofelia.

## Contexte / motivation

Le scanner de catalogage rejetait les codes 977 (`isAcceptableCode` limité à
290/291/978/979) et toute la chaîne (lookup, finalisation, notice) était câblée
pour l'ISBN. Le champ `document_type` de `BibliographicRecord` prévoyait déjà
`magazine_issue` / `newspaper` mais n'était **jamais exploité**, et il n'existait
**aucun champ ISSN**.

## Rappel technique ISSN

Un EAN-13 de périodique se décompose ainsi :

```
977  + 7 chiffres (les 7 premiers de l'ISSN, sans sa clé)
     + 2 chiffres de variante (numéro / prix)
     + 1 clé EAN-13
```

Exemple : `9771828552248` → segment `1828552` → clé ISSN (mod 11) `X`
→ **ISSN 1828-552X**. L'ISSN est stocké normalisé sans tiret : `1828552X` (8 car.).
Les 2 chiffres de variante ne font pas partie de l'ISSN : deux numéros d'une
même revue partagent donc le même ISSN.

## Décisions produit

- **Lookup ISSN multi-sources** : sources SRU des bibliothèques nationales
  (BnF, BNE) qui cataloguent les publications en série. OpenLibrary et Google
  Books n'indexent pas l'ISSN → hors registre. Si aucune source ne répond, le
  titre est saisi à la main (comme un livre inconnu).
- **1 notice par ISSN** : rescanner un autre numéro de la même revue retombe
  sur la même notice (contrainte unique sur `issn`). Le numéro / la date de
  livraison peut être noté à la main dans `series_volume`.
- **977 accepté en catalogage UNIQUEMENT** : le filtre du scanner caméra est
  global (chargé dans `base.html`). Il est rendu paramétrable (`allowIssn`) et
  seul le contrôleur de catalogage l'active. Prêt / retour / adhésion /
  récolement restent inchangés : un magazine s'y prête via son code Ofelia 290
  (étiquette collée), pas via son ISSN.

## Implémentation

| Couche | Fichier | Changement |
|---|---|---|
| Helper | `apps/core/issn.py` (nouveau) | `validate_issn`, `normalize_issn`, `issn_from_ean13`, `format_issn`, `issn_check_digit` |
| Modèle | `apps/catalog/models.py` + `migrations/0011_issn_periodical.py` | champ `issn` + contrainte unique `record_issn_unique_not_null` ; `ScanKind.ISSN` ; propriété `BibliographicRecord.issn_display` |
| Sources | `apps/catalog/sources/{bnf,bne}.py`, `sources/__init__.py` | `lookup_issn()` SRU (clause `bib.issn` / `alma.issn`) ; registre `ISSN_SOURCES` |
| Lookup | `apps/catalog/openlibrary.py` | `lookup_issn_multi()` (parallèle, miroir de `lookup_isbn_multi`) |
| Scan | `apps/catalog/views.py::scan_add` | branche 977 → `scan_kind=issn`, `lookup_issn_multi` |
| Recherche | `apps/core/search.py::classify_query`, `record_list`, `core.views.global_search` | nouveau `kind="issn"` : EAN13 977 (→ ISSN extrait) **ou** ISSN saisi (`1828-552X`) → filtre/redirige sur `issn`. Sans ça, une revue cataloguée restait introuvable dans le catalogue. |
| Finalisation | `apps/api/services.py::finalize_scan_session` | matching/creation par ISSN, `document_type=MAGAZINE_ISSUE` ; `_create_record` paramétré (`document_type`, `issn`) |
| Formulaire | `apps/catalog/forms.py` | champ `issn` + `clean_issn` |
| Templates | `_record_form.html`, `record_detail.html` | champ ISSN en édition + affichage |
| Scanner JS | `static/js/scan-camera.js`, `scan-cataloging.js` | `isAcceptableCode(v, allowIssn)` ; catalogage passe `allowIssn:true` |
| API | `apps/api/serializers.py` | `ScanKind.choices` inclut `issn` (additif ; OfeliaScan n'émet pas encore d'ISSN — contrat inchangé) |
| i18n | `scripts/translations_sprint21.py` | `ISSN`, aide + erreur de formulaire (EN/ES/MG) |

## Cas limites

- **Code 977 mal formé** (checksum ISSN incohérent) : `issn_from_ean13` renvoie
  `None` → `scan_add` répond « Code invalide » (400).
- **Saisie manuelle d'un ISSN** dans le formulaire de notice : validé par la clé
  de contrôle, stocké normalisé (`1828-552X` → `1828552X`), `NULL` si vide.
- **Prêt / retour** : un code 977 y reste rejeté (filtre global inchangé).

## Tests

- `apps/core/tests/test_issn.py` — clé de contrôle, extraction EAN→ISSN, rejet ISBN.
- `apps/catalog/tests/test_cataloging.py` — `scan_add` 977 → `scan_kind=issn` ;
  finalisation → notice `magazine_issue` + ISSN ; deux numéros même ISSN → 1 notice.
- `apps/catalog/tests/test_forms.py` — `clean_issn` valide / invalide / vide.
- `apps/core/tests/test_search.py` — `classify_query` : EAN13 977 → issn, ISSN saisi → issn, clé fausse → text.

## Recherche (findabilité)

Un périodique se retrouve dans le catalogue de trois façons, toutes routées par
`classify_query` vers le `kind="issn"` :
1. **scanner le code-barres 977** (l'ISSN est extrait de l'EAN),
2. **taper l'ISSN avec tiret** (`1828-552X`),
3. **taper l'ISSN sans tiret** (`1828552X`).

> Note : si aucune source (BnF/BNE) ne connaît l'ISSN au moment du scan, la
> notice est créée avec un **titre placeholder** `ISBN:<issn> - <date>` (comme un
> livre sans lookup) ; le/la bibliothécaire le renomme ensuite via le formulaire
> de notice (titre + `series_volume` pour le numéro).
