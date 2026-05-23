"""Initial migration de l'app `api` — FEAT-023 ScanHandoff."""
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ScanHandoff",
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
                    "token",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, unique=True
                    ),
                ),
                (
                    "target_kind",
                    models.CharField(
                        choices=[
                            ("auto", "Auto-détection"),
                            ("book", "Livre"),
                            ("card", "Carte membre"),
                        ],
                        default="auto",
                        max_length=10,
                    ),
                ),
                (
                    "state",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("completed", "Terminé"),
                            ("cancelled", "Annulé"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("value", models.CharField(blank=True, max_length=64)),
                ("value_kind", models.CharField(blank=True, max_length=20)),
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("expires_at", models.DateTimeField()),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scan_handoffs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "completed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["state", "expires_at"],
                        name="api_scanhan_state_584c9f_idx",
                    ),
                ],
            },
        ),
    ]
