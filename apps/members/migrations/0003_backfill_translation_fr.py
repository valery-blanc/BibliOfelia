"""Backfill name_fr depuis name pour les MemberCategory existantes."""
from django.db import migrations
from django.db.models import F


def backfill(apps, schema_editor):
    MemberCategory = apps.get_model("members", "MemberCategory")
    MemberCategory.objects.filter(name_fr__isnull=True).update(name_fr=F("name"))


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0002_translation_fields"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
