"""Le guide s'ouvre dans la langue de l'application."""
import pytest

from apps.accounts.models import Role, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(db):
    return User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)


def test_french_guide_has_no_language_prefix(client, librarian):
    client.force_login(librarian)
    body = client.get("/fr/").content.decode()
    assert 'href="/docs/"' in body
    assert 'href="/docs/fr/"' not in body


def test_other_languages_open_the_matching_guide(client, librarian):
    client.force_login(librarian)
    body = client.get("/en/").content.decode()
    assert 'href="/docs/en/"' in body
    body = client.get("/es/").content.decode()
    assert 'href="/docs/es/"' in body
