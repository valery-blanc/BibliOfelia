"""Sessions de scan OfeliaScan (FEAT-021 / Task #20).

ScanSession + ScanItem : OfeliaScan envoie des batchs d'items via l'API REST,
puis demande la finalisation qui matérialise les BibliographicRecord + Item.
"""
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0004_backfill_translation_fr"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ScanSession",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                (
                    "session_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("label", models.CharField(blank=True, max_length=120)),
                (
                    "state",
                    models.CharField(
                        choices=[("open", "Ouverte"), ("finalized", "Validée")],
                        default="open",
                        max_length=10,
                    ),
                ),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("finalized_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="scan_sessions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("processing_summary", models.JSONField(blank=True, default=dict)),
            ],
            options={
                "verbose_name": "session de scan",
                "verbose_name_plural": "sessions de scan",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="ScanItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("local_id", models.CharField(max_length=120)),
                (
                    "scan_kind",
                    models.CharField(
                        choices=[("ean13", "EAN13"), ("isbn", "ISBN"), ("manual", "Saisie manuelle")],
                        max_length=10,
                    ),
                ),
                ("scanned_value", models.CharField(blank=True, max_length=32)),
                ("metadata_title", models.CharField(blank=True, max_length=300)),
                ("metadata_authors", models.JSONField(blank=True, default=list)),
                ("metadata_language", models.CharField(blank=True, max_length=10)),
                ("metadata_publisher", models.CharField(blank=True, max_length=200)),
                ("metadata_year", models.IntegerField(blank=True, null=True)),
                ("location_code", models.CharField(blank=True, max_length=20)),
                ("item_state", models.CharField(blank=True, max_length=10)),
                ("copy_count", models.PositiveIntegerField(default=1)),
                ("scanned_at", models.DateTimeField()),
                ("notes", models.TextField(blank=True)),
                ("processed", models.BooleanField(default=False)),
                ("processing_result", models.JSONField(blank=True, default=dict)),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="catalog.scansession",
                    ),
                ),
            ],
            options={
                "verbose_name": "item scanné",
                "verbose_name_plural": "items scannés",
                "ordering": ["session", "id"],
            },
        ),
        migrations.AddConstraint(
            model_name="scanitem",
            constraint=models.UniqueConstraint(
                fields=("session", "local_id"), name="scanitem_unique_local"
            ),
        ),
    ]
