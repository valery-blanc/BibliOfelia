"""Tests Item._assign_codes — génération internal_id sans collision.

BUG 2026-05-24 : `count()+1` provoquait des collisions UNIQUE en présence de
trous dans la séquence des internal_id du jour (sessions OfeliaScan échouées,
suppressions). Le fix utilise MAX(internal_id)+1.
"""
from __future__ import annotations

import pytest
from django.utils import timezone

from apps.catalog.models import BibliographicRecord, Item

pytestmark = pytest.mark.django_db


def test_internal_id_uses_max_not_count_when_sequence_has_gaps():
    """Si on a déjà OFL-{today}-0005, 0006, 0009 en base et qu'on crée un
    nouvel item, l'internal_id doit être 0010 (= max+1), pas 0004 (= count+1)."""
    record = BibliographicRecord.objects.create(title="Test")
    day_str = timezone.localdate().strftime("%Y%m%d")

    # Crée 3 items avec des internal_id manuels comportant des trous
    Item.objects.filter(pk__isnull=False).delete()  # clean state
    items_to_seed = [
        f"OFL-{day_str}-0005",
        f"OFL-{day_str}-0006",
        f"OFL-{day_str}-0009",
    ]
    for ext_id in items_to_seed:
        # Crée un item avec un internal_id explicite pour seeder les trous.
        # ean13 laissé vide → _assign_codes le génère à partir du pk (unique).
        Item(record=record, internal_id=ext_id).save()

    # Maintenant on crée un nouvel item via la voie normale
    new_item = Item.objects.create(record=record)
    expected = f"OFL-{day_str}-0010"
    assert new_item.internal_id == expected, (
        f"Attendu {expected} (max+1), obtenu {new_item.internal_id}"
    )


def test_internal_id_sequential_creation_works():
    """Création séquentielle de 5 items : internal_id incrémentés 1→5."""
    record = BibliographicRecord.objects.create(title="Test")
    day_str = timezone.localdate().strftime("%Y%m%d")
    Item.objects.filter(pk__isnull=False).delete()
    items = [Item.objects.create(record=record) for _ in range(5)]
    expected = [f"OFL-{day_str}-{i:04d}" for i in range(1, 6)]
    assert [i.internal_id for i in items] == expected


def test_internal_id_first_of_day_is_0001():
    record = BibliographicRecord.objects.create(title="Test")
    day_str = timezone.localdate().strftime("%Y%m%d")
    Item.objects.filter(pk__isnull=False).delete()
    item = Item.objects.create(record=record)
    assert item.internal_id == f"OFL-{day_str}-0001"
