"""FEAT-095 — lecture des emplacements cochés dans un filtre de recherche."""
from __future__ import annotations

import pytest
from django.http import QueryDict

from apps.catalog.location_filter import selected_location_ids
from apps.catalog.models import Location

pytestmark = pytest.mark.django_db


def test_empty_means_no_filter():
    assert selected_location_ids(QueryDict("")) == []
    assert selected_location_ids({}) == []


def test_several_ids_from_querystring():
    a = Location.objects.create(code="A1")
    b = Location.objects.create(code="A2")
    params = QueryDict(mutable=True)
    params.setlist("location", [str(a.pk), str(b.pk)])
    assert selected_location_ids(params) == [a.pk, b.pk]


def test_location_code_from_old_printing_bookmark():
    loc = Location.objects.create(code="A1")
    params = QueryDict("location=A1")
    assert selected_location_ids(params) == [loc.pk]


def test_duplicate_values_are_unique_and_keep_order():
    a = Location.objects.create(code="A1")
    params = QueryDict(mutable=True)
    params.setlist("location", [str(a.pk), "A1", str(a.pk)])
    assert selected_location_ids(params) == [a.pk]
