---
id: FEAT-050
title: Catalogage Excel — vérification + import
status: DONE
created: 2026-06-05
approved: 2026-06-05
implemented: 2026-06-05
owner: Val
---

# FEAT-050 — Catalogage Excel

> Nouveau menu **Avancé → Inventaire → Catalogage Excel** offrant deux outils
> au bibliothécaire pour traiter un fonds existant fourni sous forme de
> tableur :
>
> 1. **Vérification d'un fichier** — annote l'Excel avec ce que les sources en
>    ligne (OpenLibrary, Google Books, BNF, BNE) connaissent du livre, par
>    ISBN d'abord, puis par titre+auteur en repli.
> 2. **Import dans BibliOfelia** — matérialise une liste d'ISBN en notices et
>    exemplaires via une **ScanSession virtuelle**, exactement comme un
>    catalogage caméra continu.

## Contexte / motivation

Beaucoup de bibliothèques rejoignant le projet Ofelia ont déjà un inventaire
sous forme de tableur Excel/LibreOffice (ID maison, titre, auteur, ISBN parfois
incomplet). Deux besoins distincts :

- **Avant migration** — vérifier la qualité du fichier source : combien
  d'ISBN sont reconnus, combien de titres tapés peuvent être appariés aux
  bases de données ; produire un fichier annoté à corriger à la main.
- **Pendant migration** — basculer en lot des ISBN dans BibliOfelia sans
  passer par le scanner caméra ligne par ligne.

L'enrichissement métadonnées (FEAT-031) ne couvre que des notices déjà
créées par ISBN. Cette feature comble le trou en amont (fichier brut) et en
aval (import direct).

## Périmètre — hors périmètre

### Dans le périmètre

- 1 nouvelle entrée dans `templates/core/advanced.html` (section
  Inventaire, accès `is_librarian`).
- Page de garde avec 2 onglets / sections : **Vérifier** et **Importer**.
- Lecture `.xlsx` (openpyxl). Le `.xls` legacy et le `.csv` sont **hors
  périmètre** v1 — message explicite si format non supporté.
- Fonction `search(title, author)` ajoutée à chaque source dans
  `apps/catalog/sources/*.py` (en plus de `lookup(isbn)` existant).
- Re-classement fuzzy local via `rapidfuzz` (nouvelle dépendance) pour les
  sources strictes (BNF, BNE) + production d'un score de confiance 0-100.
- Job django-q2 `run_excel_catalog_job(job_id)` avec un nouveau modèle
  `ExcelCatalogJob` (calqué sur `EnrichmentJob`).
- Mode **VERIFY** : produit un fichier annoté téléchargeable.
- Mode **IMPORT** : crée une `ScanSession` virtuelle + ses `ScanItem`, puis
  appelle `finalize_scan_session()` (réutilisation directe du pipeline
  FEAT-021 / FEAT-046).

### Hors périmètre v1

- Édition en ligne de l'Excel dans l'UI BibliOfelia (on télécharge, on
  corrige hors-ligne, on ré-importe).
- Détection de doublons inter-fichier — chaque ligne est traitée comme
  indépendante (le matching d'ISBN existants côté BibliOfelia est fait par
  `finalize_scan_session` qui gère déjà le cas).
- Sélection manuelle parmi plusieurs candidats (passe 2). On garde **Top 1
  + score de confiance** (cf. décision Val 2026-06-05).
