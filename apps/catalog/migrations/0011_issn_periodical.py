# FEAT-052 — Support des périodiques ISSN (code-barres EAN-13 préfixe 977).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0010_enrichmentjob_rate_limited_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="bibliographicrecord",
            name="issn",
            field=models.CharField(blank=True, db_index=True, max_length=8, null=True),
        ),
        migrations.AddConstraint(
            model_name="bibliographicrecord",
            constraint=models.UniqueConstraint(
                condition=models.Q(("issn__isnull", False)),
                fields=("issn",),
                name="record_issn_unique_not_null",
            ),
        ),
        migrations.AlterField(
            model_name="scanitem",
            name="scan_kind",
            field=models.CharField(
                choices=[
                    ("ean13", "EAN13"),
                    ("isbn", "ISBN"),
                    ("issn", "ISSN"),
                    ("manual", "Saisie manuelle"),
                ],
                max_length=10,
            ),
        ),
    ]
