"""Service d'enrichissement métadonnées multi-sources (FEAT-031).

Lancé via une tâche django-q2 (``run_enrichment_job``) à partir du formulaire
de l'UI admin. Itère sur les notices du périmètre, interroge les sources
actives en parallèle (ThreadPoolExecutor), et fusionne les réponses
field-by-field dans l'ordre de préférence : pour chaque champ, on prend la
première source non vide dans l'ordre choisi par l'utilisateur.

Ce comportement permet, par exemple, qu'un résumé absent côté OpenLibrary
soit complété par Google Books si celui-ci a répondu en parallèle.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import httpx
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils import timezone

from .models import (
    Author,
    BibliographicRecord,
    EnrichmentJob,
    EnrichmentJobState,
    EnrichmentMode,
    MetadataQuality,
    MetadataSource,
    Tag,
)
from .sources import SOURCES

logger = logging.getLogger(__name__)

# Champs texte synchronisables. `authors_text`, `subjects` (→ tags) et
# `cover_url` (→ FileField) sont traités à part dans `merge_record`.
SOURCE_FIELDS = ("title", "subtitle", "publisher", "publication_year", "language", "summary")

# Garde-fous tags : on cap à 10 tags max par notice, longueur 40 max chaque
# (OpenLibrary renvoie parfois 50+ subjects, certains très longs/inutiles).
_MAX_TAGS_PER_RECORD = 10
_MAX_TAG_LENGTH = 40
# Garde-fous cover : 2 MB max, timeout 10 s (cf. ProtoTypes des couvertures GB).
_COVER_MAX_BYTES = 2 * 1024 * 1024
_COVER_TIMEOUT_SECONDS = 10

_SOURCE_TO_METADATA = {
    "openlibrary": MetadataSource.OPENLIBRARY,
    "google_books": MetadataSource.IMPORT,
    "bnf": MetadataSource.IMPORT,
    "bne": MetadataSource.IMPORT,
}

# Préfixes écrits par `apps.api.services._create_record` quand OfeliaScan
# envoie un ISBN sans titre. Tous language-neutral. On garde l'ancien
# (« Sans titre — session …») pour pouvoir enrichir les notices créées
# avant le hotfix 2026-05-24.
_PLACEHOLDER_TITLE_PREFIXES = (
    "ISBN:",                    # courant : "ISBN:<isbn> - <dd.mm.aaaa hh.mn>"
    "Sans titre — session ",   # legacy avant 2026-05-24
)


def _is_empty(val, field: str | None = None) -> bool:
    """True si ``val`` doit être considéré comme « à compléter » par FEAT-031.

    Les chaînes vides, None et listes vides comptent comme vides. Pour le
    field ``title``, le placeholder posé par OfeliaScan en l'absence de
    métadonnées est aussi traité comme vide — sinon les notices fantômes
    resteraient avec leur placeholder en mode FILL_MISSING.
    """
    if val is None:
        return True
    if isinstance(val, str):
        v = val.strip()
        if not v:
            return True
        if field == "title" and v.startswith(_PLACEHOLDER_TITLE_PREFIXES):
            return True
        return False
    if isinstance(val, (list, tuple)):
        return len(val) == 0
    return False


def _record_is_complete(record: BibliographicRecord) -> bool:
    """True si la notice a déjà un vrai titre (≠ placeholder) ET au moins un
    auteur. En mode FILL_MISSING, on saute alors l'interrogation des sources :
    économise le quota et accélère les re-runs (BUG-019). Compromis assumé : on
    ne re-complète pas couverture/résumé/éditeur d'une notice déjà titrée+auteurée.
    """
    title = (record.title or "").strip()
    if not title or title.startswith(_PLACEHOLDER_TITLE_PREFIXES):
        return False
    return record.authors.exists()


def _pick(
    responses: dict, source_order: list[str], field: str
) -> tuple[object, str | None]:
    """Pour ``field``, parcourt ``source_order`` et renvoie la 1re valeur
    non vide, avec le nom de la source qui l'a fournie."""
    for name in source_order:
        data = responses.get(name)
        if not data:
            continue
        val = data.get(field)
        if not _is_empty(val):
            return val, name
    return None, None