- Compatibilité OfeliaScan mobile (pas de lien direct).
- Mise à jour de notices existantes (c'est le rôle de FEAT-031).

## Décisions de design (validées Val 2026-06-05)

| Décision | Choix retenu |
|---|---|
| Passe 2 multi-candidats | **Top 1 + colonne CONFIDENCE (0-100)** |
| Mode IMPORT — pipeline | **Création d'une ScanSession virtuelle**, label `Import Excel — <date>`, visible dans `/catalog/scan-sessions/` |
| Sources passe 2 | **Les 4 sources** (Google Books, OpenLibrary, BNF, BNE) en parallèle, fusion par score |

## Spécification fonctionnelle

### Fonctionnalité 1 — Vérification (mode VERIFY)

**Entrée** : fichier `.xlsx` avec **au moins 4 colonnes nommées** (insensible
à la casse, accents tolérés) : `ID`, `TITLE`, `AUTHOR`, `ISBN`. Toute autre
colonne est conservée telle quelle dans la sortie. Première ligne =
en-têtes. Les lignes vides sont ignorées.

**Pipeline** :

1. **Validation du fichier**
   - Format `.xlsx` uniquement (refus explicite `.xls`/`.csv`/`.ods` en v1).
   - 4 colonnes obligatoires présentes.
   - Taille max 5 Mo, 10 000 lignes max (gardes-fous).
   - Si KO → message d'erreur sur la page d'upload, pas de job créé.

2. **Passe 1 — par ISBN**
   - Pour chaque ligne avec un `ISBN` non vide :
     - Normaliser (retirer espaces / tirets / `X` final OK).
     - Si longueur ∉ {10, 13} → marquer `ISBN_INVALID` dans une colonne
       diagnostique, passer à la suivante.
     - Interroger les 4 sources en parallèle via `_try_sources(isbn, …)`
       (existant FEAT-031).
     - Première source qui répond → renseigne :
       - `TITLE_FOUND_BY_ISBN`
       - `AUTHOR_FOUND_BY_ISBN` (joints par `; ` si plusieurs)
       - `SOURCE_BY_ISBN` (`openlibrary` / `google_books` / `bnf` / `bne`)

3. **Passe 2 — par TITLE + AUTHOR**
   - Périmètre : **toutes les lignes ayant un titre** (itér. 2, 2026-06-05).
     Y compris celles résolues par ISBN en passe 1 : les ISBN sont saisis à la
     main et peuvent être erronés, donc on recoupe systématiquement.
     `ISBN_FOUND_BY_TA` permet de comparer à l'ISBN du fichier ; si les deux
     diffèrent (avec un score ≥ 75), la cellule `ISBN_FOUND_BY_TA` est colorée
     en orange (probable faute de saisie).
   - Pour chaque source, appel `search(title, author)` → liste de candidats
     normalisés `{title, authors_text, isbn_13|isbn_10, …}`.
   - **Fusion** : on agrège les candidats des 4 sources dans une liste
     unique, on calcule un score `rapidfuzz.fuzz.WRatio` sur
     `f"{title} | {author}"` vs `f"{cand.title} | {cand.authors_text}"`
     (les deux passés en `lowercase` + `strip_accents`).
   - Le **meilleur candidat** (score max) renseigne :
     - `ISBN_FOUND_BY_TA`
     - `TITLE_FOUND_BY_TA`
     - `AUTHOR_FOUND_BY_TA`
     - `SOURCE_BY_TA`
     - `CONFIDENCE` (0-100, entier)
   - Seuil **plancher** : si meilleur score < 60, on ne renseigne RIEN
     (trop incertain). Le seuil est exposé en constante du module pour
     ajustement futur.

4. **Production du fichier annoté**
   - Copie de l'Excel d'entrée + ajout des colonnes (toujours dans cet
     ordre, en queue de chaque ligne) :
     ```
     TITLE_FOUND_BY_ISBN | AUTHOR_FOUND_BY_ISBN | SOURCE_BY_ISBN
     ISBN_FOUND_BY_TA    | TITLE_FOUND_BY_TA    | AUTHOR_FOUND_BY_TA | SOURCE_BY_TA | CONFIDENCE
     ```
   - Mise en forme : ligne d'en-têtes en gras ; cellules `CONFIDENCE < 75`
     en fond orange (signal visuel pour relecture humaine).
   - Stocké dans `media/excel_jobs/<job_id>/result.xlsx`, dispo en
     téléchargement depuis la page de détail du job.

5. **Pas d'effet de bord sur la base BibliOfelia** — VERIFY n'écrit
   **rien** dans `BibliographicRecord` / `Item` / `ScanSession`.

### Fonctionnalité 2 — Import (mode IMPORT)

**Entrée** : fichier `.xlsx` avec **au moins 1 colonne nommée** : `ISBN`.
Colonnes optionnelles reconnues : `LOCATION` (code emplacement), `CATEGORY`
(nom catégorie). Toute autre colonne est **ignorée silencieusement**.

**Pipeline** :

1. **Validation** (idem VERIFY : `.xlsx`, 5 Mo, 10 000 lignes, colonne `ISBN`
   présente).

2. **Création de la `ScanSession`**
   - `label = f"Import Excel — {datetime.now():%Y-%m-%d %H:%M}"`
   - `created_by = request.user`
   - `state = OPEN`
   - `default_location` / `default_category` : restent `None`. La résolution
     se fait **par ligne** (colonnes LOCATION/CATEGORY du fichier).

3. **Création des `ScanItem`** — un par ligne valide :
   - `scan_kind = ISBN`
   - `scanned_value = <ISBN normalisé>`
   - `local_id = f"excel-{job_id}-{row_number}"` (idempotent : si on
     ré-importe le même fichier après échec, les `ScanItem` existants sont
     ignorés grâce à la contrainte unique `(session, local_id)`).
   - `metadata_title = ""` (vide → placeholder `ISBN:<n> - <date>` posé par
     `_create_record`, écrasé ensuite par FEAT-031 si lancé).
   - `location_code = ligne.LOCATION` (résolu par `_resolve_location` —
     si code inconnu : item créé sans location, warning dans le report).
   - `category` : résolu par `apps.catalog.models.Category.objects.filter(name__iexact=…)`
     — si nom inconnu : item créé sans catégorie, warning.
   - `copy_count = 1` (pas de gestion d'exemplaires multiples par ligne en
     v1).
   - `scanned_at = timezone.now()`

4. **Finalisation**
   - Appel `finalize_scan_session(session)` — réutilise tel quel le pipeline
     FEAT-021 (matching ISBN existant → réutilise la notice, sinon
     création).
   - `processing_summary` contient déjà `items_processed / records_created /
     records_matched / copies_added`.

5. **Suivi UI**
   - La session apparaît dans la liste **Catalogage par scan**
     (`/catalog/scan-sessions/`) — pas de page dédiée à inventer.
   - Le job `ExcelCatalogJob` mode IMPORT garde un FK vers la `ScanSession`
     créée + un compteur d'erreurs de lecture Excel (lignes rejetées avant
     finalisation).

