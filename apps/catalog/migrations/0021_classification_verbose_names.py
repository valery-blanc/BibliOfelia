# FEAT-094 — libellés « classification » / « code de classification ».
# Aucun changement de schéma : verbose_name seulement.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0020_excel_update_mode"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["code"],
                "verbose_name": "classification",
                "verbose_name_plural": "classifications",
            },
        ),
        migrations.AlterField(
            model_name="bibliographicrecord",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="records",
                to="catalog.category",
                verbose_name="classification",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="abbreviation",
            field=models.CharField(
                blank=True, max_length=20, verbose_name="code de classification"
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="catalog.category",
                verbose_name="classification parente",
            ),
        ),
    ]
