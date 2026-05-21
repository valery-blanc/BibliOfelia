# FEAT-002 — Modèles de données v1

Statut : **DONE** (2026-05-21)
Sprint : 1 (Domaine)
Task : #2 de `docs/tasks/TASKS.md`
Spec : `docs/specs/SPEC_BIBLIOFELIA.md` §5

## Contexte

Sprint 0 a livré le squelette du projet (Django + Docker + User étendu + Setting).
Cette feature pose toute la couche domaine v1 : 10 modèles métier + indexes + FTS5 SQLite + seed des catégories.

## Périmètre

### Apps concernées

| App | Fichier | Modèles |
|---|---|---|
| `apps.catalog` | `models.py` | Author, Category, Tag, Location, BibliographicRecord, Item |
| `apps.members` | `models.py` | MemberCategory, Member |
| `apps.loans` | `models.py` | Loan, InHouseConsultation, Reservation |

### Conformité §5.2

Tous les champs listés en spec §5.2 sont implémentés à l'identique sauf
trois écarts mineurs documentés ici :

- **`BibliographicRecord.subtitle`** : `CharField(blank=True)` plutôt que nullable
  (la spec dit "nullable"). Convention Django : pour les `CharField`, on évite
  `null=True` au profit de `blank=True` (chaîne vide). Comportement métier identique.
- **`Member.replaces_card_number`** : `CharField(blank=True)` même justification.
- **`Item.acquisition_date`** : `default=date.today` (callable, pas d'override migration).

### Génération automatique des codes (§5.2)

- **`Item.internal_id`** = `OFL-YYYYMMDD-NNNN` (NNNN = compteur réinitialisé chaque jour).
  Assigné dans `Item.save()` sur premier `pk` connu.
- **`Item.ean13`** = préfixe `290` + `pk` zero-paddé 9 chiffres + checksum EAN-13.
- **`Member.card_number`** = préfixe `291` + `pk` zero-paddé 9 chiffres + checksum.
- Algo dans `apps.core.ean.build_ean13` (déjà livré Sprint 0).

### `Member.expiration_date`

Auto-calculé à la création si non fourni : `registration_date + category.card_validity_months`
(via `dateutil.relativedelta`).

### Indexes §5.3

| Index | Modèle | Type |
|---|---|---|
| `isbn_13` unique partial (non-null) | BibliographicRecord | UniqueConstraint conditionnel |
| `isbn_10` | BibliographicRecord | db_index |
| `internal_id` unique | Item | unique=True |
| `ean13` unique | Item | unique=True |
| `(status, location)` | Item | Index composite |
| `card_number` unique | Member | unique=True |
| `(last_name, first_name)` | Member | Index composite |
| `(member, status)` | Loan | Index composite |
| `(due_date, status)` | Loan | Index composite |
| `status` | Reservation | Index simple |

### FTS5 (§5.3)

Migration `apps/catalog/migrations/0002_fts5.py` (RunSQL) :

- Table virtuelle `catalog_record_fts` (FTS5) avec colonnes
  `title`, `subtitle`, `summary`, `authors_concat`, `record_id` (UNINDEXED).
- Tokenizer `unicode61 remove_diacritics 2` (recherche tolérante aux accents).
- Triggers :
  - `*_ai` AFTER INSERT sur `BibliographicRecord`
  - `*_ad` AFTER DELETE sur `BibliographicRecord`
  - `*_au` AFTER UPDATE sur `BibliographicRecord`
  - `*_m2m_ai` AFTER INSERT sur la table M2M `_authors` (resync auteurs concaténés)
  - `*_m2m_ad` AFTER DELETE sur M2M `_authors`
- `authors_concat` est généré par sous-SELECT `group_concat(full_name, ' ')`
  sur la table M2M jointe à `catalog_author`.
- `reverse_sql` complet pour permettre `migrate catalog zero`.

### Seed (§5.2)

`apps.core.management.commands.seed_defaults` étoffé (toujours idempotent) :

- **16 Catégories** :
  - Enfance : Albums, Premières lectures, Romans jeunesse
  - Adultes : Romans, Nouvelles, Poésie, Théâtre
  - Documentaires : Sciences, Histoire, Géographie, Pratique, Religions
  - Périodiques (loan_duration=7j)
- **5 MemberCategory** :
  - ENFANT (3 prêts / 21j)
  - ADO (5 / 21)
  - ADULTE (5 / 21)
  - ENSEIGNANT (15 / 60)
  - COLLECTIF (20 / 30)

### Admin Django

Admin minimal pour les 10 modèles + User étendu, avec `search_fields` et
`autocomplete_fields` cohérents (catalog/members/loans/accounts/admin.py).
Objectif : navigation et debug pendant les sprints suivants — sera remplacé
par les écrans HTMX en Sprint 2.

## i18n / modeltranslation — différé Task #3

Les champs traduisibles (`Category.name`, `Tag.name`, `MemberCategory.name`)
sont déclarés en `CharField` simple. La feature **FEAT-003** (Task #3)
enregistrera les `TranslationOptions` et générera la migration additive
créant `name_fr`, `name_en`, `name_es`, `name_mg`. Le seed est en français
et sera la valeur de fallback.

## Vérifications effectuées

- `docker compose exec web python manage.py check` : 0 issues.
- `makemigrations` : 3 migrations + 1 migration FTS5 RunSQL.
- `migrate` : applique tout, sans erreur.
- `seed_defaults` : 16 Category + 5 MemberCategory créés.
- Création Item → `internal_id=OFL-20260521-0001`, `ean13=2900000000018` valide.
- Création Member → `card_number=2910000000017` valide, `expiration_date=+12 mois`.
- Création Loan → status `active`.
- FTS5 : `SELECT title FROM catalog_record_fts WHERE catalog_record_fts MATCH 'test'`
  retourne la ligne attendue (titre + auteurs concaténés).
- Admin : `/admin/`, `/admin/catalog/bibliographicrecord/`, `/admin/catalog/item/`,
  `/admin/members/member/`, `/admin/loans/loan/` rendent en 200.

## Suite

- Task #3 : modeltranslation sur les champs `name`, génération des .po français.
- Task #4 : groupes/permissions par `Role`, throttling DRF déjà configuré (§9), audit log register.
