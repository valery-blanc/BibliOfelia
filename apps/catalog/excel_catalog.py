"""Service de catalogage Excel (FEAT-050).

Deux modes, tous deux exécutés en tâche django-q2 via ``run_excel_catalog_job`` :

- **VERIFY** : annote un fichier Excel avec ce que les sources en ligne
  connaissent du livre — d'abord par ISBN (passe 1), puis par titre + auteur en
  repli (passe 2, réordonnée par score fuzzy local). Produit un fichier
  téléchargeable. Aucun effet de bord sur le catalogue.
- **IMPORT** : matérialise une liste d'ISBN en notices + exemplaires via une
  ``ScanSession`` virtuelle, puis ``finalize_scan_session`` (réutilise le
  pipeline FEAT-021 / FEAT-046).

La validation du fichier (``validate_xlsx``) est faite côté vue, avant la
création du job ; le runner ré-ouvre ensuite ``job.uploaded_file``.
"""
from __future__ import annotations

import io
import logging
import unicodedata
from concurrent.futures import ThreadPoolExecutor

from django.core.files.base import ContentFile
from django.utils import timezone

from .enrichment import _try_sources
from .models import (
    Category,
    DocumentType,
    ExcelCatalogJob,
    ExcelJobMode,
    ExcelJobState,
    ItemState,
    ScanItem,
    ScanKind,
    ScanSession,
    ScanSessionState,
    Tag,
)
from .lookup import is_valid_external_code, normalize_external_code
from .openlibrary import normalize_isbn
from .sources import SEARCHES, SOURCE_LABELS
from .sources._fuzzy import CONFIDENCE_FLOOR, HIGHLIGHT_BELOW, best_candidate

logger = logging.getLogger(__name__)

# Garde-fous d'upload.
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ROWS = 10_000

# Les 4 sources interrogées, dans l'ordre de préférence (1re non vide gagne).
_SOURCE_ORDER = ["openlibrary", "google_books", "bnf", "bne"]

# Colonnes ajoutées en queue par le mode VERIFY (toujours dans cet ordre).
VERIFY_OUTPUT_COLUMNS = [
    "TITLE_FOUND_BY_ISBN",
    "AUTHOR_FOUND_BY_ISBN",
    "SOURCE_BY_ISBN",
    "ISBN_FOUND_BY_TA",
    "TITLE_FOUND_BY_TA",
    "AUTHOR_FOUND_BY_TA",
    "SOURCE_BY_TA",
    "CONFIDENCE",
]


# FEAT-053 : colonnes optionnelles d'affectation de la fiche catalogue en mode
# IMPORT. Une colonne présente avec une cellule non vide écrase le champ de la
# notice (même existante) ; une cellule vide laisse l'existant intact. AUTHOR et
# TAGS remplacent (pas de fusion). Toutes optionnelles.
IMPORT_OVERRIDE_COLUMNS = [
    "title",
    "author",
    "category",
    "type",
    "editor",
    "year",
    "language",
    "tags",
    "condition",  # → état de l'exemplaire (Item.state)
    "external_code",  # FEAT-063 → code Ofelia externe de l'exemplaire
    "provenance",     # FEAT-064 → provenance de l'exemplaire
    "category_abbr",  # FEAT-067 → abréviation (cote) de la catégorie
]

# En-têtes acceptés pour les colonnes dont le nom « naturel » varie d'un
# fichier à l'autre. Clés déjà normalisées par `_norm` (minuscules, sans
# accents). Le nom canonique reste toujours accepté.
_COLUMN_ALIASES = {
    "external_code": [
        "code_externe",
        "code externe",
        "code_ofelia_externe",
        "code ofelia externe",
        "ofelia_ext",
        "externalcode",
    ],
    "provenance": ["origine"],
    "category_abbr": [
        "abbreviation",
        "abreviation",
        "categorie_abregee",
        "categorie abregee",
        "category_abbreviation",
        "cat_abbr",
    ],
}


def _resolve_column(headers: dict[str, int], name: str) -> int | None:
    """Index de la colonne `name`, en acceptant ses alias d'en-tête."""
    idx = headers.get(name)
    if idx:
        return idx
    for alias in _COLUMN_ALIASES.get(name, ()):
        idx = headers.get(alias)
        if idx:
            return idx
    return None

