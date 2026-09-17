# FEAT-094 — libellés « classification » sur le périmètre de récolement.
# Le scope n'est plus proposé dans l'UI (FEAT-045) ; le verbose_name suit
# le vocabulaire du catalogue.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0021_classification_verbose_names"),
        ("inventory", "0004_alter_inventorysession_label_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventorysession",
            name="scope_category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="catalog.category",
                verbose_name="classification",
            ),
        ),
        migrations.AlterField(
            model_name="inventorysession",
            name="scope_type",
            field=models.CharField(
                choices=[
                    ("all", "Tout le fonds"),
                    ("location", "Un emplacement"),
                    ("category", "Une classification"),
                ],
                default="all",
                max_length=10,
                verbose_name="périmètre",
            ),
        ),
    ]
