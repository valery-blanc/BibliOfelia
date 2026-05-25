"""Tests vues catalogue. SPEC §6.1 (Task #6)."""
from __future__ import annotations

import pytest

from apps.accounts.models import Role
from apps.catalog.models import BibliographicRecord, Item, ItemStatus, Location

pytestmark = pytest.mark.django_db


@pytest.fixture
def librarian(django_user_model):
    return django_user_model.objects.create_user(
        username="biblio", password="motdepasse123", role=Role.LIBRARIAN
    )


@pytest.fixture
def readonly(django_user_model):
    return django_user_model.objects.create_user(
        username="lecteur", password="motdepasse123", role=Role.READONLY
    )


@pytest.fixture
def record():
    return BibliographicRecord.objects.create(title="Fondation")


def test_record_list_visible_to_readonly(client, readonly, record):
    client.force_login(readonly)
    resp = client.get("/fr/catalog/")
    assert resp.status_code == 200
    assert b"Fondation" in resp.content


def test_record_detail_shows_pending_waiting_list(client, readonly, record):
    """FEAT-034 : la fiche notice affiche la liste d'attente (réservations
    PENDING) au niveau notice même si aucun exemplaire n'est encore mis de côté."""
    from datetime import date, timedelta

    from apps.loans.models import Reservation, ReservationStatus
    from apps.members.models import Member, MemberCategory

    cat = MemberCategory.objects.create(code="AD", name="Adulte")
    m1 = Member.objects.create(first_name="Alice", last_name="A", category=cat)
    m2 = Member.objects.create(first_name="Bob", last_name="B", category=cat)
    Reservation.objects.create(
        record=record, member=m1, status=ReservationStatus.PENDING,
        expires_at=date.today() + timedelta(days=7),
    )
    Reservation.objects.create(
        record=record, member=m2, status=ReservationStatus.PENDING,
        expires_at=date.today() + timedelta(days=7),
    )
    client.force_login(readonly)
    resp = client.get(f"/fr/catalog/{record.pk}/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Liste d&#x27;attente" in body or "Liste d'attente" in body
    assert "Alice A" in body
    assert "Bob B" in body


def test_record_detail_shows_active_reservation_holder(client, readonly, record):
    """FEAT-034 : pour un exemplaire mis de côté, la fiche notice affiche le
    membre qui retient l'exemplaire."""
    from datetime import date, timedelta

    from apps.core.models import Setting
    from apps.loans.models import Reservation, ReservationStatus
    from apps.members.models import Member, MemberCategory

    Setting.set("pickup_hold_days", 5)
    cat = MemberCategory.objects.create(code="AD", name="Adulte")
    holder = Member.objects.create(
        first_name="Marie", last_name="Curie", category=cat
    )
    item = Item.objects.create(record=record, status=ItemStatus.RESERVED_FOR_PICKUP)
    Reservation.objects.create(
        record=record,
        member=holder,
        status=ReservationStatus.READY_FOR_PICKUP,
        ready_since=date.today(),
        expires_at=date.today() + timedelta(days=14),
        fulfilled_by_item=item,
    )

    client.force_login(readonly)
    resp = client.get(f"/fr/catalog/{record.pk}/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "Marie Curie" in body
    assert holder.card_number in body


def test_record_list_search_by_isbn13(client, readonly):
    """Bug remonté Val 2026-05-24 : la recherche par ISBN ne marchait pas
    dans le catalogue (FTS5 n'indexe pas les ISBN). Désormais classify_query
    route les ISBN vers un filtre direct sur isbn_13/isbn_10."""
    rec = BibliographicRecord.objects.create(
        title="Le livre cherché", isbn_13="9782070612758"
    )
    BibliographicRecord.objects.create(title="Autre livre")
    client.force_login(readonly)
    resp = client.get("/fr/catalog/", {"q": "9782070612758"})
    assert resp.status_code == 200
    assert b"Le livre cherch\xc3\xa9" in resp.content
    assert b"Autre livre" not in resp.content


def test_record_list_search_by_isbn10(client, readonly):
    BibliographicRecord.objects.create(title="Match isbn10", isbn_10="2070612759")
    client.force_login(readonly)
    resp = client.get("/fr/catalog/", {"q": "2070612759"})
    assert resp.status_code == 200
    assert b"Match isbn10" in resp.content


def test_record_list_search_by_item_ean13(client, readonly):
    """EAN13 commençant par 290 → matche via items__ean13."""
    rec = BibliographicRecord.objects.create(title="Notice avec exemplaire")
    item = Item.objects.create(record=rec)
    BibliographicRecord.objects.create(title="Sans exemplaire")
    client.force_login(readonly)
    resp = client.get("/fr/catalog/", {"q": item.ean13})
    assert resp.status_code == 200
    assert b"Notice avec exemplaire" in resp.content
    assert b"Sans exemplaire" not in resp.content


def test_record_list_search_by_tag_substring(client, readonly):
    """Filtre `q_tag` : recherche substring case-insensitive sur les tags."""
    from apps.catalog.models import Tag
    rec1 = BibliographicRecord.objects.create(title="Livre A")
    rec2 = BibliographicRecord.objects.create(title="Livre B")
    rec3 = BibliographicRecord.objects.create(title="Livre C")
    rec1.tags.add(Tag.objects.create(name="Science Fiction"))
    rec2.tags.add(Tag.objects.create(name="science populaire"))
    rec3.tags.add(Tag.objects.create(name="Histoire"))
    client.force_login(readonly)
    resp = client.get("/fr/catalog/", {"q_tag": "science"})
    assert resp.status_code == 200
    # Match Science Fiction et science populaire, pas Histoire
    assert b"Livre A" in resp.content
    assert b"Livre B" in resp.content
    assert b"Livre C" not in resp.content


def test_record_list_tag_filter_combines_with_other_filters(client, readonly):
    """q_tag combiné avec un filtre langue : AND."""
    from apps.catalog.models import Tag
    tag = Tag.objects.create(name="Roman")
    rec_fr = BibliographicRecord.objects.create(title="FR roman", language="fr")
    rec_en = BibliographicRecord.objects.create(title="EN roman", language="en")
    rec_fr.tags.add(tag)
    rec_en.tags.add(tag)
    client.force_login(readonly)
    resp = client.get("/fr/catalog/", {"q_tag": "roman", "language": "fr"})
    assert resp.status_code == 200
    assert b"FR roman" in resp.content
    assert b"EN roman" not in resp.content


def test_record_create_forbidden_for_readonly(client, readonly):
    client.force_login(readonly)
    resp = client.get("/fr/catalog/new/")
    assert resp.status_code == 403


def test_record_create_post(client, librarian):
    client.force_login(librarian)
    resp = client.post(
        "/fr/catalog/new/",
        {"title": "Le Meilleur des mondes", "language": "fr", "document_type": "book",
         "authors_text": "Aldous Huxley"},
    )
    assert resp.status_code == 302
    record = BibliographicRecord.objects.get(title="Le Meilleur des mondes")
    assert record.created_by_id == librarian.pk
    assert record.authors.count() == 1


def test_item_bulk_create(client, librarian, record):
    client.force_login(librarian)
    resp = client.post(
        f"/fr/catalog/{record.pk}/items/new/",
        {"copies": 4, "state": "good", "acquisition_date": "2026-05-21",
         "acquisition_source": "donation"},
    )
    assert resp.status_code == 302
    assert record.items.count() == 4
    eans = {it.ean13 for it in record.items.all()}
    assert len(eans) == 4  # chaque exemplaire a un EAN13 distinct


def test_item_discard_sets_status(client, librarian, record):
    item = Item.objects.create(record=record, location=Location.objects.create(code="A1"))
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/items/{item.pk}/discard/")
    assert resp.status_code == 302
    item.refresh_from_db()
    assert item.status == ItemStatus.DISCARDED


def test_item_discard_blocked_when_on_loan(client, librarian, record):
    item = Item.objects.create(record=record, status=ItemStatus.ON_LOAN)
    client.force_login(librarian)
    client.post(f"/fr/catalog/items/{item.pk}/discard/")
    item.refresh_from_db()
    assert item.status == ItemStatus.ON_LOAN


def test_record_delete_blocked_with_active_items(client, librarian, record):
    Item.objects.create(record=record, status=ItemStatus.AVAILABLE)
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/{record.pk}/delete/")
    assert resp.status_code == 302
    assert BibliographicRecord.objects.filter(pk=record.pk).exists()


def test_record_delete_succeeds_without_items(client, librarian, record):
    client.force_login(librarian)
    resp = client.post(f"/fr/catalog/{record.pk}/delete/")
    assert resp.status_code == 302
    assert not BibliographicRecord.objects.filter(pk=record.pk).exists()