# Garde-fous tags (alignés sur enrichment.py).
_MAX_TAGS_PER_RECORD = 10
_MAX_TAG_LENGTH = 40

# Résolution TYPE (colonne Excel) → DocumentType. Clés normalisées via _norm
# (minuscules, sans accents) : accepte le code interne ou un libellé FR courant.
_DOCUMENT_TYPE_ALIASES = {
    "book": DocumentType.BOOK,
    "livre": DocumentType.BOOK,
    "magazine_issue": DocumentType.MAGAZINE_ISSUE,
    "magazine": DocumentType.MAGAZINE_ISSUE,
    "numero de magazine": DocumentType.MAGAZINE_ISSUE,
    "revue": DocumentType.MAGAZINE_ISSUE,
    "periodique": DocumentType.MAGAZINE_ISSUE,
    "newspaper": DocumentType.NEWSPAPER,
    "journal": DocumentType.NEWSPAPER,
    "comic": DocumentType.COMIC,
    "bd": DocumentType.COMIC,
    "manga": DocumentType.COMIC,
    "bd / manga": DocumentType.COMIC,
    "bd/manga": DocumentType.COMIC,
    "bande dessinee": DocumentType.COMIC,
    "audio_cd": DocumentType.AUDIO_CD,
    "cd": DocumentType.AUDIO_CD,
    "cd audio": DocumentType.AUDIO_CD,
    "audio": DocumentType.AUDIO_CD,
    "other": DocumentType.OTHER,
    "autre": DocumentType.OTHER,
}

# Résolution CONDITION (colonne Excel) → ItemState (état exemplaire).
_ITEM_STATE_ALIASES = {
    "new": ItemState.NEW,
    "neuf": ItemState.NEW,
    "good": ItemState.GOOD,
    "bon": ItemState.GOOD,
    "worn": ItemState.WORN,
    "use": ItemState.WORN,  # « usé » normalisé
    "damaged": ItemState.DAMAGED,
    "abime": ItemState.DAMAGED,  # « abîmé » normalisé
}


