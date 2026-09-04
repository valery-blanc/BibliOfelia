"""Formulaires activités / animations / bouclement. FEAT-085, FEAT-086."""
from __future__ import annotations

from datetime import date

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import ActivityEntry, ActivityType, AnimationSession, AnimationType


def _hours_field():
    return forms.IntegerField(
        label=_("Heures"), min_value=0, max_value=24, required=False, initial=0
    )


def _minutes_field():
    return forms.IntegerField(
        label=_("Minutes"), min_value=0, max_value=59, required=False, initial=0
    )


class DurationMixin:
    """Saisie en heures + minutes, stockage en minutes.

    Une durée en décimal (« 1,5 h ») invite aux arrondis et se relit mal ; une
    durée en minutes est exacte et se somme sans surprise.

    Les champs sont déclarés dans chaque formulaire : la métaclasse de Django
    ne collecte pas les attributs d'un mixin qui n'est pas lui-même un Form.
    """

    def _clean_duration(self, cleaned):
        total = (cleaned.get("hours") or 0) * 60 + (cleaned.get("minutes_part") or 0)
        if total <= 0:
            raise forms.ValidationError(_("Indiquez le temps passé."))
        cleaned["minutes"] = total
        return cleaned

    def _init_duration(self):
        if self.instance and self.instance.pk:
            hours, minutes = divmod(self.instance.minutes, 60)
            self.fields["hours"].initial = hours
            self.fields["minutes_part"].initial = minutes


def _date_widget():
    # BUG-015 : format ISO obligatoire pour <input type="date">.
    return forms.DateInput(
        attrs={"type": "date", "max": date.today().isoformat()}, format="%Y-%m-%d"
    )


class ActivityEntryForm(DurationMixin, forms.ModelForm):
    hours = _hours_field()
    minutes_part = _minutes_field()

    class Meta:
        model = ActivityEntry
        fields = ["occurred_on", "activity_type", "note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurred_on"].widget = _date_widget()
        self.fields["occurred_on"].initial = date.today()
        self.fields["occurred_on"].help_text = _(
            "Modifiable : une journée oubliée se rattrape plus tard."
        )
        self.fields["note"].required = False
        self.fields["activity_type"].queryset = ActivityType.objects.filter(
            is_active=True
        )
        self._init_duration()

    def clean_occurred_on(self):
        value = self.cleaned_data["occurred_on"]
        if value > date.today():
            raise forms.ValidationError(_("On ne saisit pas le travail de demain."))
        return value

    def clean(self):
        return self._clean_duration(super().clean())

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.minutes = self.cleaned_data["minutes"]
        if commit:
            instance.save()
        return instance


class AnimationSessionForm(DurationMixin, forms.ModelForm):
    hours = _hours_field()
    minutes_part = _minutes_field()

    animation_type = forms.ModelChoiceField(
        queryset=AnimationType.objects.filter(is_active=True),
        required=False,
        label=_("Animation"),
        empty_label=_("— Nouvelle animation —"),
    )
    new_animation = forms.CharField(
        label=_("Nouvelle animation"),
        max_length=150,
        required=False,
        help_text=_("Laissez vide si vous avez choisi une animation dans la liste."),
    )
    # FEAT-085 (complément du 2026-09-01, demande Val) : les présents se
    # saisissent dès le formulaire de création, sans attendre l'écran de détail.
    # Champ texte plutôt que widget maison : sans JavaScript, on tape les codes
    # séparés par des espaces ou des virgules et ça marche quand même.
    attendee_codes = forms.CharField(
        label=_("Membres présents"),
        required=False,
        widget=forms.TextInput(attrs={
            "autocomplete": "off",
            "data-attendee-input": "",
            "placeholder": _("Scannez une carte ou tapez les 4 derniers chiffres"),
        }),
        help_text=_(
            "Plusieurs cartes séparées par un espace ou une virgule. "
            "Vous pourrez aussi en ajouter après enregistrement."
        ),
    )

    class Meta:
        model = AnimationSession
        fields = ["occurred_on", "non_member_adults", "non_member_children", "note"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["occurred_on"].widget = _date_widget()
        self.fields["occurred_on"].initial = date.today()
        self.fields["note"].required = False
        self.fields["non_member_adults"].initial = 0
        self.fields["non_member_children"].initial = 0
        if self.instance and self.instance.pk:
            self.fields["animation_type"].initial = self.instance.animation_type
        self._init_duration()

    def clean_occurred_on(self):
        value = self.cleaned_data["occurred_on"]
        if value > date.today():
            raise forms.ValidationError(_("On ne saisit pas le travail de demain."))
        return value

    def clean(self):
        cleaned = self._clean_duration(super().clean())
        if not cleaned.get("animation_type") and not (
            cleaned.get("new_animation") or ""
        ).strip():
            self.add_error(
                "new_animation",
                _("Choisissez une animation ou donnez un intitulé."),
            )
        return cleaned

    def save(self, commit=True, user=None):
        instance = super().save(commit=False)
        instance.minutes = self.cleaned_data["minutes"]
        new_label = (self.cleaned_data.get("new_animation") or "").strip()
        if new_label:
            instance.animation_type = AnimationType.get_or_create_by_label(
                new_label, user=user
            )
        else:
            instance.animation_type = self.cleaned_data["animation_type"]
        if commit:
            instance.save()
        return instance


class ActivityTypeForm(forms.ModelForm):
    class Meta:
        model = ActivityType
        fields = ["label", "order", "is_active"]


class AnimationTypeForm(forms.ModelForm):
    class Meta:
        model = AnimationType
        fields = ["label", "is_active"]
