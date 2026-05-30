"""Formulaire de lancement d'une session de récolement. SPEC §6.5.

FEAT-045 : périmètre réduit à « Tout le fonds » / « Un emplacement ». Le scope
Catégorie reste en base (énum + champ `scope_category`) pour ne pas casser les
sessions historiques, mais n'est plus proposé dans l'UI.
"""
from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import InventoryScope, InventorySession

# Périmètres proposés dans l'UI (FEAT-045 : Catégorie retirée).
_SCOPE_CHOICES = [
    (InventoryScope.ALL.value, InventoryScope.ALL.label),
    (InventoryScope.LOCATION.value, InventoryScope.LOCATION.label),
]


class InventorySessionForm(forms.ModelForm):
    scope_type = forms.ChoiceField(
        choices=_SCOPE_CHOICES,
        initial=InventoryScope.ALL.value,
        label=_("Périmètre"),
    )

    class Meta:
        model = InventorySession
        fields = ["label", "scope_type", "scope_location"]

    def clean(self):
        cleaned = super().clean()
        scope = cleaned.get("scope_type")
        if scope == InventoryScope.LOCATION and not cleaned.get("scope_location"):
            self.add_error("scope_location", _("Choisissez un emplacement."))
        if scope == InventoryScope.ALL:
            # « Tout le fonds » : on ignore tout emplacement éventuellement posté.
            cleaned["scope_location"] = None
        return cleaned
