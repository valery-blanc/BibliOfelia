"""Formulaires usagers. SPEC §6.2."""
from __future__ import annotations

from datetime import date

from dateutil.relativedelta import relativedelta
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
            # BUG-015 : format ISO obligatoire pour <input type="date">,
            # sinon Django rend au format locale (« 25 mai 2026 »), illisible
            # par le widget HTML5 → input vide en édition.
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "registration_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "expiration_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
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
        # FEAT-037 : à la création, pré-remplir expiration_date = today + 1 an.
        # Le JS recalcule à chaque change de registration_date. Le serveur reste
        # autoritaire (Member.save() recalcule via category.card_validity_months
        # si le champ est vidé à la main).
        creating = not (self.instance and self.instance.pk)
        if creating and not self.fields["expiration_date"].initial:
            self.fields["expiration_date"].initial = (
                date.today() + relativedelta(years=1)
            )
        self.fields["preferred_language"].widget = forms.Select(
            choices=[("", _("Langue de la bibliothèque"))] + list(settings.LANGUAGES)
        )
        # Un usager ne peut pas être son propre compte parent.
        parents = Member.objects.all()
        if self.instance and self.instance.pk:
            parents = parents.exclude(pk=self.instance.pk)
        self.fields["parent_account"].queryset = parents
