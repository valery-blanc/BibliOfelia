"""FEAT-043 — Tombstones des codes Ofelia : un internal_id supprimé n'est
jamais réattribué à un nouvel exemplaire (étiquettes pouvant être imprimées).
"""
from __future__ import annotations

import pytest
from django.utils import timezone

from apps.accounts.models import Role
from apps.catalog.models import (
    BibliographicRecord,
    Item,
    RetiredItemCode,
)

pytestmark = pytest.mark.django_db


def test_signal_creates_tombstone_on_item_delete():
    rec = BibliographicRecord.objects.create(title="T")
    item = Item.objects.create(record=rec)
    internal_id = item.internal_id
    ean13 = item.ean13
    item.delete()
    tomb = RetiredItemCode.objects.get(internal_id=internal_id)
    assert tomb.ean13 == ean13
    assert tomb.record_title_snapshot == "T"
    assert tomb.reason == RetiredItemCode.REASON_ITEM_DELETE


def test_last_item_of_day_code_not_reused_after_delete():
    """Suppression du dernier item du jour : son code ne doit pas être
    réutilisé par le prochain create (le bug d'avant FEAT-043)."""
    rec = BibliographicRecord.objects.create(title="T")
    Item.objects.all().delete()
    RetiredItemCode.objects.all().delete()
    day_str = timezone.localdate().strftime("%Y%m%d")

    a = Item.objects.create(record=rec)
    b = Item.objects.create(record=rec)
    assert a.internal_id == f"OFL-{day_str}-0001"
    assert b.internal_id == f"OFL-{day_str}-0002"
    b.delete()  # tombstone 0002 créée

    c = Item.objects.create(record=rec)
    assert c.internal_id == f"OFL-{day_str}-0003", (
        f"Code 0002 ne doit pas être réutilisé, obtenu {c.internal_id}"
    )


def test_all_items_of_day_deleted_no_code_reused():
    """Suppression de TOUS les items du jour : la séquence ne repart pas
    à 0001, elle continue après le max retiré."""
    rec = BibliographicRecord.objects.create(title="T")
    Item.objects.all().delete()
    RetiredItemCode.objects.all().delete()
    day_str = timezone.localdate().strftime("%Y%m%d")

    items = [Item.objects.create(record=rec) for _ in range(3)]
    last = items[-1].internal_id  # OFL-{day}-0003
    for it in items:
        it.delete()

    new_item = Item.objects.create(record=rec)
    expected = f"OFL-{day_str}-0004"
    assert new_item.internal_id == expected, (
        f"Attendu {expected} (max retiré + 1), obtenu {new_item.internal_id}"
    )
    # Sanity : le dernier code retiré était bien 0003
    assert last.endswith("-0003")


def test_record_cascade_delete_creates_tombstones():
    rec = BibliographicRecord.objects.create(title="Cascade")
    a = Item.objects.create(record=rec)
    b = Item.objects.create(record=rec)
    ids = [a.internal_id, b.internal_id]
    rec.delete()  # CASCADE → pre_delete émis pour chaque Item
    assert RetiredItemCode.objects.filter(internal_id__in=ids).count() == 2


def test_bulk_delete_view_uses_bulk_delete_reason(client, django_user_model):
    """Quand la suppression passe par /catalog/bulk-delete/apply/, la
    tombstone doit avoir reason=bulk_delete et retired_by renseigné."""
    user = django_user_model.objects.create_user(
        username="admin", password="x", role=Role.SUPERADMIN, is_superuser=True
    )
    rec = BibliographicRecord.objects.create(title="Bulk")
    item = Item.objects.create(record=rec)
    internal_id = item.internal_id

    client.force_login(user)
    resp = client.post("/fr/catalog/bulk-delete/apply/", {"ids": [str(rec.pk)]})
    assert resp.status_code == 302

    tomb = RetiredItemCode.objects.get(internal_id=internal_id)
    assert tomb.reason == RetiredItemCode.REASON_BULK_DELETE
    assert tomb.retired_by_id == user.pk
    assert tomb.record_title_snapshot == "Bulk"
