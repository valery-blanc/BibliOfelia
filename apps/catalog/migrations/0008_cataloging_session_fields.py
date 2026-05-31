"""FEAT-046 — catalogage caméra : rattachement session + défauts de lot.

- Item.catalog_session : retrouver/imprimer les exemplaires d'un lot.
- ScanItem.category : catégorie de la notice (par ligne).
- ScanSession.default_location / default_category : défauts du lot.
"""
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0007_retired_item_codes"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="catalog_session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="created_items",
                to="catalog.scansession",
            ),
        ),
        migrations.AddField(
            model_name="scanitem",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="catalog.category",
            ),
        ),
        migrations.AddField(
            model_name="scansession",
            name="default_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="catalog.category",
            ),
        ),
        migrations.AddField(
            model_name="scansession",
            name="default_location",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="+",
                to="catalog.location",
            ),
        ),
    ]
