"""Formulaire de lancement d'une session de récolement. SPEC §6.5."""
from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import InventoryScope, InventorySession


class InventorySessionForm(forms.ModelForm):
    class Meta:
        model = InventorySession
        fields = ["label", "scope_type", "scope_location", "scope_category"]

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get("scope_type")
        if scope == InventoryScope.LOCATION and not cleaned.get("scope_location"):
            self.add_error("scope_location", _("Choisissez un emplacement."))
        if scope == InventoryScope.CATEGORY and not cleaned.get("scope_category"):
            self.add_error("scope_category", _("Choisissez une catégorie."))
        return cleaned
