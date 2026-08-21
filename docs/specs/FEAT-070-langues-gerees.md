# FEAT-070 — Liste de langues gérée (documents et usagers)

**Status:** DONE
**Date:** 2026-08-20

## Contexte

La langue d'un livre est aujourd'hui choisie parmi les **4 langues de
l'interface** (fr, en, es, mg) : impossible de cataloguer un livre en allemand
ou en tamoul. Et le filtre langue du catalogue affiche ces mêmes 4 langues,
alors que la base contient déjà de l'allemand et des codes hérités de la BnF
(`fre-fre`, `fre-eng`, `fre-jpn` — 94 notices sur la Box), invisibles au filtre.

FEAT-065 a par ailleurs introduit une liste de 22 langues parlées, figée dans le
code. Deux listes de langues dans la même application, c'est une de trop.

## Comportement

Une **liste de langues unique et gérée**, partagée par la langue des documents
et les langues parlées des usagers.

- 22 langues au départ (Français, Anglais, Portugais, Espagnol, Italien,
  Allemand, Arabe, Albanais, Turc, Russe, Serbo-croate, Tamoul, Chinois,
  Polonais, Persan, Farsi, Grec, Somali, Roumain, Ukrainien, Japonais,
  Malgache), noms traduits en FR/EN/ES/MG.
- **Codes internationaux principaux, sans variante régionale** : `fr` couvre le
  français de France, du Canada et de Suisse ; `pt` couvre le portugais et le
  brésilien.
- **Menus déroulants triés par ordre alphabétique** du libellé, dans la langue
  de l'interface — l'ordre change donc d'une langue à l'autre, ce qui est
  l'effet voulu.
- **Extensible** : écran **Avancé → Langues** (bibliothécaire) et admin Django.

La **langue de correspondance** de l'usager (`preferred_language`) reste limitée
aux langues de l'interface : BibliOfelia ne sait écrire que dans celles-là.

### Reprise des données existantes

Les codes hérités sont normalisés à la migration : on garde la **première**
langue et on la convertit en code à 2 lettres (`fre-fre` → `fr`,
`eng-fre` → `en`, `fre-jpn` → `fr`, `spa` → `es`…). Une langue inconnue de la
liste est **conservée telle quelle** : on ne perd jamais une donnée qu'on ne
sait pas nommer.

## Spec technique

- Modèle `catalog.Language` : `code` (10, unique), `name` (traduit
  modeltranslation, comme `Category`), `sort_order` non nécessaire (tri par
  libellé traduit à l'affichage).
- Seed dans `seed_defaults` (idempotent, backfill des traductions vides).
- `BibliographicRecord.language` reste un `CharField` : les choix viennent de la
  table, mais un code inconnu reste stockable (imports, sources en ligne).
- `apps/catalog/languages.py` : `language_choices()` (triées par libellé traduit)
  et `normalize_language_code()` (ISO 639-2 → 639-1, découpe sur `-`).
- `apps/members/languages.py` (FEAT-065) devient un **proxy** sur la table :
  mêmes codes, plus de liste figée.
- Migration de données : normalisation des `BibliographicRecord.language`.
- Écran `language_list` / `language_create` / `language_edit` /
  `language_delete`, calqué sur les catégories.

## Impact sur l'existant

- `apps/catalog/models.py` (+ migrations), `forms.py`, `views.py`, `urls.py`,
  `translation.py`, `admin.py`.
- `apps/core/management/commands/seed_defaults.py`.
- `apps/members/languages.py`, `apps/members/forms.py`.
- `templates/catalog/record_list.html` (filtre langue), nouveaux templates
  `catalog/language_*.html`, `templates/core/advanced.html`.

## Implémentation

- Modèle `catalog.Language` (`code`, `name` traduit via modeltranslation) —
  migration `catalog/0016`, seed des 22 langues dans `seed_defaults`.
- `apps/catalog/languages.py` : `normalize_language_code`, `language_choices`
  (triées par libellé **traduit**, donc l'ordre suit la langue de l'interface),
  `label_for`.
- Migration de données `catalog/0017` : normalisation des codes hérités
  (`fre-fre` → `fr`, `eng-fre` → `en`…). Réversible en no-op assumé — rien n'est
  détruit, les codes composites d'origine n'ont pas d'intérêt à être restaurés.
- `BibliographicRecordForm`, filtre du catalogue et lot de scan branchés dessus ;
  `apps/members/languages.py` devient un adaptateur sur la même table.
- `choices` passé en **callable** aux widgets : la liste est modifiable pendant
  que le serveur tourne, la figer à l'import masquerait toute langue ajoutée.
- Écran Avancé → Langues + `LanguageAdmin` (TranslationAdmin).
- Tests : `apps/catalog/tests/test_languages.py` (32 cas).