def _download_cover(record: BibliographicRecord, url: str) -> bool:
    """Télécharge l'image et la stocke dans ``record.cover_image``.
    Retourne True si succès."""
    try:
        with httpx.Client(timeout=_COVER_TIMEOUT_SECONDS, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            content = resp.content
            if len(content) > _COVER_MAX_BYTES:
                logger.info("Cover %s rejetée : %d octets > limite", url, len(content))
                return False
            if not content:
                return False
    except (httpx.HTTPError, OSError) as exc:
        logger.info("Cover %s KO : %s", url, exc)
        return False
    isbn = record.isbn_13 or record.isbn_10 or f"rec{record.pk}"
    filename = f"{isbn}.jpg"
    record.cover_image.save(filename, ContentFile(content), save=False)
    return True


def _apply_subjects_as_tags(
    record: BibliographicRecord, subjects: list, mode: str
) -> list[str]:
    """Crée/récupère des Tag pour ``subjects`` et les attache à ``record``.

    En FILL_MISSING : n'ajoute que si la notice n'a aucun tag.
    En OVERWRITE : remplace les tags existants.
    Cap à _MAX_TAGS_PER_RECORD, longueur _MAX_TAG_LENGTH.
    """
    has_tags = record.tags.exists()
    if mode == EnrichmentMode.FILL_MISSING and has_tags:
        return []
    seen: set[str] = set()
    cleaned: list[str] = []
    for raw in subjects:
        name = (str(raw) or "").strip()
        if not name or len(name) > _MAX_TAG_LENGTH:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)
        if len(cleaned) >= _MAX_TAGS_PER_RECORD:
            break
    if not cleaned:
        return []
    if mode == EnrichmentMode.OVERWRITE and has_tags:
        record.tags.clear()
    for name in cleaned:
        tag, _ = Tag.objects.get_or_create(name=name)
        record.tags.add(tag)
    return cleaned


def merge_record(
    record: BibliographicRecord,
    responses: dict,
    source_order: list[str],
    mode: str,
) -> dict:
    """Fusionne ``responses`` (dict {source_name: data | None}) dans ``record``.

    Pour chaque champ, on prend la 1re valeur non vide dans ``source_order``.
    Retourne le dict des champs modifiés avec leur source.
    """
    changes: dict = {}
    contributing_sources: set[str] = set()

    # 1) Champs texte/scalaires
    for field in SOURCE_FIELDS:
        new, source = _pick(responses, source_order, field)
        if _is_empty(new):
            continue
        current = getattr(record, field)
        if mode == EnrichmentMode.FILL_MISSING and not _is_empty(current, field):
            continue
        if isinstance(new, str):
            new = new.strip()
        if new != current:
            setattr(record, field, new)
            changes[field] = source
            if source:
                contributing_sources.add(source)

    # 2) Auteurs
    authors_text, source = _pick(responses, source_order, "authors_text")
    if authors_text:
        has_authors = record.authors.exists()
        if mode == EnrichmentMode.OVERWRITE or not has_authors:
            names = [n.strip() for n in str(authors_text).split(";") if n.strip()]
            if names:
                if mode == EnrichmentMode.OVERWRITE and has_authors:
                    record.authors.clear()
                for name in names:
                    author, _ = Author.objects.get_or_create(full_name=name)
                    record.authors.add(author)
                changes["authors"] = source
                if source:
                    contributing_sources.add(source)

    # 3) Subjects → tags
    subjects, source = _pick(responses, source_order, "subjects")
    if subjects:
        applied = _apply_subjects_as_tags(record, list(subjects), mode)
        if applied:
            changes["tags"] = source
            if source:
                contributing_sources.add(source)

    # 4) Cover image
    cover_url, source = _pick(responses, source_order, "cover_url")
    if cover_url:
        has_cover = bool(record.cover_image)
        if mode == EnrichmentMode.OVERWRITE or not has_cover:
            if _download_cover(record, str(cover_url)):
                changes["cover"] = source
                if source:
                    contributing_sources.add(source)

    if changes:
        # On garde la 1re source contributrice dans l'ordre préféré pour
        # le badge metadata_source de la notice.
        primary = next((s for s in source_order if s in contributing_sources), None)
        record.metadata_source = _SOURCE_TO_METADATA.get(primary, MetadataSource.IMPORT)
        record.metadata_quality = MetadataQuality.AUTO
        record.save()
    return changes


# Sentinel renvoyé par `_safe_call` quand une source a répondu 429 (quota
# atteint) : distingue « réessayer plus tard » de « rien trouvé » (None).
_RATE_LIMITED = object()


def _safe_call(name: str, fn, isbn: str):
    from .sources import SourceRateLimited

    try:
        return name, fn(isbn)
    except SourceRateLimited:
        logger.info("Source %s : quota atteint (429) pour ISBN %s", name, isbn)
        return name, _RATE_LIMITED
    except Exception as exc:
        logger.warning("Source %s a levé %s pour ISBN %s", name, exc, isbn)
        return name, None


