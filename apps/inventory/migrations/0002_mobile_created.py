"""Flag `mobile_created` sur InventorySession (FEAT-021 / Task #20).

Distingue les sessions de récolement créées depuis OfeliaScan (POST
/inventory-sessions via l'API REST) de celles créées depuis l'UI web.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="inventorysession",
            name="mobile_created",
            field=models.BooleanField(default=False),
        ),
    ]
