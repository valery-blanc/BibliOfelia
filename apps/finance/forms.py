"""Formulaires de caisse. FEAT-084."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    CashDirection,
    CashMovement,
    FeeKind,
    Invoice,
    InvoiceLine,
    Payment,
    PaymentMethod,
    Tariff,
)
from .money import config


def _amount_widget():
    return forms.NumberInput(attrs={"step": "0.01", "min": "0", "inputmode": "decimal"})


class InvoiceForm(forms.ModelForm):
    """En-tête de facture. Les lignes viennent du formset."""

    class Meta:
        model = Invoice
        fields = ["issue_date", "due_date", "note"]
        widgets = {
            # BUG-015 : format ISO obligatoire pour <input type="date">.
            "issue_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "due_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "note": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = date.today()
        if not self.instance.pk:
            self.fields["issue_date"].initial = today
            self.fields["due_date"].initial = today + timedelta(
                days=config()["payment_terms_days"]
            )
        self.fields["note"].required = False


class InvoiceLineForm(forms.ModelForm):
    class Meta:
        model = InvoiceLine
        fields = ["kind", "label", "amount", "quantity"]
        widgets = {"amount": _amount_widget()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("kind", "label", "amount", "quantity"):
            self.fields[name].required = False
        self.fields["quantity"].initial = 1


class BaseInvoiceLineFormSet(forms.BaseInlineFormSet):
    """Ignore les lignes vides, refuse une facture qui n'en aurait aucune.

    Une facture sans ligne s'enregistrerait à zéro et polluerait la
    numérotation sans rien représenter.
    """

    def clean(self):
        for form in self.forms:
            if getattr(form, "cleaned_data", None) is None:
                continue
            data = form.cleaned_data
            if not data.get("label") and not data.get("amount"):
                data["DELETE"] = True
                form.errors.clear()
                continue
            if not data.get("label"):
                form.add_error("label", _("Libellé obligatoire."))
            if data.get("amount") in (None, ""):
                form.add_error("amount", _("Montant obligatoire."))
            if not data.get("quantity"):
                data["quantity"] = 1
            if not data.get("kind"):
                data["kind"] = FeeKind.OTHER
        super().clean()
        kept = [
            form
            for form in self.forms
            if getattr(form, "cleaned_data", None)
            and not form.cleaned_data.get("DELETE")
        ]
        if not kept:
            raise forms.ValidationError(_("Ajoutez au moins une ligne à la facture."))


InvoiceLineFormSet = forms.inlineformset_factory(
    Invoice,
    InvoiceLine,
    form=InvoiceLineForm,
    formset=BaseInvoiceLineFormSet,
    extra=3,
    can_delete=True,
)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method", "paid_on", "note"]
        widgets = {
            "amount": _amount_widget(),
            "paid_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, invoice=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.invoice = invoice
        self.fields["note"].required = False
        self.fields["paid_on"].initial = date.today()
        if invoice is not None and not self.is_bound:
            self.fields["amount"].initial = invoice.balance

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0"):
            raise forms.ValidationError(_("Le montant doit être positif."))
        if self.invoice is not None and amount > self.invoice.balance:
            raise forms.ValidationError(
                _("Le montant dépasse le solde de la facture (%(b)s).")
                % {"b": self.invoice.balance}
            )
        return amount


class CashMovementForm(forms.ModelForm):
    """Mouvement saisi à la main : une dépense, ou une entrée hors facture."""

    class Meta:
        model = CashMovement
        fields = ["direction", "amount", "label", "occurred_on"]
        widgets = {
            "amount": _amount_widget(),
            "occurred_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["direction"].initial = CashDirection.OUT
        self.fields["occurred_on"].initial = date.today()

    def clean_amount(self):
        amount = self.cleaned_data["amount"]
        if amount <= Decimal("0"):
            raise forms.ValidationError(_("Le montant doit être positif."))
        return amount


class TariffForm(forms.ModelForm):
    class Meta:
        model = Tariff
        fields = ["kind", "label", "amount", "order", "is_active"]
        widgets = {"amount": _amount_widget()}


class FineForm(forms.Form):
    """Amende — saisie **manuelle** uniquement (décision Val, 2026-08-31).

    Aucun montant n'est calculé : le motif propose un tarif, le montant reste
    modifiable. Rien ne se facture dans le dos d'un employé.
    """

    tariff = forms.ModelChoiceField(
        queryset=Tariff.objects.none(),
        required=False,
        label=_("Motif"),
        empty_label=_("Autre motif (à décrire)"),
    )
    label = forms.CharField(label=_("Description"), max_length=200, required=False)
    amount = forms.DecimalField(
        label=_("Montant"), max_digits=10, decimal_places=2, widget=_amount_widget()
    )

    def __init__(self, *args, kind=FeeKind.FINE, **kwargs):
        super().__init__(*args, **kwargs)
        self.kind = kind
        self.fields["tariff"].queryset = Tariff.objects.filter(
            kind=kind, is_active=True
        )

    def clean(self):
        cleaned = super().clean()
        tariff = cleaned.get("tariff")
        if not cleaned.get("label"):
            if tariff is None:
                self.add_error("label", _("Décrivez le motif."))
            else:
                cleaned["label"] = tariff.label
        return cleaned


PAYMENT_METHOD_CASH = PaymentMethod.CASH
