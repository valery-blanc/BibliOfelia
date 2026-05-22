"""Modèles de récolement (inventaire). SPEC §6.5.

InventorySession : une campagne de pointage, avec son périmètre.
InventoryScan    : un EAN13 pointé pendant la session (web ou OfeliaScan).
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class InventoryScope(models.TextChoices):
    ALL = "all", _("Tout le fonds")
    LOCATION = "location", _("Un emplacement")
    CATEGORY = "category", _("Une catégorie")


class InventoryStatus(models.TextChoices):
    OPEN = "open", _("En cours")
    CLOSED = "closed", _("Clôturée")
    FINALIZED = "finalized", _("Validée")


class InventorySession(models.Model):
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    label = models.CharField(max_length=120, blank=True)
    scope_type = models.CharField(
        max_length=10, choices=InventoryScope.choices, default=InventoryScope.ALL
    )
    scope_location = models.ForeignKey(
        "catalog.Location", null=True, blank=True, on_delete=models.SET_NULL
    )
    scope_category = models.ForeignKey(
        "catalog.Category", null=True, blank=True, on_delete=models.SET_NULL
    )
    status = models.CharField(
        max_length=10, choices=InventoryStatus.choices, default=InventoryStatus.OPEN
    )
    started_at = models.DateTimeField(default=timezone.now)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    # True si la session a été créée depuis OfeliaScan (POST /inventory-sessions
    # via l'API REST) plutôt que depuis l'UI web. Permet à l'UI librarian de
    # distinguer les sessions « mobiles » dans la liste (FEAT-021 / Task #20).
    mobile_created = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("session de récolement")
        verbose_name_plural = _("sessions de récolement")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return self.label or f"Récolement {self.started_at:%Y-%m-%d}"

    @property
    def is_open(self) -> bool:
        return self.status == InventoryStatus.OPEN


class InventoryScan(models.Model):
    session = models.ForeignKey(
        InventorySession, related_name="scans", on_delete=models.CASCADE
    )
    ean13 = models.CharField(max_length=13)
    item = models.ForeignKey(
        "catalog.Item",
        null=True,
        blank=True,
        related_name="inventory_scans",
        on_delete=models.SET_NULL,
    )
    scanned_at = models.DateTimeField(default=timezone.now)
    device = models.CharField(max_length=80, blank=True)

    class Meta:
        verbose_name = _("pointage de récolement")
        verbose_name_plural = _("pointages de récolement")
        ordering = ["-scanned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "ean13"], name="inventory_scan_unique_per_session"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.ean13} @ {self.session_id}"
