# FEAT-042 — Traductions FR→EN/ES/MG des catégories par défaut

**Status :** IN PROGRESS
**Date :** 2026-05-27
**Sprint :** 13
**Spec parent :** `SPEC_BIBLIOFELIA.md` §5.2 (seed) + §6.9 (i18n)

---

## Contexte

Le seed (`apps/core/management/commands/seed_defaults.py`) crée 16 `Category`
et 5 `MemberCategory` avec un `name` FR. `modeltranslation` est enregistré
sur `Category.name` + `Tag.name` + `MemberCategory.name` (FEAT-003), ce qui
crée les colonnes `name_fr`, `name_en`, `name_es`, `name_mg`.

**Constat :** seul `name_fr` est rempli au seed. Conséquence, quand l'UI est
en EN/ES/MG, les noms de catégories restent en français.

## Comportement

- Lors du `seed_defaults` (premier boot ou re-exécution sur installation
  existante), chaque `Category` et `MemberCategory` créée a ses 4 champs
  `name_<lang>` remplis.
- Pour les installations existantes (catégories déjà créées avec uniquement
  `name_fr`) : `seed_defaults` met à jour les `name_en` / `name_es` /
  `name_mg` **uniquement s'ils sont vides** (préserve toute traduction
  manuelle du bibliothécaire via /admin/).

## Mapping de traduction

### Categories (16)

| code      | FR                  | EN                       | ES                       | MG                        |
|-----------|---------------------|--------------------------|--------------------------|---------------------------|
| ENF       | Enfance             | Childhood                | Infancia                 | Fahazazana                |
| ENF-ALB   | Albums              | Picture books            | Álbumes ilustrados       | Boky misy sary            |
| ENF-LEC   | Premières lectures  | Early reading            | Primeras lecturas        | Famakiana voalohany       |
| ENF-ROM   | Romans jeunesse     | Children's novels        | Novelas juveniles        | Tantara ho an'ny ankizy   |
| ADU       | Adultes             | Adults                   | Adultos                  | Olon-dehibe               |
| ADU-ROM   | Romans              | Novels                   | Novelas                  | Tantara foronina          |
| ADU-NOU   | Nouvelles           | Short stories            | Cuentos                  | Tantara fohy              |
| ADU-POE   | Poésie              | Poetry                   | Poesía                   | Tononkalo                 |
| ADU-THE   | Théâtre             | Theatre                  | Teatro                   | Tantara an-tsehatra       |
| DOC       | Documentaires       | Non-fiction              | Documentales             | Boky fampianarana         |
| DOC-SCI   | Sciences            | Sciences                 | Ciencias                 | Siansa                    |
| DOC-HIS   | Histoire            | History                  | Historia                 | Tantara                   |
| DOC-GEO   | Géographie          | Geography                | Geografía                | Jeografia                 |
| DOC-PRA   | Pratique            | Practical                | Práctico                 | Fampiharana               |
| DOC-REL   | Religions           | Religions                | Religiones               | Fivavahana                |
| PER       | Périodiques         | Periodicals              | Publicaciones periódicas | Gazety sy gazety boky     |

### MemberCategories (5)

| code        | FR                          | EN                            | ES                              | MG                             |
|-------------|-----------------------------|-------------------------------|---------------------------------|--------------------------------|
| ENFANT      | Enfant (< 14 ans)           | Child (under 14)              | Niño (menor de 14 años)         | Ankizy (latsaky ny 14 taona)   |
| ADO         | Adolescent (14-17 ans)      | Teenager (14-17)              | Adolescente (14-17 años)        | Tanora (14-17 taona)           |
| ADULTE      | Adulte                      | Adult                         | Adulto                          | Olon-dehibe                    |
| ENSEIGNANT  | Enseignant                  | Teacher                       | Docente                         | Mpampianatra                   |
| COLLECTIF   | Collectif (école/famille)   | Group (school/family)         | Colectivo (escuela/familia)     | Vondrona (sekoly/fianakaviana) |

## Technique

- Étendre `apps/core/management/commands/seed_defaults.py` :
  - Tuples `CATEGORIES` enrichis avec `(name_fr, name_en, name_es, name_mg)`.
  - À la création : `Category.objects.get_or_create(code=..., defaults={
    'name': name_fr, 'name_fr': name_fr, 'name_en': name_en, ...})`.
  - Pour les existants : `if not obj.name_en: obj.name_en = name_en; obj.save()`.
- Idem `MEMBER_CATEGORIES`.
- Ré-exécution `seed_defaults` (idempotente) backfille les installations
  existantes.

## Tests

- `apps/catalog/tests/test_seed_translations.py`
  - Après seed : `Category.objects.get(code='ENF').name_en == 'Childhood'` etc.
  - Préservation des traductions manuelles : si `name_en` est déjà rempli
    (non-vide, non-FR), re-exécution ne l'écrase pas.
- Idem `apps/members/tests/test_seed_translations.py`.

## Impact

- `apps/core/management/commands/seed_defaults.py`
- `apps/catalog/tests/`, `apps/members/tests/`
- `docs/specs/SPEC_BIBLIOFELIA.md` §5.2 (mention seed multilingue)