def _norm(value: str) -> str:
    """Normalise un nom de colonne : minuscules, sans accents, sans espaces."""
    s = unicodedata.normalize("NFKD", str(value or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


def _resolve_document_type(value: str) -> str | None:
    """FEAT-053 : mappe une valeur TYPE (code ou libellé FR) → DocumentType.
    None si non reconnue."""
    return _DOCUMENT_TYPE_ALIASES.get(_norm(value))


def _resolve_item_state(value: str) -> str | None:
    """FEAT-053 : mappe une valeur CONDITION (code ou libellé FR) → ItemState.
    None si non reconnue."""
    return _ITEM_STATE_ALIASES.get(_norm(value))


def _split_multi(value: str, sep: str) -> list[str]:
    """Découpe une cellule multi-valeurs (auteurs, tags), sans doublon ni vide."""
    seen: list[str] = []
    for part in value.split(sep):
        clean = part.strip()
        if clean and clean not in seen:
            seen.append(clean)
    return seen


def _cell_str(value) -> str:
    """Valeur de cellule en str propre. Gère les ISBN stockés en nombre."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def _header_map(ws) -> dict[str, int]:
    """Mappe nom de colonne normalisé → index de colonne (1-based)."""
    mapping: dict[str, int] = {}
    first_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), ())
    for idx, value in enumerate(first_row, start=1):
        key = _norm(value)
        if key and key not in mapping:
            mapping[key] = idx
    return mapping


def _row_label(row, headers: dict[str, int]) -> str:
    """« Auteur — Titre » d'une ligne, pour identifier une ligne signalée.

    Sert au rapport d'import (BUG-025) : une ligne sans ISBN n'a pas d'autre
    identifiant lisible que son auteur et son titre.
    """
    parts = []
    for name in ("author", "title"):
        col = headers.get(name)
        if col and col <= len(row):
            value = _cell_str(row[col - 1])
            if value:
                parts.append(value)
    return " — ".join(parts)


def required_columns(mode: str) -> list[str]:
    if mode == ExcelJobMode.IMPORT:
        return ["isbn"]
    return ["id", "title", "author", "isbn"]


def validate_xlsx(uploaded_file, mode: str) -> list[str]:
    """Valide un fichier uploadé (vue). Retourne la liste des erreurs (vide = OK).

    Vérifie : extension/type, taille, ouverture openpyxl, nombre de lignes,
    présence des colonnes obligatoires.
    """
    import openpyxl

    errors: list[str] = []
    name = (getattr(uploaded_file, "name", "") or "").lower()
    if not name.endswith(".xlsx"):
        errors.append(
            "Format non supporté : seul le format .xlsx est accepté en v1 "
            "(.xls, .csv et .ods doivent être convertis au préalable)."
        )
        return errors
    size = getattr(uploaded_file, "size", 0) or 0
    if size > MAX_FILE_BYTES:
        errors.append("Fichier trop volumineux (maximum 5 Mo).")
        return errors
    try:
        uploaded_file.seek(0)
        wb = openpyxl.load_workbook(uploaded_file, read_only=True, data_only=True)
    except Exception:
        errors.append("Fichier illisible : ce n'est pas un .xlsx valide.")
        return errors
    try:
        ws = wb.active
        if ws is None:
            errors.append("Le classeur ne contient aucune feuille.")
            return errors
        if (ws.max_row or 0) > MAX_ROWS + 1:
            errors.append(f"Trop de lignes (maximum {MAX_ROWS}).")
        headers = _header_map(ws)
        missing = [c.upper() for c in required_columns(mode) if c not in headers]
        if missing:
            errors.append(
                "Colonnes obligatoires manquantes : " + ", ".join(missing) + "."
            )
    finally:
        wb.close()
    try:
        uploaded_file.seek(0)
    except Exception:  # pragma: no cover (flux non re-seekable)
        pass
    return errors


def _search_all(title: str, author: str) -> tuple[list[dict], bool]:
    """Interroge les 4 sources `search` en parallèle, agrège les candidats.

    Renvoie ``(candidats, rate_limited)`` — ``rate_limited`` vrai si une source
    a atteint son quota (429) pendant la recherche (BUG-019)."""
    from .sources import SourceRateLimited

    candidates: list[dict] = []
    rate_limited = False

    def _one(name):
        try:
            return SEARCHES[name](title, author, limit=5) or [], False
        except SourceRateLimited:
            logger.info("Source %s search : quota atteint (429) « %s »", name, title)
            return [], True
        except Exception as exc:  # filet : une source qui casse ne bloque pas
            logger.info("Source %s search KO « %s » : %s", name, title, exc)
            return [], False

    with ThreadPoolExecutor(max_workers=len(SEARCHES)) as ex:
        for result, was_limited in ex.map(_one, _SOURCE_ORDER):
            candidates.extend(result)
            rate_limited = rate_limited or was_limited
    return candidates, rate_limited


def _pass1_by_isbn(isbn: str) -> tuple[dict | None, bool]:
    """Passe 1 : interroge les sources par ISBN, renvoie ``(hit, rate_limited)``
    où ``hit`` est la 1re réponse non vide (titre présent) avec sa source, ou
    None. ``rate_limited`` vrai si une source a atteint son quota (429)."""
    responses, rate_limited = _try_sources(isbn, _SOURCE_ORDER, with_rate_limit=True)
    for name in _SOURCE_ORDER:
        data = responses.get(name)
        if data and (data.get("title") or "").strip():
            return {
                "title": (data.get("title") or "").strip(),
                "authors_text": (data.get("authors_text") or "").strip(),
                "source": name,
            }, rate_limited
    return None, rate_limited


def run_verify_job(job: ExcelCatalogJob) -> None:
    """Mode VERIFY : annote l'Excel et écrit ``result_file``."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill

    wb = openpyxl.load_workbook(job.uploaded_file.path, data_only=True)
    ws = wb.active
    headers = _header_map(ws)
    col_title = headers.get("title")
    col_author = headers.get("author")
    col_isbn = headers.get("isbn")

    # Colonnes de sortie ajoutées en queue.
    start_col = ws.max_column + 1
    bold = Font(bold=True)
    orange = PatternFill(start_color="FFE5B4", end_color="FFE5B4", fill_type="solid")
    for offset, name in enumerate(VERIFY_OUTPUT_COLUMNS):
        cell = ws.cell(row=1, column=start_col + offset, value=name)
        cell.font = bold
    # En-têtes d'origine en gras aussi.
    for col in range(1, start_col):
        ws.cell(row=1, column=col).font = bold

    out = {n: start_col + i for i, n in enumerate(VERIFY_OUTPUT_COLUMNS)}
    total = ws.max_row - 1 if ws.max_row else 0
    job.total = max(0, total)
    job.save(update_fields=["total"])

    for row in range(2, (ws.max_row or 1) + 1):
        raw_isbn = _cell_str(ws.cell(row=row, column=col_isbn).value) if col_isbn else ""
        title = _cell_str(ws.cell(row=row, column=col_title).value) if col_title else ""
        author = _cell_str(ws.cell(row=row, column=col_author).value) if col_author else ""

        # Ligne vide → on saute sans la compter comme « non trouvée ».
        if not (raw_isbn or title or author):
            continue

        typed_isbn = normalize_isbn(raw_isbn) if raw_isbn else ""
        found_by_isbn = False
        row_rate_limited = False
        if raw_isbn:
            isbn = typed_isbn
            if len(isbn) not in (10, 13):
                ws.cell(row=row, column=out["SOURCE_BY_ISBN"], value="ISBN_INVALID")
            else:
                hit, rl = _pass1_by_isbn(isbn)
                row_rate_limited = row_rate_limited or rl
                if hit:
                    ws.cell(row=row, column=out["TITLE_FOUND_BY_ISBN"], value=hit["title"])
                    ws.cell(row=row, column=out["AUTHOR_FOUND_BY_ISBN"], value=hit["authors_text"])
                    ws.cell(row=row, column=out["SOURCE_BY_ISBN"],
                            value=SOURCE_LABELS.get(hit["source"], hit["source"]))
                    found_by_isbn = True
                    job.matched_by_isbn += 1

        # Passe 2 lancée pour TOUTES les lignes ayant un titre, y compris
        # celles résolues par ISBN : les ISBN sont saisis à la main et peuvent
        # être erronés. La colonne ISBN_FOUND_BY_TA permet alors de comparer
        # l'ISBN trouvé par titre+auteur à celui du fichier (FEAT-050 itér. 2).
        found_by_ta = False
        if title:
            candidates, rl = _search_all(title, author)
            row_rate_limited = row_rate_limited or rl
            best, sc = best_candidate(title, author, candidates)
            if best and sc >= CONFIDENCE_FLOOR:
                isbn_found = best.get("isbn_13") or best.get("isbn_10") or ""
                ta_cell = ws.cell(row=row, column=out["ISBN_FOUND_BY_TA"], value=isbn_found)
                ws.cell(row=row, column=out["TITLE_FOUND_BY_TA"], value=best.get("title", ""))
                ws.cell(row=row, column=out["AUTHOR_FOUND_BY_TA"], value=best.get("authors_text", ""))
                # Source non tracée par candidat → on laisse vide, le score suffit.
                conf_cell = ws.cell(row=row, column=out["CONFIDENCE"], value=sc)
                if sc < HIGHLIGHT_BELOW:
                    conf_cell.fill = orange
                # ISBN saisi ≠ ISBN trouvé par titre+auteur (score fiable) →
                # probable erreur de saisie : on colore la cellule pour la repérer.
                if isbn_found and typed_isbn and isbn_found != typed_isbn and sc >= HIGHLIGHT_BELOW:
                    ta_cell.fill = orange
                found_by_ta = True
                job.matched_by_ta += 1

        if not found_by_isbn and not found_by_ta:
            job.not_found += 1
        if row_rate_limited:
            job.rate_limited += 1
            # Ne pas écraser une source trouvée : ne marquer que si rien par ISBN.
            if not found_by_isbn:
                ws.cell(row=row, column=out["SOURCE_BY_ISBN"], value="RATE_LIMITED")

        job.processed += 1
        if job.processed % 10 == 0:
            job.save(update_fields=[
                "processed", "matched_by_isbn", "matched_by_ta",
                "not_found", "rate_limited",
            ])

    buffer = io.BytesIO()
    wb.save(buffer)
    wb.close()
    job.result_file.save(f"verify-{job.pk}.xlsx", ContentFile(buffer.getvalue()), save=False)


def _parse_row_overrides(
    row,
    override_cols: dict,
    resolved_category,
    external_codes: set[str] | None = None,
    provenances: dict | None = None,
) -> tuple[dict, list[str]]:
    """FEAT-053 : extrait les overrides fiche/exemplaire d'une ligne Excel.

    Ne retient que les colonnes présentes ET non vides (cellule vide → l'info
    existante est conservée). Renvoie ``(overrides, warnings)``. AUTHOR et TAGS
    sont des listes (remplacement, pas fusion). ``resolved_category`` est la
    Category déjà résolue depuis la colonne CATEGORY (None si absente/inconnue).

    ``external_codes`` (FEAT-063) est l'ensemble des codes Ofelia externes déjà
    pris — en base au démarrage du job, puis enrichi ligne après ligne. Un code
    déjà pris n'est pas appliqué : deux exemplaires portant le même code
    rendraient tout scan ambigu.

    ``provenances`` (FEAT-064) indexe les provenances connues par code **et**
    par libellé normalisés, chargées une seule fois pour tout le fichier.
    """
    def _cell(field: str) -> str:
        idx = override_cols.get(field)
        if idx and idx <= len(row):
            return _cell_str(row[idx - 1])
        return ""

    overrides: dict = {}
    warnings: list[str] = []

    title = _cell("title")
    if title:
        overrides["title"] = title[:300]

    # CATEGORY : déjà résolue en amont (partage la colonne avec l'import de base).
    if override_cols.get("category") and resolved_category is not None:
        overrides["category"] = resolved_category

    author = _cell("author")
    if author:
        overrides["authors"] = _split_multi(author, ";")

    editor = _cell("editor")
    if editor:
        overrides["publisher"] = editor[:200]

    language = _cell("language")
    if language:
        overrides["language"] = language[:10]

    year = _cell("year")
    if year:
        try:
            overrides["publication_year"] = int(float(year))
        except (ValueError, TypeError):
            warnings.append("YEAR_INVALID")

    doc_type = _cell("type")
    if doc_type:
        resolved = _resolve_document_type(doc_type)
        if resolved:
            overrides["document_type"] = resolved
        else:
            warnings.append("TYPE_UNKNOWN")

    tags = _cell("tags")
    if tags:
        parsed = [t[:_MAX_TAG_LENGTH] for t in _split_multi(tags, ",")][:_MAX_TAGS_PER_RECORD]
        if parsed:
            overrides["tags"] = parsed

    condition = _cell("condition")
    if condition:
        resolved = _resolve_item_state(condition)
        if resolved:
            overrides["state"] = resolved
        else:
            warnings.append("CONDITION_UNKNOWN")

    # FEAT-067 : la cote appartient à la catégorie, pas à la ligne — on la pose
    # sur la Category résolue par la colonne CATEGORY. Sans catégorie résolue,
    # elle n'a pas de cible : on le signale plutôt que de la perdre en silence.
    abbr = _cell("category_abbr")
    if abbr:
        if resolved_category is None:
            warnings.append("CATEGORY_ABBR_ORPHAN")
        elif resolved_category.abbreviation != abbr[:20]:
            resolved_category.abbreviation = abbr[:20]
            resolved_category.save(update_fields=["abbreviation"])

    provenance_raw = _cell("provenance")
    if provenance_raw:
        provenance = (provenances or {}).get(_norm(provenance_raw))
        if provenance is not None:
            overrides["provenance"] = provenance
        else:
            warnings.append("PROVENANCE_UNKNOWN")

    external_code = normalize_external_code(_cell("external_code"))
    if external_code:
        if not is_valid_external_code(external_code):
            warnings.append("EXTERNAL_CODE_INVALID")
        elif external_codes is not None and external_code in external_codes:
            warnings.append("EXTERNAL_CODE_DUPLICATE")
        else:
            overrides["external_code"] = external_code
            if external_codes is not None:
                external_codes.add(external_code)

    return overrides, warnings


def _apply_import_overrides(job, session, overrides_by_local: dict[str, dict]) -> None:
    """FEAT-053 : applique les overrides aux notices/exemplaires produits.

    Après ``finalize_scan_session``, chaque ScanItem porte dans son
    ``processing_result`` l'``record_id`` et la liste ``copies_created``. On
    écrase les champs de la notice (même préexistante) avec les valeurs Excel ;
    AUTHOR / TAGS sont remplacés. ``state`` s'applique aux exemplaires du lot.
    """
    from django.db import transaction

    from .models import Author, BibliographicRecord, Item

    if not overrides_by_local:
        return

    _RECORD_SCALARS = (
        "title", "publisher", "publication_year", "language", "document_type", "category",
    )
    items = {
        si.local_id: si
        for si in ScanItem.objects.filter(
            session=session, local_id__in=list(overrides_by_local.keys())
        )
    }

    with transaction.atomic():
        for local_id, overrides in overrides_by_local.items():
            scan_item = items.get(local_id)
            if scan_item is None:
                continue
            result = scan_item.processing_result or {}
            record_id = result.get("record_id")
            copy_ids = result.get("copies_created") or []

            if record_id:
                record = BibliographicRecord.objects.filter(pk=record_id).first()
                if record:
                    changed = []
                    for field in _RECORD_SCALARS:
                        if field == "category":
                            if "category" in overrides:
                                record.category = overrides["category"]
                                changed.append("category")
                        elif field in overrides:
                            setattr(record, field, overrides[field])
                            changed.append(field)
                    if changed:
                        record.save(update_fields=changed)
                    if "authors" in overrides:
                        record.authors.clear()
                        for name in overrides["authors"]:
                            author, _ = Author.objects.get_or_create(full_name=name)
                            record.authors.add(author)
                    if "tags" in overrides:
                        record.tags.clear()
                        for name in overrides["tags"]:
                            tag, _ = Tag.objects.get_or_create(name=name)
                            record.tags.add(tag)

            if "state" in overrides and copy_ids:
                Item.objects.filter(pk__in=copy_ids).update(state=overrides["state"])

            if "provenance" in overrides and copy_ids:
                Item.objects.filter(pk__in=copy_ids).update(
                    provenance=overrides["provenance"]
                )

            # FEAT-063 : le code externe désigne UN exemplaire — s'il y a
            # plusieurs copies sur la ligne, il va sur la première.
            if "external_code" in overrides and copy_ids:
                code = overrides["external_code"]
                target = copy_ids[0]
                already_taken = (
                    Item.objects.filter(external_code=code)
                    .exclude(pk=target)
                    .exists()
                )
                if not already_taken:
                    Item.objects.filter(pk=target).update(external_code=code)


def run_import_job(job: ExcelCatalogJob) -> None:
    """Mode IMPORT : crée une ScanSession virtuelle + ses ScanItem, finalise."""
    import openpyxl

    from apps.api.services import finalize_scan_session
    from .models import Location

    wb = openpyxl.load_workbook(job.uploaded_file.path, read_only=True, data_only=True)
    ws = wb.active
    headers = _header_map(ws)
    col_isbn = headers.get("isbn")
    col_loc = headers.get("location")
    col_cat = headers.get("category")
    # FEAT-053 : colonnes optionnelles d'affectation fiche/exemplaire.
    override_cols = {
        name: _resolve_column(headers, name) for name in IMPORT_OVERRIDE_COLUMNS
    }
    # local_id → dict d'overrides (uniquement les colonnes présentes ET non vides).
    overrides_by_local: dict[str, dict] = {}

    # Ré-exécution (admin) après un échec à mi-parcours : on réutilise la
    # session déjà créée → `update_or_create` sur (session, local_id) garantit
    # l'absence de doublons (risque #5 de la spec).
    session = job.scan_session
    if session is None:
        session = ScanSession.objects.create(
            label=f"Import Excel — {timezone.localtime(timezone.now()):%Y-%m-%d %H:%M}",
            created_by=job.created_by,
            state=ScanSessionState.OPEN,
        )
        job.scan_session = session
        job.save(update_fields=["scan_session"])

    known_locations = {loc.code for loc in Location.objects.all()}
    # FEAT-063 : codes externes déjà attribués (en base), enrichis au fil des
    # lignes pour attraper aussi les doublons internes au fichier.
    from .models import Item as _Item

    external_codes = set(
        _Item.objects.exclude(external_code="").values_list("external_code", flat=True)
    )
    # FEAT-064 : provenances indexées par code et par libellé (une seule requête).
    from .models import Provenance

    provenances: dict = {}
    for prov in Provenance.objects.all():
        provenances[_norm(prov.code)] = prov
        if prov.label:
            provenances.setdefault(_norm(prov.label), prov)
    total = 0
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        raw_isbn = _cell_str(row[col_isbn - 1]) if col_isbn and col_isbn <= len(row) else ""
        loc_code = _cell_str(row[col_loc - 1]) if col_loc and col_loc <= len(row) else ""
        cat_name = _cell_str(row[col_cat - 1]) if col_cat and col_cat <= len(row) else ""
        if not raw_isbn:
            # BUG-025 : une ligne **remplie mais sans ISBN** était sautée en
            # silence — absente des compteurs comme du rapport, donc « disparue »
            # (105 lignes dans le fichier → 104 notices, sans une seule erreur).
            # L'import est indexé par ISBN, on ne peut pas la créer ici : on la
            # signale pour qu'elle soit cataloguée à la main. Les lignes
            # entièrement vides (openpyxl en compte souvent après les données)
            # restent ignorées sans bruit.
            if any(_cell_str(cell) for cell in row):
                total += 1
                job.processed += 1
                job.errors += 1
                job.report.append({
                    "row": row_idx,
                    "isbn": "",
                    "warning": "ISBN_MISSING",
                    "label": _row_label(row, headers),
                })
            continue
        total += 1
        isbn = normalize_isbn(raw_isbn)
        if len(isbn) not in (10, 13):
            job.errors += 1
            job.report.append({
                "row": row_idx,
                "isbn": raw_isbn,
                "warning": "ISBN_INVALID",
                "label": _row_label(row, headers),
            })
            job.processed += 1
            continue

        warnings = []
        if loc_code and loc_code not in known_locations:
            warnings.append("LOCATION_UNKNOWN")
            loc_code = ""
        category = None
        if cat_name:
            category = Category.objects.filter(name__iexact=cat_name).first()
            if category is None:
                warnings.append("CATEGORY_UNKNOWN")

        # FEAT-053 : overrides fiche/exemplaire (colonnes présentes + non vides).
        local_id = f"excel-{job.pk}-{row_idx}"
        overrides, ov_warnings = _parse_row_overrides(
            row, override_cols, category, external_codes, provenances
        )
        warnings.extend(ov_warnings)
        if overrides:
            overrides_by_local[local_id] = overrides

        ScanItem.objects.update_or_create(
            session=session,
            local_id=local_id,
            defaults={
                "scan_kind": ScanKind.ISBN if len(isbn) == 10 else ScanKind.EAN13,
                "scanned_value": isbn,
                # FEAT-053 : titre du fichier (sinon placeholder posé par
                # _create_record, remplaçable ensuite par l'enrichissement).
                "metadata_title": overrides.get("title", ""),
                "category": category,
                "location_code": loc_code,
                "copy_count": 1,
                "scanned_at": timezone.now(),
            },
        )
        if warnings:
            job.report.append({"row": row_idx, "isbn": isbn, "warning": ", ".join(warnings)})
        job.processed += 1
    wb.close()

    job.total = total
    job.save(update_fields=["total", "processed", "errors", "report"])

    summary = finalize_scan_session(session)
    # FEAT-053 : après matérialisation, appliquer les overrides aux notices/
    # exemplaires produits (écrase l'existant le cas échéant).
    _apply_import_overrides(job, session, overrides_by_local)
    job.matched_by_isbn = summary.get("records_matched", 0)
    job.not_found = summary.get("records_created", 0)
    job.save(update_fields=["matched_by_isbn", "not_found"])


def run_excel_catalog_job(job_id: int) -> None:
    """Point d'entrée django-q2 : dispatch VERIFY / IMPORT.

    Idempotente : si le job n'est plus PENDING (worker concurrent via le retry
    django-q2), on s'arrête immédiatement.
    """
    job = ExcelCatalogJob.objects.get(pk=job_id)
    if job.state != ExcelJobState.PENDING:
        logger.info("ExcelCatalogJob #%s déjà %s, abandon (re-entry).", job_id, job.state)
        return
    try:
        job.state = ExcelJobState.RUNNING
        job.save(update_fields=["state"])
        if job.mode == ExcelJobMode.VERIFY:
            run_verify_job(job)
        else:
            run_import_job(job)
        job.state = ExcelJobState.FINISHED
        job.finished_at = timezone.now()
        job.save()
    except Exception as exc:
        logger.exception("ExcelCatalogJob %s failed", job_id)
        job.state = ExcelJobState.FAILED
        job.report.append({"global_error": str(exc)})
        job.finished_at = timezone.now()
        job.save()
