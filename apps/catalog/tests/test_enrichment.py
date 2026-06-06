"""Tests FEAT-031 — Enrichissement métadonnées multi-sources. Sprint 9."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from apps.catalog.enrichment import (
    build_queryset,
    merge_record,
    run_enrichment_job,
)
from apps.catalog.models import (
    Author,
    BibliographicRecord,
    EnrichmentJob,
    EnrichmentJobState,
    EnrichmentMode,
    Tag,
)


def _merge(rec, data, mode, source="openlibrary"):
    """Helper : wrap data dans la nouvelle signature multi-source."""
    return merge_record(rec, {source: data}, [source], mode)

pytestmark = pytest.mark.django_db


def _record(**kw):
    defaults = {
        "title": "Old", "subtitle": "", "publisher": "",
        "publication_year": None, "language": "", "summary": "",
        "isbn_13": "9782070612758",
    }
    defaults.update(kw)
    return BibliographicRecord.objects.create(**defaults)


# ----------------------- merge_record --------------------------

def test_merge_fill_missing_does_not_overwrite():
    rec = _record(publisher="Local Pub")
    data = {"publisher": "External", "title": "New Title"}
    changes = _merge(rec, data, EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    assert rec.publisher == "Local Pub"  # Pas écrasé
    assert rec.title == "Old"  # Déjà rempli, pas écrasé
    # publication_year vide → mais data n'en a pas non plus → pas de changement
    assert "publisher" not in changes


def test_merge_fill_missing_overwrites_legacy_placeholder_title():
    """Bug remonté Val 2026-05-24 : les notices créées avant le hotfix avaient
    `title = "Sans titre — session <uuid>"`. En mode FILL_MISSING, ce
    placeholder doit être considéré comme vide et écrasé (rétrocompat)."""
    rec = _record(title="Sans titre — session abc-123-def")
    data = {"title": "Le vrai titre", "authors_text": "X"}
    changes = _merge(rec, data, EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    assert rec.title == "Le vrai titre"
    assert "title" in changes


def test_merge_fill_missing_overwrites_new_placeholder_title():
    """Nouveau placeholder language-neutral (hotfix 2026-05-24) :
    `ISBN:<isbn> - <dd.mm.aaaa hh.mn>` doit être écrasé en FILL_MISSING."""
    rec = _record(title="ISBN:9782070612758 - 24.05.2026 14.30")
    data = {"title": "Le vrai titre", "authors_text": "X"}
    changes = _merge(rec, data, EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    assert rec.title == "Le vrai titre"
    assert "title" in changes


def test_merge_fill_missing_fills_empty_fields():
    rec = _record(publisher="")
    data = {"publisher": "External", "publication_year": 2020}
    changes = _merge(rec, data, EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    assert rec.publisher == "External"
    assert rec.publication_year == 2020
    assert set(changes.keys()) == {"publisher", "publication_year"}


def test_merge_overwrite_replaces():
    rec = _record(publisher="Old Pub", title="Old")
    data = {"publisher": "New Pub", "title": "New"}
    changes = _merge(rec, data, EnrichmentMode.OVERWRITE, "google_books")
    rec.refresh_from_db()
    assert rec.publisher == "New Pub"
    assert rec.title == "New"
    assert "publisher" in changes and "title" in changes


def test_merge_skips_empty_source_values():
    rec = _record(publisher="Existing")
    data = {"publisher": "", "title": None}
    changes = _merge(rec, data, EnrichmentMode.OVERWRITE, "bnf")
    rec.refresh_from_db()
    assert rec.publisher == "Existing"
    assert changes == {}


def test_merge_adds_authors_when_missing():
    rec = _record()
    data = {"authors_text": "Jane Doe; John Smith"}
    _merge(rec, data, EnrichmentMode.FILL_MISSING)
    names = list(rec.authors.values_list("full_name", flat=True))
    assert "Jane Doe" in names and "John Smith" in names


def test_merge_does_not_touch_authors_in_fill_missing_when_present():
    rec = _record()
    a = Author.objects.create(full_name="Local Author")
    rec.authors.add(a)
    data = {"authors_text": "External Author"}
    _merge(rec, data, EnrichmentMode.FILL_MISSING)
    names = list(rec.authors.values_list("full_name", flat=True))
    assert names == ["Local Author"]


# ----------------------- build_queryset --------------------------

def test_build_queryset_filters_to_isbn_only():
    with_isbn = _record(isbn_13="9782070612758")
    BibliographicRecord.objects.create(title="No ISBN")
    qs = build_queryset({"kind": "all"})
    assert list(qs) == [with_isbn]


def test_build_queryset_no_author_scope():
    rec_no_author = _record(isbn_13="9782070612758")
    rec_with_author = _record(isbn_13="9782070612759")
    rec_with_author.authors.add(Author.objects.create(full_name="X"))
    qs = build_queryset({"kind": "no_author"})
    assert rec_no_author in qs
    assert rec_with_author not in qs


# ----------------------- run_enrichment_job --------------------------

def test_run_enrichment_job_marks_finished():
    _record()
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"],
        scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )
    with patch("apps.catalog.enrichment.SOURCES", {
        "openlibrary": lambda isbn: {"title": "New Title", "authors_text": "X"}
    }):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    assert job.state == EnrichmentJobState.FINISHED
    assert job.total == 1
    assert job.processed == 1


def test_run_enrichment_job_counts_errors():
    _record()
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"],
        scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )

    def boom(isbn):
        return {"title": "X", "authors_text": "Y"}

    def merge_boom(*args, **kwargs):
        raise RuntimeError("boom")

    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": boom}), \
         patch("apps.catalog.enrichment.merge_record", side_effect=merge_boom):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    assert job.state == EnrichmentJobState.FINISHED
    assert job.errors == 1


def test_run_enrichment_job_skips_no_isbn():
    BibliographicRecord.objects.create(title="No isbn")
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"],
        scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )
    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": lambda i: None}):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    # La notice sans ISBN est exclue par build_queryset → total=0
    assert job.total == 0


def test_run_enrichment_job_no_data_from_sources():
    _record()
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"],
        scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )
    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": lambda i: None}):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    assert job.skipped == 1
    assert job.updated == 0


def test_run_enrichment_job_idempotent_when_already_running():
    """Si django-q2 re-enqueue la tâche pendant qu'elle tourne, le 2e worker
    doit s'arrêter immédiatement (cf. BUG du processed > total observé en Pi
    avec Q_CLUSTER.retry trop court)."""
    _record()
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"],
        scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
        state=EnrichmentJobState.RUNNING,  # simule un worker concurrent en cours
    )
    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": lambda i: {"title": "X"}}):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    # Pas touché : state inchangé, processed reste 0
    assert job.state == EnrichmentJobState.RUNNING
    assert job.processed == 0
    assert job.updated == 0


def test_try_sources_returns_all_responses_preserving_order():
    """_try_sources renvoie maintenant un dict {source: data | None}
    pour permettre la fusion field-by-field dans merge_record."""
    from apps.catalog.enrichment import _try_sources

    sources_mock = {
        "openlibrary": lambda i: {"title": "FROM-OL", "authors_text": "OL Author"},
        "google_books": lambda i: {"title": "FROM-GB", "authors_text": "GB Author"},
    }
    with patch("apps.catalog.enrichment.SOURCES", sources_mock):
        responses = _try_sources("9782070612758", ["openlibrary", "google_books"])
    assert list(responses.keys()) == ["openlibrary", "google_books"]
    assert responses["openlibrary"]["title"] == "FROM-OL"
    assert responses["google_books"]["title"] == "FROM-GB"


def test_try_sources_returns_none_for_failed_source():
    from apps.catalog.enrichment import _try_sources

    sources_mock = {
        "openlibrary": lambda i: None,
        "google_books": lambda i: {"title": "FROM-GB", "authors_text": "X"},
    }
    with patch("apps.catalog.enrichment.SOURCES", sources_mock):
        responses = _try_sources("9782070612758", ["openlibrary", "google_books"])
    assert responses["openlibrary"] is None
    assert responses["google_books"]["title"] == "FROM-GB"


# ----------------------- 429 / quota (BUG-019) --------------------------

def test_try_sources_with_rate_limit_flag():
    """Une source qui lève SourceRateLimited apparaît comme None mais lève le
    drapeau rate_limited (et le sentinel n'échappe jamais)."""
    from apps.catalog.enrichment import _try_sources
    from apps.catalog.sources import SourceRateLimited

    def limited(isbn):
        raise SourceRateLimited("google_books")

    sources_mock = {"openlibrary": lambda i: None, "google_books": limited}
    with patch("apps.catalog.enrichment.SOURCES", sources_mock):
        responses, rate_limited = _try_sources(
            "9782070612758", ["openlibrary", "google_books"], with_rate_limit=True
        )
    assert rate_limited is True
    assert responses["google_books"] is None


def test_run_enrichment_job_counts_rate_limited():
    """Quota 429 sans donnée → compté dans rate_limited, placeholder conservé,
    entrée dédiée dans le rapport (re-run ultérieur possible)."""
    from apps.catalog.sources import SourceRateLimited

    rec = _record(title="ISBN:9782070612758 - 24.05.2026 14.30")
    job = EnrichmentJob.objects.create(
        sources=["google_books"],
        scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )

    def limited(isbn):
        raise SourceRateLimited("google_books")

    with patch("apps.catalog.enrichment.SOURCES", {"google_books": limited}):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    rec.refresh_from_db()
    assert job.rate_limited == 1
    assert job.updated == 0
    assert job.skipped == 0
    assert rec.title.startswith("ISBN:")  # placeholder conservé
    assert any(e.get("rate_limited") for e in job.report)


def test_run_enrichment_job_skips_complete_records_in_fill_missing():
    """FILL_MISSING : une notice déjà titrée + auteurée n'interroge pas les
    sources (économie quota / vitesse, BUG-019)."""
    rec = _record(title="Un vrai titre")
    rec.authors.add(Author.objects.create(full_name="Une autrice"))
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"], scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )
    called = {"n": 0}

    def src(isbn):
        called["n"] += 1
        return {"title": "X", "authors_text": "Y"}

    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": src}):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    assert called["n"] == 0  # source jamais appelée
    assert job.skipped == 1
    assert job.updated == 0


def test_run_enrichment_job_overwrite_does_not_skip_complete():
    """OVERWRITE : on réinterroge même une notice déjà complète."""
    rec = _record(title="Un vrai titre")
    rec.authors.add(Author.objects.create(full_name="Une autrice"))
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"], scope_filter={"kind": "all"},
        mode=EnrichmentMode.OVERWRITE,
    )
    called = {"n": 0}

    def src(isbn):
        called["n"] += 1
        return {"title": "Nouveau", "authors_text": "Z"}

    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": src}):
        run_enrichment_job(job.pk)
    assert called["n"] == 1


