"""Modèles partagés : Setting (paramètres globaux JSON)."""
from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


class Setting(models.Model):
    """Paramètres globaux key/value JSON. Voir SPEC §5.2 (Setting)."""

    key = models.CharField(max_length=100, primary_key=True)
    value = models.JSONField(default=dict, blank=True)
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("paramètre")
        verbose_name_plural = _("paramètres")
        ordering = ["key"]

    def __str__(self) -> str:
        return self.key

    @classmethod
    def get(cls, key: str, default=None):
        try:
            return cls.objects.get(pk=key).value
        except cls.DoesNotExist:
            return default

    @classmethod
    def set(cls, key: str, value, description: str = "") -> "Setting":
        obj, _ = cls.objects.update_or_create(
            pk=key, defaults={"value": value, "description": description or ""}
        )
        return obj
