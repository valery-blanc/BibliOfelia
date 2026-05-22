"""Formulaires des paramètres (§6.6).

Chaque formulaire pilote un sous-ensemble de clés `Setting` (JSON). On valide
ici les valeurs et on délègue la persistance à `services.save_settings_form`.
"""
from __future__ import annotations

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models import Setting


def _initial_dict(key: str, default=None) -> dict:
    v = Setting.get(key, default if default is not None else {})
    return v if isinstance(v, dict) else (default or {})


class LibraryIdentityForm(forms.Form):
    KEY = "library_identity"

    name = forms.CharField(label=_("Nom de la bibliothèque"), max_length=120)
    box_name = forms.CharField(
        label=_("Nom de la box (mDNS)"), max_length=80,
        help_text=_("Visible par OfeliaScan lors de l'appairage."),
    )
    address = forms.CharField(label=_("Adresse"), widget=forms.Textarea(attrs={"rows": 3}), required=False)
    email = forms.EmailField(label=_("Contact (email)"), required=False)
    phone = forms.CharField(label=_("Téléphone"), required=False, max_length=40)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["name"].initial = Setting.get("library_name", data.get("name", ""))
            self.fields["box_name"].initial = Setting.get("box_name", data.get("box_name", ""))
            self.fields["address"].initial = data.get("address", "")
            self.fields["email"].initial = data.get("email", "")
            self.fields["phone"].initial = data.get("phone", "")

    def save(self) -> None:
        data = self.cleaned_data
        Setting.set("library_name", data["name"], "Nom affiché de la bibliothèque")
        Setting.set("box_name", data["box_name"], "Nom mDNS publié")
        Setting.set(self.KEY, {
            "name": data["name"],
            "box_name": data["box_name"],
            "address": data.get("address", ""),
            "email": data.get("email", ""),
            "phone": data.get("phone", ""),
        }, "Identité bibliothèque")


class LanguagesForm(forms.Form):
    KEY = "languages_config"

    enabled = forms.MultipleChoiceField(
        label=_("Langues activées"),
        widget=forms.CheckboxSelectMultiple,
    )
    default = forms.ChoiceField(label=_("Langue par défaut"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("fr", "Français"), ("en", "English"), ("es", "Español"), ("mg", "Malagasy")]
        self.fields["enabled"].choices = choices
        self.fields["default"].choices = choices
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["enabled"].initial = data.get(
                "enabled", [c for c, _ in settings.LANGUAGES]
            )
            self.fields["default"].initial = data.get("default", settings.LANGUAGE_CODE)

    def clean(self):
        cleaned = super().clean()
        enabled = cleaned.get("enabled", [])
        default = cleaned.get("default")
        if default and default not in enabled:
            raise forms.ValidationError(
                _("La langue par défaut doit être activée.")
            )
        return cleaned

    def save(self) -> None:
        Setting.set(self.KEY, {
            "enabled": self.cleaned_data["enabled"],
            "default": self.cleaned_data["default"],
        }, "Langues actives (effectif au prochain redémarrage)")


class BackupConfigForm(forms.Form):
    """SPEC §8 : chemin USB, fréquence, cloud opt-in."""
    KEY = "backup_config"

    usb_path = forms.CharField(label=_("Chemin clé USB"), max_length=200,
                               initial=settings.BACKUP_USB_PATH)
    hourly_enabled = forms.BooleanField(label=_("Sauvegarde horaire"), required=False, initial=True)
    cloud_enabled = forms.BooleanField(label=_("Sauvegarde cloud (rclone)"), required=False)
    cloud_remote = forms.CharField(
        label=_("Remote rclone"), required=False, max_length=120,
        help_text=_("Ex: ofelia:bibliofelia"),
    )
    encryption_passphrase_set = forms.BooleanField(
        label=_("Passphrase de chiffrement configurée"),
        required=False, disabled=True,
        help_text=_("Renseignée via la commande `setup_backup_encryption`."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["usb_path"].initial = data.get("usb_path", settings.BACKUP_USB_PATH)
            self.fields["hourly_enabled"].initial = data.get("hourly_enabled", True)
            self.fields["cloud_enabled"].initial = data.get("cloud_enabled", False)
            self.fields["cloud_remote"].initial = data.get("cloud_remote", "")
            self.fields["encryption_passphrase_set"].initial = bool(
                Setting.get("backup_encryption_passphrase_hash")
            )

    def save(self) -> None:
        Setting.set(self.KEY, {
            "usb_path": self.cleaned_data["usb_path"],
            "hourly_enabled": bool(self.cleaned_data["hourly_enabled"]),
            "cloud_enabled": bool(self.cleaned_data["cloud_enabled"]),
            "cloud_remote": self.cleaned_data.get("cloud_remote", ""),
        }, "Configuration sauvegardes")


class LabelFormatForm(forms.Form):
    KEY = "label_format"

    item_width_mm = forms.IntegerField(label=_("Étiquette exemplaire — largeur (mm)"),
                                       min_value=10, max_value=200, initial=50)
    item_height_mm = forms.IntegerField(label=_("Étiquette exemplaire — hauteur (mm)"),
                                        min_value=10, max_value=200, initial=25)
    item_title_max_chars = forms.IntegerField(label=_("Caractères max titre"),
                                              min_value=10, max_value=80, initial=30)
    card_per_a4 = forms.ChoiceField(
        label=_("Cartes par feuille A4"),
        choices=[("4", "4"), ("6", "6"), ("8", "8"), ("10", "10")],
        initial="8",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["item_width_mm"].initial = data.get("item_width_mm", 50)
            self.fields["item_height_mm"].initial = data.get("item_height_mm", 25)
            self.fields["item_title_max_chars"].initial = data.get("item_title_max_chars", 30)
            self.fields["card_per_a4"].initial = str(data.get("card_per_a4", 8))

    def save(self) -> None:
        Setting.set(self.KEY, {
            "item_width_mm": self.cleaned_data["item_width_mm"],
            "item_height_mm": self.cleaned_data["item_height_mm"],
            "item_title_max_chars": self.cleaned_data["item_title_max_chars"],
            "card_per_a4": int(self.cleaned_data["card_per_a4"]),
        }, "Format étiquettes / cartes")


class ZeroTierForm(forms.Form):
    KEY = "zerotier"

    network_id = forms.CharField(label=_("Identifiant réseau ZeroTier"),
                                 required=False, max_length=32)
    status = forms.ChoiceField(
        label=_("Statut"),
        choices=[("disabled", _("Désactivé")), ("pending", _("En attente")),
                 ("connected", _("Connecté"))],
        initial="disabled",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["network_id"].initial = data.get("network_id", "")
            self.fields["status"].initial = data.get("status", "disabled")

    def save(self) -> None:
        Setting.set(self.KEY, {
            "network_id": self.cleaned_data["network_id"],
            "status": self.cleaned_data["status"],
        }, "ZeroTier")