def test_run_enrichment_job_does_not_skip_placeholder_title():
    """Une notice au placeholder (sans auteur) reste interrogée en FILL_MISSING."""
    _record(title="ISBN:9782070612758 - 24.05.2026 14.30")
    job = EnrichmentJob.objects.create(
        sources=["openlibrary"], scope_filter={"kind": "all"},
        mode=EnrichmentMode.FILL_MISSING,
    )
    called = {"n": 0}

    def src(isbn):
        called["n"] += 1
        return {"title": "Le vrai titre", "authors_text": "A"}

    with patch("apps.catalog.enrichment.SOURCES", {"openlibrary": src}):
        run_enrichment_job(job.pk)
    job.refresh_from_db()
    assert called["n"] == 1
    assert job.updated == 1


def test_google_books_throttle_is_adaptive(monkeypatch):
    """Pas de bridage en régime normal ; bridage après un 429 (mode lent)."""
    from apps.catalog.sources import google_books

    slept: list[float] = []
    monkeypatch.setattr(google_books.time, "sleep", lambda s: slept.append(s))
    monkeypatch.setattr(google_books, "_last_request_at", 0.0)
    monkeypatch.setattr(google_books, "_slowed_until", 0.0)

    # Régime normal : deux requêtes rapprochées → aucun sleep.
    google_books._throttle()
    google_books._throttle()
    assert slept == []

    # Après un 429 → mode lent : la 2e requête immédiate doit attendre.
    google_books._note_rate_limited()
    google_books._throttle()
    google_books._throttle()
    assert any(s > 0 for s in slept)


