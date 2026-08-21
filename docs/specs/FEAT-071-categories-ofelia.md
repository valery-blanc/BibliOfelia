# FEAT-071 — Catégories officielles Ofelia

**Status:** DONE
**Date:** 2026-08-20

## Contexte

Les 16 catégories du seed d'origine (Enfance/Adultes/Documentaires/Périodiques)
ne correspondent pas au classement réellement utilisé par le projet. Val a
fourni la liste officielle : **5 tranches d'âge × 4 types de document**.

Sur grand-saconnex, les catégories portent en plus un préfixe de langue
(`FR AD FIC` / « Français Adultes Fiction ») : la langue est une propriété du
livre, pas de son rayon, et la dupliquer dans la catégorie multiplierait les
lignes sans rien apporter.

## Comportement

### La liste

| Code / cote | Nom |
|---|---|
| `AD FIC` | Adultes Fiction |
| `AD DOC` | Adultes Documentaire |
| `AD ALB` | Adultes Album |
| `AD BD` | Adultes Bande dessinée |
| `JE FIC` | Jeunesse Fiction |
| `JE DOC` | Jeunesse Documentaire |
| `JE ALB` | Jeunesse Album |
| `JE BD` | Jeunesse Bande dessinée |
| `ADO FIC` | Adolescents Fiction |
| `ADO DOC` | Adolescents Documentaire |
| `ADO ALB` | Adolescents Album |
| `ADO BD` | Adolescents Bande dessinée |
| `EN FIC` | Enfants Fiction |
| `EN DOC` | Enfants Documentaire |
| `EN ALB` | Enfants Album |
| `EN BD` | Enfants Bande dessinée |
| `PE FIC` | Petite enfance Fiction |
| `PE DOC` | Petite enfance Documentaire |
| `PE ALB` | Petite enfance Album |
| `PE BD` | Petite enfance Bande dessinée |

Le **code est identique à l'abréviation** : c'est déjà la convention des
catégories de grand-saconnex, et une cote qui diffère du code n'aurait aucune
justification ici.

Les noms sont traduits en EN/ES/MG ; les **codes ne sont jamais traduits** — une
cote est imprimée sur une étiquette physique.

> **Coquille relevée dans la liste fournie** : « Adolescents Fiction » y porte la
> cote `ADO DOC`, identique à « Adolescents Documentaire ». Corrigé en
> **`ADO FIC`**. Signalé à Val.

### Reprise des catégories existantes

Commande `python manage.py migrate_categories` (idempotente, `--dry-run`
disponible) :

1. **Retrait du préfixe de langue** : `FR AD FIC` → `AD FIC`, « Français Adultes
   Fiction » → « Adultes Fiction ». Le préfixe est reconnu sur le code (`FR `,
   `EN `, `ES `, `MG `… suivi d'un code connu) et sur le nom.
2. **Fusion** : si la catégorie cible existe déjà, les notices y sont déplacées
   et l'ancienne est supprimée. Sinon l'ancienne est renommée en place.
3. **Correspondance des anciennes catégories du seed** (décision Val
   2026-08-20 : remapper puis supprimer) :
   `ADU-ROM`/`ADU-NOU` → `AD FIC` ; `DOC-*` → `AD DOC` ; `ENF-ALB` → `EN ALB` ;
   `ENF-LEC`/`ENF-ROM` → `EN FIC` ; `ADU-POE`/`ADU-THE` → `AD FIC` ;
   `PER` → `AD DOC` ; les catégories parentes vides (`ENF`, `ADU`, `DOC`) sont
   supprimées.
4. Toute catégorie qui n'entre dans aucun cas est **laissée intacte** et
   signalée dans le compte rendu : la commande ne supprime jamais une catégorie
   qu'elle n'a pas su reclasser.

## Spec technique

- `seed_defaults` : `CATEGORIES` remplacé par les 20 entrées (code = cote), avec
  les 4 langues. Plus de hiérarchie parent : les tranches d'âge ne sont plus des
  catégories à part entière.
- `apps/catalog/management/commands/migrate_categories.py` : `--dry-run`,
  compte rendu ligne à ligne, transaction unique.
- Sur une base neuve, le seed suffit ; la commande ne sert qu'aux bases
  existantes (Box, grand-saconnex).

## Impact sur l'existant

- `apps/core/management/commands/seed_defaults.py`.
- Nouvelle commande `migrate_categories`.
- Bases : Box (32 notices catégorisées, données de démo) et grand-saconnex
  (104 notices, 11 catégories préfixées `FR `).

## Implémentation

- `seed_defaults` : `CATEGORIES` construit par produit `_AGE_GROUPS ×
  _DOC_KINDS` — 20 lignes × 5 colonnes recopiées à la main, c'est une coquille
  assurée (celle de la liste fournie en est la preuve).
- `apps/catalog/management/commands/migrate_categories.py` : `--dry-run`,
  idempotente, compte rendu ligne à ligne. Ne supprime jamais une catégorie
  qu'elle n'a pas su reclasser.
- Tests : `apps/catalog/tests/test_categories_migration.py` (15 cas), dont
  « une catégorie inconnue survit » et « aucune notice ne perd sa catégorie ».
