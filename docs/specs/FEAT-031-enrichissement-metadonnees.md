# FEAT-031 — Enrichissement métadonnées du catalogue (multi-sources, async)

**Status :** DONE
**Date :** 2026-05-23
**Sprint :** 9
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.1 + nouvelle sous-section §6.11

---

## Contexte

Le catalogue contient des notices saisies manuellement, importées depuis
OpenLibrary unitairement (lookup ISBN à la création), ou créées via
OfeliaScan. La qualité varie : nombreuses notices avec auteurs vides,
publisher manquant, année floue. Plutôt que de re-saisir notice par notice,
on veut une action **batch** qui interroge plusieurs sources externes pour
compléter le fonds.

Décisions validées par Val (2026-05-23) :
- 4 sources : **OpenLibrary** (existante), **Google Books** (clé API
  obligatoire), **BNF** (SRU, sans clé), **BNE** (SRU, sans clé).
- Tâche **asynchrone django-q2** (le fonds peut faire plusieurs milliers de
  notices, on ne peut pas bloquer une requête HTTP).
- Choix utilisateur à chaque lancement : mode **« compléter seulement »**
  (défaut, ne touche pas les champs déjà remplis) ou **« écraser »** (la
  source remplace la valeur locale si la source répond).
- Rapport final visible dans l'UI : N notices traitées, N mises à jour, N
  inchangées, N erreurs.

---

## Comportement

### 1. Paramètres → Sources de métadonnées

Nouvelle entrée dans `core:settings_index` : **« Sources de métadonnées »**
(`core:settings_section` avec section="sources"). Permet de saisir :

- `google_books_api_key` (champ texte, obligatoire pour activer Google
  Books). Persistance via `Setting.set("google_books_api_key", ...)`.
- Toggle on/off par source (4 cases à cocher).

### 2. Avancé → Enrichissement métadonnées

Nouvelle page `core:enrichment_index` (rôle superadmin) :

- **Tableau des jobs passés** (date de lancement, mode, scope, total,
  updated, erreurs, état : `pending`/`running`/`finished`/`failed`).
- **Bouton « Lancer un nouvel enrichissement »** → formulaire :
  - **Scope** : Toutes les notices / Notices créées avant date / Notices
    sans auteur / Sélection ISBN précise (textarea liste).
  - **Mode** : `fill_missing` (défaut) / `overwrite`.
  - **Sources** : 4 cases (cases pré-cochées = sources actives dans
    Settings).
  - Bouton « Lancer ».

À la soumission : crée un `EnrichmentJob(state=PENDING)`, queue la tâche
django-q2 `apps.catalog.enrichment.run_enrichment_job(job_id)`, redirige
vers la liste des jobs avec message « Tâche lancée, suivez l'avancement
ici ».

### 3. Détail d'un job

Page `core:enrichment_detail(job_id)` : statut + barre de progression
(rafraîchissement HTMX toutes les 3 s) + table de résultats par notice
(récap des changements appliqués / erreurs).

### 4. Tâche asynchrone (django-q2)

`apps.catalog.enrichment.run_enrichment_job(job_id)` :
1. Charge le job, passe en `RUNNING`.
2. Calcule le périmètre (queryset de `BibliographicRecord`).
3. Pour chaque notice avec un ISBN :
   - Itère sur les sources actives (ordre : Google Books → OpenLibrary →
     BNF → BNE — basé sur la couverture observée).
   - Première source qui répond → merge dans la notice selon le mode.
   - Sauvegarde la notice (`updated_at` auto). Incrémente `processed`,
     `updated`, `skipped`, `errors` dans le job.
   - Append entrée dans `job.report` (JSON list).
4. À la fin : passe en `FINISHED` (ou `FAILED` si exception non gérée).

Throttling : `time.sleep(0.5)` entre chaque appel HTTP pour rester
respectueux des API publiques.

---

## Spec technique

### Modèle `EnrichmentJob` (`apps/catalog/models.py`)

