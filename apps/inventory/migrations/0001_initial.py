"""Migration initiale du récolement : InventorySession + InventoryScan.

SPEC §6.5 (Task #10). Rédigée à la main (makemigrations indisponible dans
l'environnement de dev au moment de l'écriture) ; à régénérer/vérifier avec
`python manage.py makemigrations --check inventory` au prochain boot.
"""
from __future__ import annotations

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalog", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="InventorySession",
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
                    "session_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("label", models.CharField(blank=True, max_length=120)),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("all", "Tout le fonds"),
                            ("location", "Un emplacement"),
                            ("category", "Une catégorie"),
                        ],
                        default="all",
                        max_length=10,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "En cours"),
                            ("closed", "Clôturée"),
                            ("finalized", "Validée"),
                        ],
                        default="open",
                        max_length=10,
                    ),
                ),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("closed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "scope_category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="catalog.category",
                    ),
                ),
                (
                    "scope_location",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="catalog.location",
                    ),
                ),
            ],
            options={
                "verbose_name": "session de récolement",
                "verbose_name_plural": "sessions de récolement",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="InventoryScan",
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
                ("ean13", models.CharField(max_length=13)),
                ("scanned_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("device", models.CharField(blank=True, max_length=80)),
                (
                    "item",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="inventory_scans",
                        to="catalog.item",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scans",
                        to="inventory.inventorysession",
                    ),
                ),
            ],
            options={
                "verbose_name": "pointage de récolement",
                "verbose_name_plural": "pointages de récolement",
                "ordering": ["-scanned_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="inventoryscan",
            constraint=models.UniqueConstraint(
                fields=("session", "ean13"),
                name="inventory_scan_unique_per_session",
            ),
        ),
    ]