def test_google_books_backoff_then_raises_rate_limited(monkeypatch):
    """google_books lève SourceRateLimited quand le 429 persiste après réessais."""
    from apps.catalog.sources import SourceRateLimited, google_books

    class _Resp429:
        status_code = 429
        headers: dict = {}

        def raise_for_status(self):  # pragma: no cover (jamais atteint sur 429)
            raise AssertionError

        def json(self):  # pragma: no cover
            return {}

    calls = {"n": 0}

    def fake_get(*args, **kwargs):
        calls["n"] += 1
        return _Resp429()

    monkeypatch.setattr(google_books, "_MIN_INTERVAL_SLOW", 0)
    monkeypatch.setattr(google_books.time, "sleep", lambda s: None)
    monkeypatch.setattr(google_books.httpx, "get", fake_get)
    with pytest.raises(SourceRateLimited):
        google_books.lookup("9782070612758")
    # 1 essai initial + _MAX_RETRIES_429 réessais
    assert calls["n"] == google_books._MAX_RETRIES_429 + 1


def test_try_sources_handles_exception_in_one_source():
    from apps.catalog.enrichment import _try_sources

    def boom(isbn):
        raise RuntimeError("network down")

    sources_mock = {
        "openlibrary": boom,
        "google_books": lambda i: {"title": "OK", "authors_text": "X"},
    }
    with patch("apps.catalog.enrichment.SOURCES", sources_mock):
        responses = _try_sources("9782070612758", ["openlibrary", "google_books"])
    assert responses["openlibrary"] is None
    assert responses["google_books"]["title"] == "OK"


