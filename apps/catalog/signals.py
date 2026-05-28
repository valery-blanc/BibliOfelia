"""FEAT-043 : tombstones des codes Ofelia (internal_id).

Un signal `pre_delete` sur Item insère une ligne dans RetiredItemCode avant
toute suppression (incluant CASCADE depuis BibliographicRecord). Combiné à
`Item._assign_codes()` qui prend en compte les codes retirés, cela garantit
qu'un internal_id supprimé n'est jamais réattribué à un nouvel exemplaire.

Le `retired_by` et le `reason=bulk_delete` sont positionnés en amont par la
vue bulk_delete (création préalable de la tombstone) ; pour les autres
chemins (admin, suppression unitaire), le signal crée la tombstone avec
reason=item_delete et retired_by=NULL.
"""
from __future__ import annotations

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from .models import Item, RetiredItemCode


@receiver(pre_delete, sender=Item)
def retire_item_code(sender, instance: Item, **kwargs) -> None:
    if not instance.internal_id:
        return
    record_title = ""
    try:
        record_title = instance.record.title or ""
    except Exception:
        pass
    RetiredItemCode.objects.get_or_create(
        internal_id=instance.internal_id,
        defaults={
            "ean13": instance.ean13 or "",
            "record_title_snapshot": record_title[:255],
            "reason": RetiredItemCode.REASON_ITEM_DELETE,
        },
    )