6. **Enrichissement métadonnées** — **pas automatique en v1**. Le
   bibliothécaire peut ensuite lancer un job FEAT-031 sur la session (lien
   « Enrichir cette session » à ajouter dans une itération suivante si
   besoin). Décision : on évite d'enchaîner les jobs implicitement.

## Spécification technique

### Modèle `ExcelCatalogJob` — nouveau

Dans `apps/catalog/models.py` (cohérent avec `EnrichmentJob` qui y vit
déjà).

```python
class ExcelJobMode(TextChoices):
    VERIFY = "verify", _("Vérification")
    IMPORT = "import", _("Import")

class ExcelJobState(TextChoices):
    PENDING  = "pending",  _("En attente")
    RUNNING  = "running",  _("En cours")
    FINISHED = "finished", _("Terminé")
    FAILED   = "failed",   _("Échec")

class ExcelCatalogJob(models.Model):
    mode             = CharField(choices=ExcelJobMode.choices)
    state            = CharField(choices=ExcelJobState.choices, default=PENDING)
    uploaded_file    = FileField(upload_to="excel_jobs/%Y/%m/")
    result_file      = FileField(upload_to="excel_jobs/%Y/%m/", null=True, blank=True)
    scan_session     = FK(ScanSession, null=True, blank=True, on_delete=SET_NULL)  # IMPORT only
    total            = PositiveIntegerField(default=0)
    processed        = PositiveIntegerField(default=0)
    matched_by_isbn  = PositiveIntegerField(default=0)
    matched_by_ta    = PositiveIntegerField(default=0)
    not_found        = PositiveIntegerField(default=0)
    errors           = PositiveIntegerField(default=0)
    report           = JSONField(default=list, blank=True)  # warnings par ligne
    created_at       = DateTimeField(default=timezone.now)
    finished_at      = DateTimeField(null=True, blank=True)
    created_by       = FK(User, on_delete=SET_NULL, null=True)
```

Migration : `apps/catalog/migrations/0009_excel_catalog_job.py`.

