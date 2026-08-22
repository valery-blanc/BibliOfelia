"""Formulaires du wizard de premier démarrage. SPEC §11.3.

Chaque étape (1..7 utiles + 8 récap) a son propre Form ; les données sont
stockées en session entre les étapes.
"""
from __future__ import annotations

from django import forms
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _


LANGUAGE_CHOICES = [
    ("fr", "Français"), ("en", "English"), ("es", "Español"), ("mg", "Malagasy"),
]


class Step1LanguageForm(forms.Form):
    """Choix de la langue de l'interface du wizard lui-même."""
    language = forms.ChoiceField(label=_("Langue"), choices=LANGUAGE_CHOICES, initial="fr")


class Step2LibraryForm(forms.Form):
    name = forms.CharField(label=_("Nom de la bibliothèque"), max_length=120)
    box_name = forms.CharField(
        label=_("Nom de la box (mDNS)"),
        max_length=80,
        help_text=_("Visible par OfeliaScan."),
        initial="BibliOfelia",
    )
    address = forms.CharField(label=_("Adresse"), required=False,
                              widget=forms.Textarea(attrs={"rows": 3}))


class Step3LanguagesForm(forms.Form):
    enabled = forms.MultipleChoiceField(
        label=_("Langues activées"),
        choices=LANGUAGE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=["fr"],
    )
    default = forms.ChoiceField(label=_("Langue par défaut"), choices=LANGUAGE_CHOICES, initial="fr")

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("default") and cleaned.get("default") not in cleaned.get("enabled", []):
            raise forms.ValidationError(_("La langue par défaut doit être activée."))
        return cleaned


class Step4SuperadminForm(forms.Form):
    username = forms.CharField(label=_("Identifiant"), max_length=30)
    first_name = forms.CharField(label=_("Prénom"), required=False, max_length=80)
    last_name = forms.CharField(label=_("Nom"), required=False, max_length=80)
    email = forms.EmailField(label=_("Email"), required=False)
    password = forms.CharField(label=_("Mot de passe"), widget=forms.PasswordInput)
    password_confirm = forms.CharField(label=_("Confirmer"), widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password") != cleaned.get("password_confirm"):
            raise forms.ValidationError(_("Les mots de passe ne correspondent pas."))
        validate_password(cleaned.get("password") or "")
        return cleaned


class Step5BackupForm(forms.Form):
    usb_path = forms.CharField(label=_("Chemin clé USB"), max_length=200, initial="/backup")
    hourly_enabled = forms.BooleanField(label=_("Sauvegarde horaire automatique"),
                                        required=False, initial=True)
    cloud_enabled = forms.BooleanField(label=_("Sauvegarde cloud (optionnel)"),
                                       required=False)
    cloud_remote = forms.CharField(label=_("Remote rclone"), required=False, max_length=120)


class Step6ZerotierForm(forms.Form):
    enabled = forms.BooleanField(label=_("Activer ZeroTier"), required=False)
    network_id = forms.CharField(label=_("Network ID"), required=False, max_length=32)


class Step7DemoForm(forms.Form):
    install_demo = forms.BooleanField(
        label=_("Installer des données de démonstration (50 notices, 20 usagers, prêts)"),
        required=False,
    )
