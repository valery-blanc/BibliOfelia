"""FEAT-046 — catalogage en scan caméra continu."""
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.catalog.models import (
    BibliographicRecord,
    Category,
    Item,
    ScanItem,
    ScanSession,
    ScanSessionState,
)

pytestmark = pytest.mark.django_db

VALID_ISBN = "9782070368228"  # EAN-13 valide (préfixe 978)


@pytest.fixture
def librarian(client):
    user = User.objects.create_user(username="lib", password="pw", role=Role.LIBRARIAN)
    client.force_login(user)
    return user


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """Évite tout appel réseau (OpenLibrary + multi-sources) dans les tests."""
    monkeypatch.setattr("apps.catalog.views.lookup_isbn", lambda raw: None)
    monkeypatch.setattr("apps.catalog.views.lookup_isbn_multi", lambda raw: None)


@pytest.fixture
def session(librarian):
    return ScanSession.objects.create(label="Lot test", created_by=librarian)


def test_create_session_redirects_to_hub(client, librarian):
    cat = Category.objects.create(code="ROM", name="Roman")
    resp = client.post(
        reverse("catalog:scan_session_create"),
        {"label": "Mon lot", "default_category": cat.pk, "default_location": ""},
    )
    assert resp.status_code == 302
    s = ScanSession.objects.get(label="Mon lot")
    assert s.default_category_id == cat.pk
    assert s.created_by_id == librarian.pk


def test_scan_add_creates_scanitem(client, librarian, session):
    resp = client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] and data["action"] == "created"
    assert data["count"] == 1
    assert ScanItem.objects.filter(session=session, scanned_value=VALID_ISBN).count() == 1


def test_scan_add_same_code_within_window_ignored(client, librarian, session):
    client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    resp = client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    data = resp.json()
    assert data["action"] == "ignored"
    assert ScanItem.objects.get(session=session, scanned_value=VALID_ISBN).copy_count == 1


@pytest.mark.django_db(transaction=True)  # vue non_atomic_requests → autocommit réel
def test_scan_add_no_duplicate_isbn_line(client, librarian, session):
    """Un même ISBN scanné plusieurs fois rapidement ne crée jamais 2 lignes
    (régression BUG 2026-05-31 : lookup HTTP entre SELECT et INSERT)."""
    for _ in range(4):
        client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    rows = ScanItem.objects.filter(session=session, scanned_value=VALID_ISBN)
    assert rows.count() == 1
    assert rows.first().copy_count == 1  # tenu en vue → pas d'incrément


def test_scan_add_after_gap_increments_copy(client, librarian, session):
    client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    # Simule un retrait + re-présentation : dernier vu il y a 10 s.
    ScanItem.objects.filter(session=session).update(
        scanned_at=timezone.now() - timedelta(seconds=10)
    )
    resp = client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    data = resp.json()
    assert data["action"] == "incremented"
    assert data["copy_count"] == 2
    assert ScanItem.objects.get(session=session).copy_count == 2


def test_scan_add_rejects_ofelia_and_member_codes(client, librarian, session):
    for code in ("2900000000000", "2910000000000"):
        resp = client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": code})
        assert resp.json()["action"] == "rejected"
    assert ScanItem.objects.filter(session=session).count() == 0


def test_scan_add_409_when_finalized(client, librarian, session):
    session.state = ScanSessionState.FINALIZED
    session.save(update_fields=["state"])
    resp = client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    assert resp.status_code == 409


def test_scan_item_delete(client, librarian, session):
    client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    item = ScanItem.objects.get(session=session)
    resp = client.post(reverse("catalog:scan_item_delete", args=[session.pk, item.pk]))
    assert resp.status_code == 302
    assert not ScanItem.objects.filter(pk=item.pk).exists()


def test_commit_finalize_creates_record_with_category_and_session(client, librarian, session):
    cat = Category.objects.create(code="ROM", name="Roman")
    client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    item = ScanItem.objects.get(session=session)
    # Titre/auteur sont en lecture seule sur le hub (issus du lookup ISBN). On
    # simule un lookup réussi en les posant directement sur le ScanItem ; le
    # commit ne lit que catégorie / emplacement / état / nb d'exemplaires.
    item.metadata_title = "Le Petit Prince"
    item.metadata_authors = ["Saint-Exupéry"]
    item.save(update_fields=["metadata_title", "metadata_authors"])
    resp = client.post(
        reverse("catalog:scan_session_commit", args=[session.pk]),
        {
            f"category_{item.pk}": cat.pk,
            f"location_{item.pk}": "",
            f"state_{item.pk}": "good",
            f"copies_{item.pk}": "2",
            "finalize": "1",
        },
    )
    assert resp.status_code == 302
    rec = BibliographicRecord.objects.get(isbn_13=VALID_ISBN)
    assert rec.title == "Le Petit Prince"
    assert rec.category_id == cat.pk
    copies = Item.objects.filter(record=rec)
    assert copies.count() == 2
    assert all(c.catalog_session_id == session.pk for c in copies)
    session.refresh_from_db()
    assert session.state == ScanSessionState.FINALIZED


def test_commit_finalize_matches_existing_record_untouched(client, librarian, session):
    existing = BibliographicRecord.objects.create(title="Titre d'origine", isbn_13=VALID_ISBN)
    client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    item = ScanItem.objects.get(session=session)
    client.post(
        reverse("catalog:scan_session_commit", args=[session.pk]),
        {
            f"title_{item.pk}": "Titre modifié (ignoré)",
            f"author_{item.pk}": "",
            f"language_{item.pk}": "fr",
            f"category_{item.pk}": "",
            f"location_{item.pk}": "",
            f"state_{item.pk}": "good",
            f"copies_{item.pk}": "1",
            "finalize": "1",
        },
    )
    # La notice existante n'est pas modifiée, on n'a pas créé de doublon.
    assert BibliographicRecord.objects.filter(isbn_13=VALID_ISBN).count() == 1
    existing.refresh_from_db()
    assert existing.title == "Titre d'origine"
    assert Item.objects.filter(record=existing, catalog_session=session).count() == 1


def test_labels_picker_filters_by_session(client, librarian, session):
    rec = BibliographicRecord.objects.create(title="X", isbn_13=VALID_ISBN)
    in_session = Item.objects.create(record=rec, catalog_session=session)
    other = Item.objects.create(record=rec)
    resp = client.get(reverse("printing:labels"), {"catalog_session": session.pk})
    assert resp.status_code == 200
    items = list(resp.context["items"])
    assert in_session in items
    assert other not in items


def test_hub_pages_render(client, librarian, session):
    Category.objects.create(code="ROM", name="Roman")
    client.post(reverse("catalog:scan_add", args=[session.pk]), {"ean": VALID_ISBN})
    for url in (
        reverse("catalog:scan_session_list"),
        reverse("catalog:scan_session_create"),
        reverse("catalog:scan_session", args=[session.pk]),
    ):
        assert client.get(url).status_code == 200


def test_readonly_cannot_access_cataloging(client):
    """Le catalogage est réservé librarian/superadmin : READONLY → 403 partout."""
    other = User.objects.create_user(username="ro", password="pw", role=Role.READONLY)
    client.force_login(other)
    assert client.get(reverse("catalog:scan_session_list")).status_code == 403
    resp = client.post(
        reverse("catalog:scan_session_create"),
        {"label": "x", "default_category": "", "default_location": ""},
    )
    assert resp.status_code == 403
    assert not ScanSession.objects.filter(label="x").exists()