```python
class EnrichmentJobState(models.TextChoices):
    PENDING = "pending", _("En attente")
    RUNNING = "running", _("En cours")
    FINISHED = "finished", _("Terminé")
    FAILED = "failed", _("Échec")


class EnrichmentMode(models.TextChoices):
    FILL_MISSING = "fill_missing", _("Compléter les champs vides uniquement")
    OVERWRITE = "overwrite", _("Écraser avec les données externes")


class EnrichmentJob(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(max_length=12, choices=EnrichmentJobState.choices,
                              default=EnrichmentJobState.PENDING)
    mode = models.CharField(max_length=20, choices=EnrichmentMode.choices,
                             default=EnrichmentMode.FILL_MISSING)
    sources = models.JSONField(default=list)   # ["openlibrary", "google_books", "bnf", "bne"]
    scope_filter = models.JSONField(default=dict)  # {"kind": "all"|"no_author"|"before"|"isbns", ...}
    total = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    report = models.JSONField(default=list)  # [{record_id, isbn, source, changes, error}]
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name="enrichment_jobs", on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ["-started_at"]
```

Migration : `apps/catalog/migrations/0006_enrichment_job.py`.

### Module `apps/catalog/sources/`

Structure :
```
apps/catalog/sources/
├── __init__.py         # registry SOURCES = {"openlibrary": ..., "google_books": ..., "bnf": ..., "bne": ...}
├── openlibrary.py      # refacto existant (lookup_isbn → lookup)
├── google_books.py     # https://www.googleapis.com/books/v1/volumes?q=isbn:X&key=API_KEY
├── bnf.py              # SRU + parsing XML Dublin Core
└── bne.py              # SRU Alma (https://catalogo.bne.es/view/sru/34BNE_INST)
```

Chaque module expose :
```python
def lookup(isbn: str) -> dict | None:
    """Retourne un dict de champs : title, subtitle, authors_text, publisher,
    publication_year, language. Ou None si pas trouvé/erreur."""
```

Format de retour normalisé identique à `openlibrary.lookup_isbn` actuel,
avec ajout du champ `language` (code ISO 639-1).

### Service `apps/catalog/enrichment.py`

```python
SOURCE_FIELDS = ["title", "subtitle", "publisher", "publication_year",
                 "language", "summary"]
# Champs non touchés : authors (gérés séparément), category, tags, isbn_13/10.

def merge_record(record, data, mode):
    """Applique data sur record selon mode. Retourne dict des changements."""
    changes = {}
    for field in SOURCE_FIELDS:
        new = (data.get(field) or "").strip() if isinstance(data.get(field), str) else data.get(field)
        if new in (None, ""):
            continue
        current = getattr(record, field) or ""
        if mode == EnrichmentMode.FILL_MISSING and current:
            continue
        if new != current:
            setattr(record, field, new)
            changes[field] = {"old": current, "new": new}
    if data.get("authors_text"):
        # syncho auteurs uniquement si mode=overwrite ou record sans auteur
        ...
    if changes:
        record.metadata_source = MetadataSource.OPENLIBRARY  # ou la source qui a répondu
        record.metadata_quality = MetadataQuality.AUTO
        record.save()
    return changes


def run_enrichment_job(job_id: int) -> None:
    """Tâche django-q2."""
    job = EnrichmentJob.objects.get(pk=job_id)
    try:
        job.state = EnrichmentJobState.RUNNING
        job.save(update_fields=["state"])
        qs = _build_queryset(job.scope_filter)
        job.total = qs.count()
        job.save(update_fields=["total"])
        for record in qs.iterator():
            try:
                data, source_name = _try_sources(record.isbn_13 or record.isbn_10, job.sources)
                if data:
                    changes = merge_record(record, data, job.mode)
                    if changes:
                        job.updated += 1
                        job.report.append({"record_id": record.pk, "isbn": record.isbn_13 or record.isbn_10,
                                           "source": source_name, "changes": changes})
                    else:
                        job.skipped += 1
                else:
                    job.skipped += 1
            except Exception as exc:
                job.errors += 1
                job.report.append({"record_id": record.pk, "error": str(exc)})
            finally:
                job.processed += 1
                if job.processed % 10 == 0:
                    job.save(update_fields=["processed", "updated", "skipped", "errors", "report"])
                time.sleep(0.5)
        job.state = EnrichmentJobState.FINISHED
        job.finished_at = timezone.now()
        job.save()
    except Exception as exc:
        job.state = EnrichmentJobState.FAILED
        job.report.append({"global_error": str(exc)})
        job.finished_at = timezone.now()
        job.save()
```

### Vues (`apps/core/admin_views.py`)

- `enrichment_index` (GET) : liste des jobs + bouton "Lancer".
- `enrichment_start` (POST) : valide formulaire, crée job, queue
  `async_task("apps.catalog.enrichment.run_enrichment_job", job.pk)`.
