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


class MetadataSourcesForm(forms.Form):
    """FEAT-031 : configuration des sources externes d'enrichissement."""

    KEY = "metadata.sources"
    KEY_API_KEY = "metadata.google_books_api_key"

    # FEAT-059/060 : ordre = ordre de préférence de `lookup_isbn_multi`. Toutes
    # les sources sont actives par défaut — aucune n'exige de clé (la clé Google
    # Books ne fait que relever le quota) et une source muette ne coûte qu'un
    # appel HTTP parallèle.
    SOURCE_ORDER = ["openlibrary", "google_books", "bnf", "bne", "swisscovery", "k10plus"]

    google_books_api_key = forms.CharField(
        label=_("Clé API Google Books"),
        required=False,
        help_text=_(
            "Facultative mais recommandée : sans clé, Google Books partage un "
            "quota par adresse IP et répond « quota atteint ». Gratuite via "
            "Google Cloud Console."
        ),
    )
    openlibrary_enabled = forms.BooleanField(label=_("OpenLibrary"), required=False, initial=True)
    google_books_enabled = forms.BooleanField(label=_("Google Books"), required=False, initial=True)
    bnf_enabled = forms.BooleanField(label=_("BnF (livres FR)"), required=False, initial=True)
    bne_enabled = forms.BooleanField(label=_("BNE (livres ES)"), required=False, initial=True)
    swisscovery_enabled = forms.BooleanField(
        label=_("Swisscovery (livres CH)"), required=False, initial=True
    )
    k10plus_enabled = forms.BooleanField(
        label=_("K10plus (livres DE)"), required=False, initial=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY, {})
            self.fields["google_books_api_key"].initial = Setting.get(self.KEY_API_KEY, "")
            for source in self.SOURCE_ORDER:
                self.fields[f"{source}_enabled"].initial = data.get(source, True)

    def save(self) -> None:
        data = self.cleaned_data
        Setting.set(self.KEY_API_KEY, data.get("google_books_api_key", "").strip())
        Setting.set(
            self.KEY,
            {s: bool(data[f"{s}_enabled"]) for s in self.SOURCE_ORDER},
        )

    @staticmethod
    def active_sources() -> list[str]:
        """Sources activées dans Settings (toutes par défaut, cf. SOURCE_ORDER).

        FEAT-059 : Google Books était exclu par défaut (héritage de l'époque où
        on croyait la clé d'API obligatoire) — il n'apparaissait donc pas dans
        les cases à cocher de l'enrichissement sur une instance neuve.
        """
        data = Setting.get(MetadataSourcesForm.KEY, {}) or {}
        return [s for s in MetadataSourcesForm.SOURCE_ORDER if data.get(s, True)]


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


