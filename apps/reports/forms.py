"""Formulaires des rapports : choix de période."""
from __future__ import annotations

from datetime import date, timedelta

from django import forms
from django.utils.translation import gettext_lazy as _


class PeriodForm(forms.Form):
    start = forms.DateField(
        label=_("Du"), widget=forms.DateInput(attrs={"type": "date"})
    )
    end = forms.DateField(
        label=_("Au"), widget=forms.DateInput(attrs={"type": "date"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            today = date.today()
            self.fields["start"].initial = today - timedelta(days=30)
            self.fields["end"].initial = today

    def clean(self):
        cleaned = super().clean()
        s, e = cleaned.get("start"), cleaned.get("end")
        if s and e and s > e:
            raise forms.ValidationError(_("La date de début doit précéder la fin."))
        return cleaned


class YearForm(forms.Form):
    year = forms.IntegerField(
        label=_("Année"), min_value=2000, max_value=2100,
        initial=date.today().year,
    )
