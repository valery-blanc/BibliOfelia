# FEAT-051 — Filtre emplacement dans le catalogue

Statut : **EN TEST** (Val, 2026-06-05)

## Contexte

La page catalogue (`catalog:record_list`) propose déjà des filtres catégorie,
type de document, langue et tag. Val souhaite pouvoir aussi filtrer les notices
par **emplacement** physique (`Location`), pour retrouver rapidement ce qui se
trouve dans un rayon / une étagère donnée.

## Comportement

- Un sélecteur « Tous emplacements / `<code>` » est ajouté à la barre de filtre,
  juste après le filtre langue. Il est alimenté par `Location.objects.all()`
  (ordonnés par `code`).
- L'emplacement étant porté par l'**exemplaire** (`Item.location`) et non par la
  notice, une notice est retenue dès qu'**au moins un** de ses exemplaires se
  trouve dans l'emplacement choisi.
- Le filtre se combine avec les filtres existants (catégorie, type, langue, tag,
  recherche texte/ISBN/EAN13) et avec la pagination.

## Spécification technique

### Vue — `apps/catalog/views.py::record_list`

```python
location = request.GET.get("location") or ""
if location:
    # Notices ayant au moins un exemplaire dans cet emplacement.
    records = records.filter(items__location_id=location).distinct()
```

- `.distinct()` indispensable : la jointure `items__location_id` peut dupliquer
  une notice ayant plusieurs exemplaires dans le même emplacement.
- Contexte enrichi : `locations` (liste pour le `<select>`) + `selected.location`
  (valeur courante pour ré-afficher la sélection).

### Template — `templates/catalog/record_list.html`

```django
<select name="location" class="filter-select" style="width:auto;min-width:150px">
    <option value="">{% trans "Tous emplacements" %}</option>
    {% for loc in locations %}
    <option value="{{ loc.pk }}" {% if selected.location == loc.pk|stringformat:'s' %}selected{% endif %}>{{ loc.code }}</option>
    {% endfor %}
</select>
```

## Impact

- **Migration** : aucune (lecture seule sur modèles existants).
- **i18n** : 1 nouvelle chaîne FR « Tous emplacements » → EN `All locations`,
  ES `Todas las ubicaciones`, MG `Toerana rehetra`
  (`scripts/translations_sprint20.py`). Gate `i18n_check.py` → 0.
- **Limite connue (pré-existante)** : les liens de pagination ne conservent que
  `q` et `q_tag` ; changer de page réinitialise les filtres `select` (catégorie,
  type, langue, emplacement). Comportement identique pour tous les filtres
  `select` — hors périmètre de cette feature.

## Fichiers touchés

- `apps/catalog/views.py` — filtre + contexte
- `templates/catalog/record_list.html` — `<select name="location">`
- `scripts/translations_sprint20.py` — chaîne « Tous emplacements »
- `docs/specs/SPEC_BIBLIOFELIA.md` — §6.1 + en-tête
- `docs/tasks/TASKS.md` — checklist FEAT-051