- `enrichment_detail` (GET) : statut + rapport, HTMX poll si RUNNING.

### URLs (`apps/core/urls.py`)

```python
path("admin/enrichment/", views.enrichment_index, name="enrichment_index"),
path("admin/enrichment/start/", views.enrichment_start, name="enrichment_start"),
path("admin/enrichment/<int:pk>/", views.enrichment_detail, name="enrichment_detail"),
```

### Lien depuis `advanced.html`

Ajout d'une carte « Enrichissement métadonnées » à côté d'Impression /
Rapports / Inventaire / Administration.

### Settings (`apps/core/forms.py`)

Nouveau formulaire `MetadataSourcesForm` avec champs :
- `google_books_api_key` (CharField, password=False, blank=True).
- `openlibrary_enabled` (BooleanField, default=True).
- `google_books_enabled` (BooleanField, default=False).
- `bnf_enabled` (BooleanField, default=True).
- `bne_enabled` (BooleanField, default=True).

Persistance via `Setting.set` (clés : `metadata.sources`,
`metadata.google_books_api_key`).

---

## Impact sur l'existant

**Nouveaux fichiers :**
- `apps/catalog/sources/__init__.py`, `openlibrary.py`, `google_books.py`,
  `bnf.py`, `bne.py`.
- `apps/catalog/enrichment.py` (service + tâche q2).
- `apps/catalog/migrations/0006_enrichment_job.py`.
- `apps/catalog/tests/test_sources.py`, `test_enrichment.py`.
- `templates/core/admin/enrichment_index.html`,
  `enrichment_start.html`, `enrichment_detail.html`.

**Fichiers modifiés :**
- `apps/catalog/models.py` : +EnrichmentJob, EnrichmentJobState, EnrichmentMode.
- `apps/catalog/openlibrary.py` : `lookup_isbn` → wrapper qui appelle
  `sources.openlibrary.lookup` pour rester compatible avec l'usage
  existant (création de notice).
- `apps/core/admin_views.py` : +3 vues.
- `apps/core/urls.py` : +3 routes.
- `apps/core/forms.py` : +MetadataSourcesForm.
- `apps/core/views.py` ou `admin_views.py` : `settings_section` reconnaît
  section="sources".
- `templates/core/advanced.html` : +1 carte.

---

## Tests

### `apps/catalog/tests/test_sources.py`

- `test_openlibrary_lookup_normalizes_isbn` (avec mocked httpx)
- `test_google_books_lookup_uses_api_key`
- `test_google_books_lookup_returns_none_when_no_items`
- `test_bnf_sru_parses_dublin_core_xml`
- `test_bne_sru_parses_alma_xml`
- `test_bnf_returns_none_on_malformed_xml`

### `apps/catalog/tests/test_enrichment.py`

- `test_merge_record_fill_missing_does_not_overwrite_existing`
- `test_merge_record_overwrite_replaces_existing`
- `test_merge_record_skips_empty_source_values`
- `test_run_enrichment_job_marks_finished` (mocked sources)
- `test_run_enrichment_job_counts_errors`
- `test_build_queryset_no_author_scope`
- `test_run_enrichment_job_no_isbn_skipped`

### `apps/core/tests/test_enrichment_views.py`

- `test_enrichment_index_requires_superadmin`
- `test_enrichment_start_creates_job_and_queues_task` (mock async_task)
- `test_enrichment_detail_renders_report`

---

## Dépendances

Aucune nouvelle dépendance Python : `httpx` (déjà présent), parsing XML
via `xml.etree.ElementTree` (stdlib).

---

## Risques et limites

- **Rate limiting** : Google Books exige une clé API ; le quota gratuit
  est suffisant pour quelques milliers de lookups/jour. BNF et BNE n'ont
  pas de quota documenté mais on throttle à 0.5 s entre appels.
- **Timeouts** : timeout 10 s par source ; en cas d'échec on passe à la
  suivante.
- **Notices sans ISBN** : skipped (aucune source ne sait répondre sans
  ISBN). Documenté dans le rapport.
- **Auteurs** : merge délicat (texte libre côté local vs liste côté
  sources). On ne touche aux auteurs que si mode=overwrite OU notice sans
  auteur.

---

## Fix applied / Notes d'implémentation

À compléter après build/test.
