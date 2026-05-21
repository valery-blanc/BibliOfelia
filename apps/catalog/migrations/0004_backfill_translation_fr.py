"""Backfill name_fr depuis name pour Category et Tag existants.

Modeltranslation copie déjà name → name_<default_lang> automatiquement au save
des nouveaux objets, mais pas pour les rows déjà en base avant FEAT-003.
"""
from django.db import migrations
from django.db.models import F


def backfill(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Tag = apps.get_model("catalog", "Tag")
    for model in (Category, Tag):
        model.objects.filter(name_fr__isnull=True).update(name_fr=F("name"))


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0003_translation_fields"),
    ]

    operations = [
        migrations.RunPython(backfill, noop),
    ]
