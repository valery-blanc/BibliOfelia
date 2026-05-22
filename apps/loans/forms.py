"""Formulaires prêts / consultations / réservations. SPEC §6.3, §6.4."""
from __future__ import annotations

from django import forms
from django.utils.translation import gettext_lazy as _

from apps.members.models import Member

from .models import InHouseConsultation


class ConsultationForm(forms.ModelForm):
    """Consultation sur place. Usager et exemplaire optionnels (SPEC §6.3)."""

    class Meta:
        model = InHouseConsultation
        fields = ["member", "count", "date"]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].required = False
        self.fields["member"].queryset = Member.objects.order_by("last_name")


class ReservationForm(forms.Form):
    """Choix de l'usager pour une réservation sur une notice."""

    member = forms.ModelChoiceField(
        queryset=Member.objects.order_by("last_name", "first_name"),
        label=_("Réserver pour"),
    )
