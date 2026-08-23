"""FEAT-082 — une seule source de vérité pour la version affichée.

Le pied de page codait `0.1.0-dev` en dur pendant que `/pairing/info`, `/health`,
le service Avahi et les rapports lisaient `settings.BIBLIOFELIA_VERSION` : les
deux pouvaient annoncer des versions différentes du même logiciel, et une
surcharge par variable d'environnement n'atteignait jamais l'écran.
"""
import pytest
from django.test import Client
from django.urls import reverse

from apps.accounts.models import Role, User

pytestmark = pytest.mark.django_db


def test_default_version_is_1_0(settings):
    assert settings.BIBLIOFELIA_VERSION == "1.0"
    assert "dev" not in settings.BIBLIOFELIA_VERSION


def test_footer_follows_the_setting(settings, client):
    """Le pied de page doit suivre le réglage, pas une constante recopiée."""
    settings.BIBLIOFELIA_VERSION = "9.9-test"
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    body = client.get(reverse("core:dashboard")).content.decode()
    assert "BibliOfelia v9.9-test" in body
    assert "0.1.0-dev" not in body


def test_pairing_info_exposes_the_same_version(settings):
    """`/pairing/info` est public (healthcheck du Dockerfile) et sert de contrat
    à OfeliaScan : il doit annoncer exactement la même version que l'écran."""
    settings.BIBLIOFELIA_VERSION = "9.9-test"
    data = Client().get("/api/v1/pairing/info").json()
    assert data["version"] == "9.9-test"
