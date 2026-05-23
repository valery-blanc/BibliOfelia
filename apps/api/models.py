"""Modèles propres à l'app `api`.

FEAT-023 — `ScanHandoff` : protocole single-scan entre BibliOfelia web et
OfeliaScan. Le navigateur crée un handoff (token UUID + TTL 5 min) via session,
ouvre un deep-link `ofeliascan://scan-one?token=...`, et poll le résultat ;
OfeliaScan POST la valeur via JWT. Token bearer single-use.
"""
from __future__ import annotations

import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


HANDOFF_TTL_SECONDS = 5 * 60


class ScanHandoffState(models.TextChoices):
    PENDING = "pending", _("En attente")
    COMPLETED = "completed", _("Terminé")
    CANCELLED = "cancelled", _("Annulé")


class ScanHandoffTarget(models.TextChoices):
    AUTO = "auto", _("Auto-détection")
    BOOK = "book", _("Livre")
    CARD = "card", _("Carte membre")


class ScanHandoff(models.Model):
    """Single-scan handoff entre BibliOfelia web et OfeliaScan (FEAT-023).

    Créé par une page web (session-auth, librarian), consommé par OfeliaScan
    (JWT) qui POST la valeur scannée. Le navigateur récupère la valeur par
    polling. Token bearer single-use, TTL 5 min.
    """

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="scan_handoffs",
    )
    target_kind = models.CharField(
        max_length=10,
        choices=ScanHandoffTarget.choices,
        default=ScanHandoffTarget.AUTO,
    )
    state = models.CharField(
        max_length=10,
        choices=ScanHandoffState.choices,
        default=ScanHandoffState.PENDING,
    )
    value = models.CharField(max_length=64, blank=True)
    value_kind = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["state", "expires_at"]),
        ]

    def __str__(self):
        return f"ScanHandoff({self.token}, {self.state})"

    def save(self, *args, **kwargs):
        if not self.pk and not self.expires_at:
            base = self.created_at or timezone.now()
            self.expires_at = base + timedelta(seconds=HANDOFF_TTL_SECONDS)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        return (
            self.state == ScanHandoffState.PENDING
            and timezone.now() >= self.expires_at
        )

    def effective_state(self) -> str:
        """`expired` calculé à la volée si TTL dépassé sans completion."""
        if self.is_expired:
            return "expired"
        return self.state
