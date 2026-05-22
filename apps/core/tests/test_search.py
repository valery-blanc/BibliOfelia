"""Tests recherche globale : classification + FTS5. SPEC §6.1 (Task #5)."""
from __future__ import annotations

import pytest

from apps.catalog.models import BibliographicRecord
from apps.core.search import classify_query, fts_match_expression, fts_search, normalize_code


class TestClassifyQuery:
    def test_item_ean13_prefix_290(self):
        assert classify_query("2900000000123")[0] == "item"

    def test_member_ean13_prefix_291(self):
        assert classify_query("2910000000456")[0] == "member"

    def test_other_ean13_treated_as_isbn(self):
        kind, value = classify_query("9782070612758")
        assert kind == "isbn"
        assert value == "9782070612758"

    def test_isbn10_with_separators(self):
        kind, value = classify_query("2-07-061275-8")
        assert kind == "isbn"
        assert value == "2070612758"

    def test_isbn10_ending_with_x(self):
        assert classify_query("123456789X")[0] == "isbn"

    def test_free_text(self):
        kind, value = classify_query("harry potter")
        assert kind == "text"
        assert value == "harry potter"

    def test_normalize_strips_separators(self):
        assert normalize_code(" 290-0000-0001-23 ") == "2900000000123"


def test_fts_match_expression_prefixes_each_term():
    assert fts_match_expression("petit prince") == '"petit"* "prince"*'


@pytest.mark.django_db
class TestFtsSearch:
    def test_finds_record_by_title(self):
        rec = BibliographicRecord.objects.create(title="Le Petit Prince")
        assert rec.pk in fts_search("petit")

    def test_diacritics_insensitive(self):
        rec = BibliographicRecord.objects.create(title="L'Étranger")
        assert rec.pk in fts_search("etranger")

    def test_no_match_returns_empty(self):
        BibliographicRecord.objects.create(title="Moby Dick")
        assert fts_search("zzzznotfound") == []

    def test_empty_query_returns_empty(self):
        assert fts_search("   ") == []
