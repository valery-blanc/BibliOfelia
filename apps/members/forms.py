"""Formulaires usagers. SPEC §6.2."""
from __future__ import annotations

from datetime import date

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models import Member


class MemberForm(forms.ModelForm):
    """Inscription / édition d'un usager.

    `card_number` et `expiration_date` sont calculés par `Member.save()` si
    laissés vides ; `expiration_date` reste ajustable (SPEC §6.2).
    """

    class Meta:
        model = Member
        fields = [
            "first_name", "last_name", "category", "preferred_language",
            "birth_date", "contact_phone", "address", "registration_date",
            "expiration_date", "parent_account", "photo", "notes",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "registration_date": forms.DateInput(attrs={"type": "date"}),
            "expiration_date": forms.DateInput(attrs={"type": "date"}),
            "address": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiration_date"].required = False
        self.fields["registration_date"].help_text = _(
            "Par défaut : aujourd'hui."
        )
        if not self.fields["registration_date"].initial:
            self.fields["registration_date"].initial = date.today
        self.fields["preferred_language"].widget = forms.Select(
            choices=[("", _("Langue de la bibliothèque"))] + list(settings.LANGUAGES)
        )
        # Un usager ne peut pas être son propre compte parent.
        parents = Member.objects.all()
        if self.instance and self.instance.pk:
            parents = parents.exclude(pk=self.instance.pk)
        self.fields["parent_account"].queryset = parents
