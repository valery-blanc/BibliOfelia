"""Fixtures des tests API.

Le throttling DRF (`ScopedRateThrottle`) stocke ses compteurs dans le cache ;
on le vide entre chaque test pour que les scopes `auth`/`isbn` repartent à zéro.
"""
from __future__ import annotations

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()