### Sources — extension `search(title, author)`

Ajouter dans **chaque** source de `apps/catalog/sources/` :

```python
def search(title: str, author: str, limit: int = 5) -> list[dict]:
    """Retourne jusqu'à `limit` candidats normalisés (même schéma que lookup)."""
```

Détails par source :

- **`google_books.py`** : `q=intitle:"…" inauthor:"…"`, `maxResults=5`. **Clé
  API facultative** (itér. 2, 2026-06-05) : interrogé même sans clé — l'API
  Google Books répond en anonyme (quota par IP, 429 possible en cas de rafale).
  Modifie aussi `lookup(isbn)` (passe 1 + FEAT-031) : meilleure couverture des
  ISBN hors fonds FR/EN (ex. `978-607…` Mexique). Tolérance native.
- **`openlibrary.py`** : `https://openlibrary.org/search.json?title=…&author=…&limit=5`.
  Tolérance native. Pas de clé.
- **`bnf.py`** : SRU `bib.title adj "…" and bib.author adj "…"`,
  `maximumRecords=5`. Pas de tolérance — la passe fuzzy locale s'en
  charge.
- **`bne.py`** : SRU équivalent (à vérifier — sinon basculer sur l'API
  `datos.bne.es/opensearch`).

Pas de cache LRU en v1 (l'utilisateur lance le job 1 fois ; les jobs FEAT-031
seront le gros consommateur).

### Module `apps/catalog/sources/_fuzzy.py` — nouveau

```python
from rapidfuzz import fuzz, utils

def score(query_title: str, query_author: str,
          cand_title: str, cand_authors: str) -> int:
    q = utils.default_process(f"{query_title} | {query_author}")
    c = utils.default_process(f"{cand_title} | {cand_authors}")
    return int(fuzz.WRatio(q, c))

CONFIDENCE_FLOOR = 60   # passe 2 : on n'écrit rien si score < 60
HIGHLIGHT_BELOW  = 75   # cellules CONFIDENCE colorées dans l'Excel
```

### Service `apps/catalog/excel_catalog.py` — nouveau

Le fichier porte toute la logique :

- `validate_xlsx(file) -> tuple[Workbook, list[str]]` — colonnes,
  taille, lignes max.
- `run_verify_job(job_id)` — passes 1+2, écrit `result_file`.
- `run_import_job(job_id)` — crée ScanSession + ScanItem, appelle
  `finalize_scan_session`.
- Point d'entrée django-q2 : `run_excel_catalog_job(job_id)` qui dispatch
  selon `job.mode`.

### Vues `apps/catalog/views.py` — ajouts

- `excel_catalog_index` : page de garde avec 2 onglets (VERIFY / IMPORT) +
  liste des 10 derniers jobs de l'utilisateur.
- `excel_catalog_verify_create` (POST) : upload + `ExcelCatalogJob.objects.create(mode=VERIFY, …)` +
  `async_task("apps.catalog.excel_catalog.run_excel_catalog_job", job.pk)`.
- `excel_catalog_import_create` (POST) : idem mode IMPORT.
- `excel_catalog_detail(job_id)` : suivi temps réel (polling HTMX 2 s).
- `excel_catalog_download(job_id)` : sert le `result_file`
  (`FileResponse`, `as_attachment=True`).

Toutes en `@librarian_required`.

### Templates

- `templates/catalog/excel_catalog/index.html` — onglets + liste des jobs
  récents.
- `templates/catalog/excel_catalog/_verify_form.html` — upload + bouton
  « Lancer la vérification ».
- `templates/catalog/excel_catalog/_import_form.html` — upload + petit
  guide colonnes optionnelles + bouton « Importer ».
- `templates/catalog/excel_catalog/detail.html` — barre de progression,
  compteurs, bouton téléchargement (VERIFY) ou lien vers la ScanSession
  (IMPORT).

### Menu `Avancé → Inventaire`

Ajout dans `templates/core/advanced.html` (section déjà gardée par
`is_librarian`), entre **Catalogage par scan** et **Emplacements** :

