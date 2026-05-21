# FEAT-003 — i18n + modeltranslation (4 langues)

Statut : **DONE** (2026-05-21)
Sprint : 1 (Domaine)
Task : #3 de `docs/tasks/TASKS.md`
Spec : `docs/specs/SPEC_BIBLIOFELIA.md` §6.9

## Contexte

L'app cible 4 langues : **fr** (par défaut), **en**, **es**, **mg** (Malagasy).
- Les **chaînes de l'interface** (Python `_("texte")` + templates) passent par
  Django i18n (`django.po` / `django.mo`).
- Les **valeurs de référentiel** (noms de catégories, tags, catégories d'usager)
  sont stockées en base avec une colonne par langue via `django-modeltranslation`.

## Périmètre

### Champs traduits par modeltranslation

| Modèle | Champ | Fichier translation |
|---|---|---|
| `catalog.Category` | `name` | `apps/catalog/translation.py` |
| `catalog.Tag` | `name` | `apps/catalog/translation.py` |
| `members.MemberCategory` | `name` | `apps/members/translation.py` |

Modeltranslation crée à la migration : `name_fr`, `name_en`, `name_es`, `name_mg`.
Le champ canonique `name` reste présent et se comporte au runtime comme une
property qui retourne le champ de la langue active (avec fallback sur `fr`).

### Non-traduits (volontairement)

- `Author.notes`, `BibliographicRecord.summary` → contenu propre à un livre,
  pas une terminologie partagée.
- `Location.description` → label local au site, créé par la bibliothèque.
- `Author.full_name` → nom propre, identique dans toutes les langues.

### Migrations

1. `catalog/0003_translation_fields.py` — ADD COLUMN `name_fr/en/es/mg` sur Category, Tag.
2. `catalog/0004_backfill_translation_fr.py` — `UPDATE … SET name_fr = name` (RunPython).
3. `members/0002_translation_fields.py` — ADD COLUMN pour MemberCategory.
4. `members/0003_backfill_translation_fr.py` — backfill `name → name_fr`.

Les fichiers générés par `makemigrations` ont été renommés pour clarté
(`0003_category_name_en_..._and_more.py` → `0003_translation_fields.py`).

### Admin

`apps/catalog/admin.py` et `apps/members/admin.py` :
les classes des 3 modèles traduits héritent désormais de
`modeltranslation.admin.TranslationAdmin` au lieu de `admin.ModelAdmin`.
Le formulaire d'édition affiche 4 champs `name_xx` côte à côte (un par langue).

### Code de langue Malagasy

Django 5.1 ne livre pas `mg` dans `django.conf.locale.LANG_INFO`. Sans
enregistrement, `modeltranslation.admin.TranslationAdmin` lève
`KeyError: 'Unknown language code mg.'` au rendu du formulaire d'édition.

Fix dans `config/settings/base.py` :

```python
from django.conf.locale import LANG_INFO
LANG_INFO.setdefault("mg", {
    "bidi": False, "code": "mg",
    "name": "Malagasy", "name_local": "Malagasy",
})
```

### Fichiers de traduction Python (.po / .mo)

- `locale/{fr,en,es,mg}/LC_MESSAGES/django.po` créés par
  `python manage.py makemessages -l fr -l en -l es -l mg --no-location`.
- 83 `msgid` extraits (labels DocumentType, MemberStatus, etc. + verbose_name).
- **Stratégie v1** : remplir uniquement `fr` (msgstr peut rester vide → fallback msgid déjà en français). Les `.po` `en/es/mg` sont créés vides et seront traduits ultérieurement (ou par contributeur externe). Django fallback configuré (`MODELTRANSLATION_FALLBACK_LANGUAGES = ('fr',)`).
- `.mo` compilés via `compilemessages`, ajoutés au `dev-entrypoint.sh` pour
  régénération automatique au boot (les `.mo` sont gitignorés — artefact).

### Wiring i18n existant (Sprint 0)

Déjà en place avant FEAT-003, vérifié :

- `LocaleMiddleware` actif après `SessionMiddleware`.
- URLs `/i18n/setlang/` exposées par `django.conf.urls.i18n`.
- `i18n_patterns` enveloppe les apps métier (`/catalog/`, `/members/`, …)
  avec `prefix_default_language=False`.
- `MODELTRANSLATION_LANGUAGES` et `MODELTRANSLATION_FALLBACK_LANGUAGES` set.

### Sélecteur de langue côté UI

**Non livré ici** — fait partie de Task #5 (UI base, Sprint 2). En attendant,
le switch se fait via POST sur `/i18n/setlang/` (cookie `django_language`).

## Vérifications effectuées

- `manage.py check` : 0 issue.
- `makemigrations` + `migrate` : 4 migrations appliquées proprement.
- Smoke test ORM :
  - `Category(ADU-ROM).name_fr = 'Romans'` après backfill.
  - `Tag.objects.create(name='X')` → `name_fr='X'` automatique.
  - `translation.activate('en')` puis `.refresh_from_db()` → `name = name_en`.
  - Activé `mg`, `name_mg` vide → fallback `name_fr = 'Romans'`.
- Smoke test admin :
  - `/admin/catalog/category/{id}/change/` retourne 200 et le HTML contient
    les 4 champs `name_fr`, `name_en`, `name_es`, `name_mg`.
  - `/admin/catalog/category/`, `/admin/catalog/tag/`,
    `/admin/members/membercategory/` rendent en 200.

## Suite

- Task #4 (Sprint 1) : rôles/permissions Django Group par `Role`, throttling DRF
  affiné, `auditlog.register(...)` explicite pour les modèles sensibles.
- Task #5 (Sprint 2) : sélecteur de langue dans le layout HTMX (POST `/i18n/setlang/`).
