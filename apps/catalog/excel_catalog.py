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
    ExcelCatalogJob,
    ExcelJobMode,
    ExcelJobState,
    ScanItem,
    ScanKind,
    ScanSession,
    ScanSessionState,
)
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


def _norm(value: str) -> str:
    """Normalise un nom de colonne : minuscules, sans accents, sans espaces."""
    s = unicodedata.normalize("NFKD", str(value or ""))
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.strip().lower()


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


def _search_all(title: str, author: str) -> list[dict]:
    """Interroge les 4 sources `search` en parallèle, agrège les candidats."""
    candidates: list[dict] = []

    def _one(name):
        try:
            return SEARCHES[name](title, author, limit=5) or []
        except Exception as exc:  # filet : une source qui casse ne bloque pas
            logger.info("Source %s search KO « %s » : %s", name, title, exc)
            return []

    with ThreadPoolExecutor(max_workers=len(SEARCHES)) as ex:
        for result in ex.map(_one, _SOURCE_ORDER):
            candidates.extend(result)
    return candidates


def _pass1_by_isbn(isbn: str) -> dict | None:
    """Passe 1 : interroge les sources par ISBN, renvoie la 1re réponse non
    vide (titre présent) avec sa source, ou None."""
    responses = _try_sources(isbn, _SOURCE_ORDER)
    for name in _SOURCE_ORDER:
        data = responses.get(name)
        if data and (data.get("title") or "").strip():
            return {
                "title": (data.get("title") or "").strip(),
                "authors_text": (data.get("authors_text") or "").strip(),
                "source": name,
            }
    return None


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
        if raw_isbn:
            isbn = typed_isbn
            if len(isbn) not in (10, 13):
                ws.cell(row=row, column=out["SOURCE_BY_ISBN"], value="ISBN_INVALID")
            else:
                hit = _pass1_by_isbn(isbn)
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
            candidates = _search_all(title, author)
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

        job.processed += 1
        if job.processed % 10 == 0:
            job.save(update_fields=["processed", "matched_by_isbn", "matched_by_ta", "not_found"])

    buffer = io.BytesIO()
    wb.save(buffer)
    wb.close()
    job.result_file.save(f"verify-{job.pk}.xlsx", ContentFile(buffer.getvalue()), save=False)


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
    total = 0
    for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        raw_isbn = _cell_str(row[col_isbn - 1]) if col_isbn and col_isbn <= len(row) else ""
        loc_code = _cell_str(row[col_loc - 1]) if col_loc and col_loc <= len(row) else ""
        cat_name = _cell_str(row[col_cat - 1]) if col_cat and col_cat <= len(row) else ""
        if not raw_isbn:
            continue
        total += 1
        isbn = normalize_isbn(raw_isbn)
        if len(isbn) not in (10, 13):
            job.errors += 1
            job.report.append({"row": row_idx, "isbn": raw_isbn, "warning": "ISBN_INVALID"})
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

        ScanItem.objects.update_or_create(
            session=session,
            local_id=f"excel-{job.pk}-{row_idx}",
            defaults={
                "scan_kind": ScanKind.ISBN if len(isbn) == 10 else ScanKind.EAN13,
                "scanned_value": isbn,
                "metadata_title": "",
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