class MemberCardFormatForm(forms.Form):
    """FEAT-038 : paramètres impression des cartes membres."""

    KEY = "card_format"

    per_a4 = forms.ChoiceField(
        label=_("Cartes par feuille A4"),
        choices=[("4", "4"), ("6", "6"), ("8", "8"), ("10", "10")],
        initial="8",
    )
    show_logo = forms.BooleanField(
        label=_("Logo OFELIA en fond"),
        required=False,
        initial=True,
        help_text=_("Affiche le logo grandes lettres OFELIA centré sur chaque carte."),
    )
    show_photo = forms.BooleanField(
        label=_("Photo du membre"),
        required=False,
        initial=True,
        help_text=_("Affiche la photo en haut à gauche quand le membre en a une."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["per_a4"].initial = str(data.get("per_a4", 8))
            self.fields["show_logo"].initial = bool(data.get("show_logo", True))
            self.fields["show_photo"].initial = bool(data.get("show_photo", True))

    def save(self) -> None:
        Setting.set(self.KEY, {
            "per_a4": int(self.cleaned_data["per_a4"]),
            "show_logo": bool(self.cleaned_data["show_logo"]),
            "show_photo": bool(self.cleaned_data["show_photo"]),
        }, "Format cartes membres")


class ItemLabelFormatForm(forms.Form):
    """FEAT-039 : paramètres impression des étiquettes codes Ofelia."""

    KEY = "item_label_format"

    width_mm = forms.IntegerField(
        label=_("Largeur (mm)"),
        min_value=20, max_value=200, initial=70,
    )
    height_mm = forms.IntegerField(
        label=_("Hauteur (mm)"),
        min_value=20, max_value=200, initial=42,
    )
    title_max_chars = forms.IntegerField(
        label=_("Caractères max titre"),
        min_value=10, max_value=120, initial=50,
        help_text=_("Cumulé sur les lignes du titre."),
    )
    title_lines = forms.IntegerField(
        label=_("Lignes de titre"),
        min_value=1, max_value=3, initial=2,
    )
    author_lines = forms.IntegerField(
        label=_("Lignes d'auteurs"),
        min_value=1, max_value=3, initial=2,
    )
    show_logo = forms.BooleanField(
        label=_("Logo Ofelia"),
        required=False, initial=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["width_mm"].initial = data.get("width_mm", 70)
            self.fields["height_mm"].initial = data.get("height_mm", 42)
            self.fields["title_max_chars"].initial = data.get("title_max_chars", 50)
            self.fields["title_lines"].initial = data.get("title_lines", 2)
            self.fields["author_lines"].initial = data.get("author_lines", 2)
            self.fields["show_logo"].initial = bool(data.get("show_logo", True))

    def save(self) -> None:
        Setting.set(self.KEY, {
            "width_mm": self.cleaned_data["width_mm"],
            "height_mm": self.cleaned_data["height_mm"],
            "title_max_chars": self.cleaned_data["title_max_chars"],
            "title_lines": self.cleaned_data["title_lines"],
            "author_lines": self.cleaned_data["author_lines"],
            "show_logo": bool(self.cleaned_data["show_logo"]),
        }, "Format étiquettes codes Ofelia")


class RollPrinterFormatForm(forms.Form):
    """FEAT-062 : paramètres de l'imprimante à ruban continu (Brother QL-810W)."""

    KEY = "roll_printer_format"

    enabled = forms.BooleanField(
        label=_("Imprimante à ruban disponible"),
        required=False, initial=True,
        help_text=_("Affiche le bouton « Ruban » sur les écrans d'impression."),
    )
    tape_width_mm = forms.ChoiceField(
        label=_("Largeur du ruban (mm)"),
        choices=[("29", "29"), ("38", "38"), ("50", "50"), ("62", "62")],
        initial="62",
    )
    label_length_mm = forms.IntegerField(
        label=_("Longueur d'une étiquette (mm)"),
        min_value=15, max_value=200, initial=35,
        help_text=_("Doit correspondre à la longueur de coupe réglée dans le pilote Brother."),
    )
    card_length_mm = forms.IntegerField(
        label=_("Longueur d'une carte membre (mm)"),
        min_value=40, max_value=200, initial=89,
        help_text=_("89 mm : juste sous le format continu natif du pilote Brother (62 × 89,9 mm)."),
    )
    two_color = forms.BooleanField(
        label=_("Ruban bicolore noir/rouge"),
        required=False, initial=True,
        help_text=_("Rouge sur les cartes membres. Les étiquettes restent monochromes."),
    )
    show_logo = forms.BooleanField(
        label=_("Logo Ofelia sur les étiquettes"),
        required=False, initial=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            data = _initial_dict(self.KEY)
            self.fields["enabled"].initial = bool(data.get("enabled", True))
            self.fields["tape_width_mm"].initial = str(data.get("tape_width_mm", 62))
            self.fields["label_length_mm"].initial = data.get("label_length_mm", 35)
            self.fields["card_length_mm"].initial = data.get("card_length_mm", 89)
            self.fields["two_color"].initial = bool(data.get("two_color", True))
            self.fields["show_logo"].initial = bool(data.get("show_logo", True))

    def save(self) -> None:
        Setting.set(self.KEY, {
            "enabled": bool(self.cleaned_data["enabled"]),
            "tape_width_mm": int(self.cleaned_data["tape_width_mm"]),
            "label_length_mm": self.cleaned_data["label_length_mm"],
            "card_length_mm": self.cleaned_data["card_length_mm"],
            "two_color": bool(self.cleaned_data["two_color"]),
            "show_logo": bool(self.cleaned_data["show_logo"]),
        }, "Imprimante à ruban continu (FEAT-062)")


class LoanReservationDefaultsForm(forms.Form):
    """FEAT-034 + FEAT-035 : durées par défaut des prêts et des réservations."""

    default_loan_days = forms.IntegerField(
        label=_("Durée par défaut d'un prêt (jours)"),
        min_value=1, max_value=365,
        help_text=_("Utilisée si ni la catégorie de document ni la catégorie de membre n'en définit une. Défaut : 21 jours (3 semaines)."),
    )
    reservation_expiry_days = forms.IntegerField(
        label=_("Validité d'une réservation en attente (jours)"),
        min_value=1, max_value=365,
        help_text=_("Délai au-delà duquel une réservation pour laquelle aucun exemplaire ne s'est libéré expire automatiquement."),
    )
    pickup_hold_days = forms.IntegerField(
        label=_("Durée de mise de côté à retirer (jours)"),
        min_value=1, max_value=60,
        help_text=_("Une fois un exemplaire mis de côté pour un membre, il a ce délai pour venir le retirer avant que la réservation ne bascule au membre suivant."),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.fields["default_loan_days"].initial = int(
                Setting.get("default_loan_days", 21) or 21
            )
            self.fields["reservation_expiry_days"].initial = int(
                Setting.get("reservation_expiry_days", 7) or 7
            )
            self.fields["pickup_hold_days"].initial = int(
                Setting.get("pickup_hold_days", 5) or 5
            )

    def save(self) -> None:
        Setting.set(
            "default_loan_days", int(self.cleaned_data["default_loan_days"]),
            "Durée par défaut d'un prêt (fallback global)",
        )
        Setting.set(
            "reservation_expiry_days", int(self.cleaned_data["reservation_expiry_days"]),
            "Délai d'expiration d'une réservation pending",
        )
        Setting.set(
            "pickup_hold_days", int(self.cleaned_data["pickup_hold_days"]),
            "Délai de garde après mise à dispo",
        )


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
