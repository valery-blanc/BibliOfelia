# FEAT-054 — Méthode de saisie d'un lot de catalogage (mobile / caméra / douchette).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0011_issn_periodical"),
    ]

    operations = [
        migrations.AddField(
            model_name="scansession",
            name="input_mode",
            field=models.CharField(
                choices=[
                    ("mobile", "OfeliaScan"),
                    ("camera", "Caméra"),
                    ("douchette", "Douchette"),
                ],
                default="camera",
                max_length=10,
            ),
        ),
    ]
