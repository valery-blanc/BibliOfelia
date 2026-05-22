"""Tests lookup OpenLibrary. SPEC §6.1 (Task #6)."""
from __future__ import annotations

import httpx

from apps.catalog import openlibrary

_SAMPLE = {
    "ISBN:9782070612758": {
        "title": "Le Petit Prince",
        "subtitle": "",
        "authors": [{"name": "Antoine de Saint-Exupéry"}],
        "publishers": [{"name": "Gallimard"}],
        "publish_date": "1943",
    }
}


class _FakeResp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_lookup_isbn_parses_fields(monkeypatch):
    monkeypatch.setattr(openlibrary.httpx, "get", lambda *a, **k: _FakeResp(_SAMPLE))
    data = openlibrary.lookup_isbn("978-2-07-061275-8")
    assert data["title"] == "Le Petit Prince"
    assert data["authors_text"] == "Antoine de Saint-Exupéry"
    assert data["publisher"] == "Gallimard"
    assert data["publication_year"] == "1943"
    assert data["isbn_13"] == "9782070612758"


def test_lookup_isbn_network_error_returns_none(monkeypatch):
    def boom(*a, **k):
        raise httpx.ConnectError("box hors-ligne")

    monkeypatch.setattr(openlibrary.httpx, "get", boom)
    assert openlibrary.lookup_isbn("9782070612758") is None


def test_lookup_isbn_unknown_returns_none(monkeypatch):
    monkeypatch.setattr(openlibrary.httpx, "get", lambda *a, **k: _FakeResp({}))
    assert openlibrary.lookup_isbn("9782070612758") is None


def test_lookup_isbn_invalid_length():
    assert openlibrary.lookup_isbn("123") is None
