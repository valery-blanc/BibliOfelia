"""Tests formulaires catalogue. SPEC §6.1 (Task #6)."""
from __future__ import annotations

import pytest

from apps.catalog.forms import BibliographicRecordForm, ItemBulkCreateForm
from apps.catalog.models import Author, BibliographicRecord

pytestmark = pytest.mark.django_db


def test_record_form_creates_authors_from_text():
    form = BibliographicRecordForm(
        data={
            "title": "Dune",
            "authors_text": "Frank Herbert; Brian Herbert",
            "language": "fr",
            "document_type": "book",
        }
    )
    assert form.is_valid(), form.errors
    record = form.save()
    assert record.authors.count() == 2
    assert Author.objects.filter(full_name="Frank Herbert").exists()


def test_record_form_empty_isbn_stored_as_null():
    form = BibliographicRecordForm(
        data={"title": "Sans ISBN", "language": "fr", "document_type": "book"}
    )
    assert form.is_valid(), form.errors
    record = form.save()
    assert record.isbn_13 is None


def test_record_form_rejects_malformed_isbn13():
    form = BibliographicRecordForm(
        data={
            "title": "Mauvais ISBN",
            "isbn_13": "123",
            "language": "fr",
            "document_type": "book",
        }
    )
    assert not form.is_valid()
    assert "isbn_13" in form.errors


def test_record_form_reuses_existing_author():
    Author.objects.create(full_name="Frank Herbert")
    form = BibliographicRecordForm(
        data={
            "title": "Dune Messiah",
            "authors_text": "Frank Herbert",
            "language": "fr",
            "document_type": "book",
        }
    )
    assert form.is_valid(), form.errors
    form.save()
    assert Author.objects.filter(full_name="Frank Herbert").count() == 1


def test_bulk_create_form_limits_copies():
    form = ItemBulkCreateForm(
        data={
            "copies": 50,
            "state": "good",
            "acquisition_date": "2026-05-21",
            "acquisition_source": "donation",
        }
    )
    assert not form.is_valid()
    assert "copies" in form.errors