# ------------- merge_record multi-source (per-field fallback) ----------

def test_merge_per_field_fallback_summary_from_google_if_openlibrary_empty():
    """Bug remonté Val 2026-05-24 : pour summary et subjects, si OpenLibrary
    ne fournit rien, on doit fallback sur Google Books."""
    rec = _record()
    responses = {
        "openlibrary": {"title": "T", "authors_text": "A", "summary": ""},
        "google_books": {"title": "T", "summary": "Le résumé GB"},
    }
    changes = merge_record(rec, responses, ["openlibrary", "google_books"],
                            EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    assert rec.summary == "Le résumé GB"
    assert changes.get("summary") == "google_books"


def test_merge_subjects_become_tags():
    rec = _record()
    responses = {
        "openlibrary": {
            "title": "T", "subjects": ["Fiction", "Aventure", "Jeunesse"],
        },
    }
    merge_record(rec, responses, ["openlibrary"], EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    tag_names = set(rec.tags.values_list("name", flat=True))
    assert tag_names == {"Fiction", "Aventure", "Jeunesse"}


def test_merge_subjects_dedup_and_skip_too_long():
    rec = _record()
    responses = {
        "openlibrary": {
            "title": "T",
            "subjects": ["Fiction", "fiction", "x" * 100, "Roman"],
        },
    }
    merge_record(rec, responses, ["openlibrary"], EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    tag_names = {t.lower() for t in rec.tags.values_list("name", flat=True)}
    # "fiction" dédup, "x"*100 trop long, reste Fiction + Roman
    assert tag_names == {"fiction", "roman"}


def test_merge_subjects_fill_missing_skips_if_tags_exist():
    rec = _record()
    existing = Tag.objects.create(name="ExistingTag")
    rec.tags.add(existing)
    responses = {"openlibrary": {"title": "T", "subjects": ["NewTag"]}}
    merge_record(rec, responses, ["openlibrary"], EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    names = set(rec.tags.values_list("name", flat=True))
    assert names == {"ExistingTag"}


def test_merge_subjects_overwrite_replaces():
    rec = _record()
    existing = Tag.objects.create(name="ExistingTag")
    rec.tags.add(existing)
    responses = {"openlibrary": {"title": "T", "subjects": ["NewTag"]}}
    merge_record(rec, responses, ["openlibrary"], EnrichmentMode.OVERWRITE)
    rec.refresh_from_db()
    names = set(rec.tags.values_list("name", flat=True))
    assert names == {"NewTag"}


def test_merge_per_field_subjects_from_google_if_openlibrary_empty():
    rec = _record()
    responses = {
        "openlibrary": {"title": "T", "subjects": []},
        "google_books": {"title": "T", "subjects": ["GB-Cat"]},
    }
    changes = merge_record(rec, responses, ["openlibrary", "google_books"],
                            EnrichmentMode.FILL_MISSING)
    rec.refresh_from_db()
    assert set(rec.tags.values_list("name", flat=True)) == {"GB-Cat"}
    assert changes.get("tags") == "google_books"