```html
<a href="{% url 'catalog:excel_catalog_index' %}" class="list-row">
    <div class="lrow-icon" style="--lr-bg:var(--olive-light);--lr-fg:#6B5A0E">
        {% icon "file-spreadsheet" size="18px" %}
    </div>
    <div class="lrow-body">
        <div class="lrow-title">{% trans "Catalogage Excel" %}</div>
        <div class="lrow-sub">{% trans "Vérifier ou importer un fichier Excel d'inventaire (ISBN, titre, auteur, emplacement, catégorie)." %}</div>
    </div>
    <div class="lrow-end">{% icon "chevron-right" size="18px" %}</div>
</a>
```

Icône Lucide `file-spreadsheet` à télécharger dans `static/icons/`.

### URLs `apps/catalog/urls.py` — ajouts

```python
path("excel-catalog/",                 views.excel_catalog_index,         name="excel_catalog_index"),
path("excel-catalog/verify/",          views.excel_catalog_verify_create, name="excel_catalog_verify"),
path("excel-catalog/import/",          views.excel_catalog_import_create, name="excel_catalog_import"),
path("excel-catalog/<int:pk>/",        views.excel_catalog_detail,        name="excel_catalog_detail"),
path("excel-catalog/<int:pk>/download/", views.excel_catalog_download,    name="excel_catalog_download"),
```

### Dépendances Python

À ajouter dans `requirements.txt` :

```
openpyxl>=3.1
rapidfuzz>=3.6
```

`openpyxl` est déjà transitivement présent via `django-import-export` ?
À vérifier — sinon ajouter explicitement. `rapidfuzz` est nouveau (pure
Python wheel, pas de compilation).

## Tests

`apps/catalog/tests/test_excel_catalog.py` :

- `test_validate_xlsx_rejects_xls`
- `test_validate_xlsx_rejects_oversized`
- `test_validate_xlsx_requires_columns_verify` (manque TITLE → erreur)
- `test_validate_xlsx_requires_columns_import` (manque ISBN → erreur)
- `test_verify_job_pass1_only` (ISBN reconnu — mocke `_try_sources`)
- `test_verify_job_pass2_fuzzy_match` (titre tapé avec faute → score > 60)
- `test_verify_job_pass2_low_score_skipped` (score < 60 → colonnes vides)
- `test_import_job_creates_scan_session_and_items`
- `test_import_job_resolves_location_and_category`
- `test_import_job_skips_invalid_isbn`
- `test_import_job_idempotent_on_local_id` (relance même fichier → dédup)

Cible coverage : ≥ 75 % sur `excel_catalog.py` et `_fuzzy.py`.

## i18n

Toutes les chaînes UI traduites EN/ES/MG via
`scripts/translations_sprint20.py` (à créer). Gate
`scripts/i18n_check.py → 0` avant commit (règle CLAUDE.md).

## Impact sur SPEC_BIBLIOFELIA.md

