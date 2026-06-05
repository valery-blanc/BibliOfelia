"""FEAT-050 — modèle ExcelCatalogJob (catalogage Excel : vérification + import)."""
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0008_cataloging_session_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="ExcelCatalogJob",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "mode",
                    models.CharField(
                        choices=[("verify", "Vérification"), ("import", "Import")],
                        max_length=10,
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("running", "En cours"),
                            ("finished", "Terminé"),
                            ("failed", "Échec"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("uploaded_file", models.FileField(upload_to="excel_jobs/%Y/%m/")),
                (
                    "result_file",
                    models.FileField(
                        blank=True, null=True, upload_to="excel_jobs/%Y/%m/"
                    ),
                ),
                ("total", models.PositiveIntegerField(default=0)),
                ("processed", models.PositiveIntegerField(default=0)),
                ("matched_by_isbn", models.PositiveIntegerField(default=0)),
                ("matched_by_ta", models.PositiveIntegerField(default=0)),
                ("not_found", models.PositiveIntegerField(default=0)),
                ("errors", models.PositiveIntegerField(default=0)),
                ("report", models.JSONField(blank=True, default=list)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="excel_catalog_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scan_session",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="excel_jobs",
                        to="catalog.scansession",
                    ),
                ),
            ],
            options={
                "verbose_name": "catalogage Excel",
                "verbose_name_plural": "catalogages Excel",
                "ordering": ["-created_at"],
            },
        ),
    ]