def _try_sources(
    isbn: str, source_names: Iterable[str], *, with_rate_limit: bool = False
):
    """Interroge toutes les sources en parallèle. Renvoie un dict
    {source_name: data | None} préservant l'ordre de ``source_names``.

    Si ``with_rate_limit`` est vrai, renvoie ``(dict, rate_limited: bool)`` où
    ``rate_limited`` indique qu'au moins une source a été bloquée par un 429
    (quota). Le sentinel interne n'échappe jamais : les sources rate-limitées
    apparaissent comme ``None`` dans le dict (compat. appelants existants).
    """
    names = [n for n in source_names if n in SOURCES]
    if not names:
        return ({}, False) if with_rate_limit else {}
    results: dict[str, dict | None] = {}
    rate_limited = False
    with ThreadPoolExecutor(max_workers=len(names)) as executor:
        futures = [executor.submit(_safe_call, n, SOURCES[n], isbn) for n in names]
        for future in futures:
            name, data = future.result()
            if data is _RATE_LIMITED:
                rate_limited = True
                data = None
            results[name] = data
    # Conserver l'ordre demandé par l'utilisateur
    ordered = {n: results.get(n) for n in names}
    return (ordered, rate_limited) if with_rate_limit else ordered


def build_queryset(scope_filter: dict):
    """Construit le queryset des notices selon le ``scope_filter`` du job."""
    qs = BibliographicRecord.objects.all()
    kind = (scope_filter or {}).get("kind", "all")
    if kind == "no_author":
        qs = qs.filter(authors__isnull=True)
    elif kind == "missing_publisher":
        qs = qs.filter(Q(publisher="") | Q(publisher__isnull=True))
    elif kind == "isbns":
        isbns = scope_filter.get("isbns") or []
        qs = qs.filter(Q(isbn_13__in=isbns) | Q(isbn_10__in=isbns))
    # "all" : pas de filtre supplémentaire
    qs = qs.filter(Q(isbn_13__isnull=False) | Q(isbn_10__isnull=False)).distinct()
    return qs


def run_enrichment_job(job_id: int) -> None:
    """Tâche django-q2 — exécute un EnrichmentJob.

    Idempotente : si le job est déjà RUNNING (worker concurrent déclenché par
    le retry de django-q2) ou FINISHED/FAILED, on s'arrête immédiatement.
    """
    job = EnrichmentJob.objects.get(pk=job_id)
    if job.state != EnrichmentJobState.PENDING:
        logger.info(
            "EnrichmentJob #%s déjà dans l'état %s, abandon (re-entry détectée).",
            job_id, job.state,
        )
        return
    try:
        job.state = EnrichmentJobState.RUNNING
        job.save(update_fields=["state"])

        qs = build_queryset(job.scope_filter)
        job.total = qs.count()
        job.save(update_fields=["total"])

        for record in qs.iterator():
            isbn = record.isbn_13 or record.isbn_10
            if not isbn:
                job.skipped += 1
                job.processed += 1
                continue
            # FILL_MISSING : notice déjà complète (titre réel + auteurs) → on ne
            # réinterroge pas les sources (économie quota + vitesse, BUG-019).
            if job.mode == EnrichmentMode.FILL_MISSING and _record_is_complete(record):
                job.skipped += 1
                job.processed += 1
                continue
            try:
                responses, rate_limited = _try_sources(
                    isbn, job.sources, with_rate_limit=True
                )
                if any(responses.values()):
                    source_order = list(responses.keys())
                    changes = merge_record(record, responses, source_order, job.mode)
                    if changes:
                        job.updated += 1
                        job.report.append({
                            "record_id": record.pk,
                            "isbn": isbn,
                            "changes": changes,
                        })
                    else:
                        job.skipped += 1
                elif rate_limited:
                    # Aucune donnée ET au moins une source bloquée par le quota :
                    # la notice pourra être complétée par un re-run ultérieur.
                    job.rate_limited += 1
                    job.report.append({
                        "record_id": record.pk,
                        "isbn": isbn,
                        "rate_limited": True,
                    })
                else:
                    job.skipped += 1
            except Exception as exc:
                job.errors += 1
                job.report.append({
                    "record_id": record.pk,
                    "isbn": isbn,
                    "error": str(exc),
                })
            finally:
                job.processed += 1
                if job.processed % 5 == 0:
                    job.save(update_fields=[
                        "processed", "updated", "skipped", "errors",
                        "rate_limited", "report",
                    ])

        job.state = EnrichmentJobState.FINISHED
        job.finished_at = timezone.now()
        job.save()
    except Exception as exc:
        logger.exception("Enrichment job %s failed", job_id)
        job.state = EnrichmentJobState.FAILED
        job.report.append({"global_error": str(exc)})
        job.finished_at = timezone.now()
        job.save()
