"""Tests BUG-013 (fix pérenne) — wrapper set_language qui force FORCE_SCRIPT_NAME."""
from __future__ import annotations

import pytest
from django.test import RequestFactory, override_settings

from apps.core.i18n_views import set_language


@override_settings(FORCE_SCRIPT_NAME="/bibliofelia")
@pytest.mark.django_db
def test_set_language_prepends_prefix_and_swaps_lang_for_unresolved_url():
    """URL qui ne matche aucune route → préfixe ajouté + code langue échangé."""
    rf = RequestFactory(SCRIPT_NAME="/bibliofelia")
    req = rf.post("/i18n/setlang/", {"language": "en", "next": "/fr/page-inconnue/"})
    req.META["HTTP_REFERER"] = "http://host/bibliofelia/fr/page-inconnue/"
    resp = set_language(req)
    assert resp.status_code == 302
    assert resp["Location"] == "/bibliofelia/en/page-inconnue/"


@override_settings(FORCE_SCRIPT_NAME="/bibliofelia")
@pytest.mark.django_db
def test_set_language_does_not_double_prefix():
    """Si translate_url a déjà ajouté le préfixe, ne pas le doubler."""
    rf = RequestFactory(SCRIPT_NAME="/bibliofelia")
    req = rf.post("/i18n/setlang/", {"language": "en", "next": "/fr/"})
    req.META["HTTP_REFERER"] = "http://host/bibliofelia/fr/"
    resp = set_language(req)
    assert resp.status_code == 302
    assert resp["Location"] == "/bibliofelia/en/"
    assert not resp["Location"].startswith("/bibliofelia/bibliofelia/")


@override_settings(FORCE_SCRIPT_NAME="")
@pytest.mark.django_db
def test_set_language_no_prefix_in_dev():
    """Sans FORCE_SCRIPT_NAME (dev), ne rien préfixer."""
    rf = RequestFactory()
    req = rf.post("/i18n/setlang/", {"language": "en", "next": "/fr/"})
    req.META["HTTP_REFERER"] = "http://host/fr/"
    resp = set_language(req)
    assert resp.status_code == 302
    assert resp["Location"].startswith("/")
    assert not resp["Location"].startswith("/bibliofelia")


@pytest.mark.django_db
def test_set_language_url_name_resolves():
    """Sanity check : `{% url 'set_language' %}` continue à fonctionner."""
    from django.urls import reverse
    assert reverse("set_language") == "/i18n/setlang/"