- §6.x nouveau : **Catalogage Excel**, sous §6 (Cas d'usage).
- §5.2 : modèle `ExcelCatalogJob` ajouté.
- §7 : nouvelle dépendance `openpyxl` + `rapidfuzz`.
- En-tête : version + ligne FEAT-050.

## Risques / points d'attention

1. **Performances passe 2** — 4 sources × `search` × N lignes. Pour 1000
   lignes → ~4000 requêtes HTTP. Mitigation : ThreadPoolExecutor par ligne
   (`max_workers=4`), timeout 10 s par source (déjà standard), abandon
   silencieux si une source rate. Pour 10 000 lignes → ~1h. Acceptable
   pour un job async. Documenter dans l'UI : « Compter ~10 min pour 1000
   lignes ».
2. **BNF/BNE qualité matching** — la requête SRU `adj` est tolérante mais
   bruyante. Si on récupère 5 candidats par requête, on fait confiance au
   score fuzzy. À surveiller en QA réelle.
3. **Encodages Excel** — openpyxl gère UTF-8 nativement, mais certains
   fichiers exportés depuis vieilles versions d'Excel ont des cellules
   `None` mélangées à des `str`. Normalisation systématique
   `(cell.value or "").strip()`.
4. **Idempotence VERIFY** — pas critique (pas d'effet de bord BD).
5. **Idempotence IMPORT** — assurée par `local_id` unique
   `excel-<job_id>-<row>`. Si le job échoue à mi-parcours, on peut le
   ré-exécuter manuellement (admin Django) sur la même session sans
   doublons.
6. **Sécurité upload** — `FileField` limite déjà côté Django ; on rejette
   tout sauf `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
   ET extension `.xlsx`. Pas de macro Excel exécutée (openpyxl ne les lit
   pas).

## Décomposition en tâches (TASKS.md)

Voir bloc **Sprint 20 — FEAT-050** dans `docs/tasks/TASKS.md`.

## Statut

- [x] Spec validée par Val (2026-06-05) — décisions multi-hits / ScanSession virtuelle / 4 sources confirmées via `AskUserQuestion` ; Val a aussi confirmé que la passe 1 (ISBN → titre/auteur) faisait bien partie du périmètre
- [x] Code (2026-06-05)
- [x] Tests verts — 16 cas dans `apps/catalog/tests/test_excel_catalog.py` (suite complète 362 passed, +13 ; couverture `excel_catalog.py` 78 %, `_fuzzy.py` 90 %)
- [x] i18n gate OK — `scripts/translations_sprint20.py` (35 entrées × EN/ES/MG), `i18n_check.py` → 0
- [x] Déploiement Pi (Val a explicitement demandé : code tout + déploie Pi, **pas de commit**, il teste à son retour ou à distance sur la Pi)
- [x] Test fonctionnel UI Val — **OK 2026-06-05** (« ça fonctionne »)
- [x] Commit groupé après confirmation Val

## Écarts d'implémentation vs spec

- **Validation côté vue** : `validate_xlsx(uploaded_file, mode)` renvoie une
  liste d'erreurs (au lieu de `(Workbook, errors)`) ; la vue affiche les
  erreurs en `messages.error` sans créer de job. Le runner ré-ouvre
  `job.uploaded_file.path`.
- **Vues** : nommées `@require_role(LIBRARIAN, SUPERADMIN)` (convention du
  repo) plutôt qu'un décorateur `librarian_required` inexistant. Détail/download
  filtrés sur `created_by=request.user` (un bibliothécaire ne voit que ses
  propres travaux ; superadmin via l'admin Django).
- **IMPORT idempotent** : `run_import_job` réutilise `job.scan_session` s'il
  existe déjà (re-exécution admin après échec) → `update_or_create` sur
  `(session, local_id)` garantit l'absence de doublons.
- **Passe 2 source** : la colonne `SOURCE_BY_TA` est laissée vide (le candidat
  fusionné ne trace pas sa source d'origine après agrégation) ; le score de
  confiance suffit au tri humain. `CONFIDENCE` reste renseignée.
- **rapidfuzz** épinglé `3.10.1`, **openpyxl** `3.1.5` (versions exactes).

## Itération 2 (retours Val 2026-06-05)

1. **Passe 2 sur toutes les lignes** (et plus seulement celles sans ISBN) — les
   ISBN sont saisis à la main et parfois erronés ; on recoupe systématiquement
   par titre+auteur. `ISBN_FOUND_BY_TA` ≠ ISBN du fichier (score ≥ 75) → cellule
   colorée en orange (repère de faute de saisie).
2. **Google Books interrogé sans clé API** (`lookup` + `search`) — avant, la
   source renvoyait `[]`/`None` faute de clé, ce qui ratait des ISBN hors fonds
   FR/EN (ex. `9786074440966`, Disney Mexique). L'API répond en anonyme mais
   avec un **quota par IP** : 429 fréquents en rafale / depuis une IP très
   sollicitée. **Pour une couverture fiable : renseigner une clé API Google
   Books** (gratuite, Google Cloud).
3. **Configuration de la clé via `/admin/`** (décision Val) — pas de réouverture
   de la page Paramètres (cf. FEAT-047). `Setting` est désormais enregistré dans
   l'admin Django (`apps/core/admin.py`, surface superadmin). Créer/éditer le
   paramètre `key = metadata.google_books_api_key`, `value = "AIzaSy…"` (chaîne
   JSON, **avec les guillemets**). Consommé par `apps/catalog/sources/google_books.py`.
