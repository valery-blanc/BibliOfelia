"""Formulaires du catalogue. SPEC §6.1."""
from __future__ import annotations

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.issn import normalize_issn, validate_issn

from .languages import language_choices

from .lookup import (
    EXTERNAL_CODE_MAX_LENGTH,
    is_valid_external_code,
    normalize_external_code,
)
from .models import (
    Author,
    BibliographicRecord,
    Category,
    Item,
    Language,
    Location,
    Provenance,
    ScanSession,
)


class BibliographicRecordForm(forms.ModelForm):
    """Notice bibliographique. Les auteurs sont saisis en texte libre
    (point-virgule) plutôt qu'en multi-select, plus simple pour les
    bibliothécaires (SPEC §10.1)."""

    authors_text = forms.CharField(
        label=_("Auteur(s)"),
        required=False,
        help_text=_("Séparez plusieurs auteurs par un point-virgule."),
    )
    # FEAT-052 : champ explicite (max_length 9) pour accepter l'ISSN saisi avec
    # tiret (« 1234-5679 ») ; `clean_issn` le normalise ensuite en 8 caractères.
    # Sans ça, la validation `max_length=8` héritée du modèle rejette le tiret.
    issn = forms.CharField(
        label=_("ISSN"),
        required=False,
        max_length=9,
        help_text=_("Pour les revues/magazines (code-barres 977). Ex. 1234-5679."),
    )

    class Meta:
        model = BibliographicRecord
        fields = [
            "title", "subtitle", "publisher", "publication_year", "language",
            "isbn_13", "isbn_10", "issn", "summary", "cover_image", "category", "tags",
            "series_name", "series_volume", "document_type",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.CheckboxSelectMultiple,
        }
        labels = {
            # `verbose_name` est bien posé sur le modèle, mais Django dérive le
            # label d'un M2M de son `related_name` : on le fixe ici.
            "tags": _("Tags"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # FEAT-070 : la langue du document vient de la table `Language`
        # (extensible), pas des 4 langues de l'interface.
        self.fields["language"].widget = forms.Select(choices=language_choices())
        if self.instance and self.instance.pk and "authors_text" not in self.data:
            self.fields["authors_text"].initial = "; ".join(
                a.full_name for a in self.instance.authors.all()
            )

    def _clean_isbn(self, field: str, length: int):
        raw = (self.cleaned_data.get(field) or "").replace("-", "").replace(" ", "")
        if not raw:
            return None  # NULL en base : évite la collision sur la chaîne vide
        body_ok = raw[:-1].isdigit() and (raw[-1].isdigit() or raw[-1] in "Xx")
        if len(raw) != length or not body_ok:
            raise forms.ValidationError(
                _("L'ISBN doit comporter %(n)s caractères.") % {"n": length}
            )
        return raw.upper()

    def clean_isbn_13(self):
        return self._clean_isbn("isbn_13", 13)

    def clean_isbn_10(self):
        return self._clean_isbn("isbn_10", 10)

    def clean_issn(self):
        """FEAT-052 : ISSN normalisé (8 car., clé validée). Vide → NULL."""
        raw = normalize_issn(self.cleaned_data.get("issn") or "")
        if not raw:
            return None  # NULL en base : évite la collision sur la chaîne vide
        if not validate_issn(raw):
            raise forms.ValidationError(
                _("ISSN invalide (8 caractères, ex. 1234-5679).")
            )
        return raw

    def save(self, commit=True):
        # commit=True : ModelForm.save sauve déjà l'instance + les M2M déclarés
        # (tags). commit=False : l'appelant doit invoquer save_m2m() puis
        # sync_authors() lui-même (cf. catalog.views.record_create).
        record = super().save(commit=commit)
        if commit:
            self.sync_authors(record)
        return record

    def sync_authors(self, record: BibliographicRecord) -> None:
        names = [
            n.strip()
            for n in (self.cleaned_data.get("authors_text") or "").split(";")
            if n.strip()
        ]
        authors = [Author.objects.get_or_create(full_name=n)[0] for n in names]
        record.authors.set(authors)


class ItemForm(forms.ModelForm):
    """Édition d'un exemplaire existant."""

    class Meta:
        model = Item
        fields = [
            "external_code", "location", "provenance", "state", "acquisition_date",
            "acquisition_source", "donor", "notes",
        ]
        widgets = {
            "acquisition_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "external_code": _("Code Ofelia externe"),
            "location": _("Emplacement"),
            "provenance": _("Provenance"),
            "state": _("État"),
            "acquisition_date": _("Date d'acquisition"),
            "acquisition_source": _("Source d'acquisition"),
            "donor": _("Donateur"),
            "notes": _("Notes"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provenance"].queryset = Provenance.objects.all().order_by("code")
        if not self.fields["provenance"].queryset.exists():
            # BUG-027 : un menu vide sans explication laisse croire que le champ
            # ne marche pas. On dit où créer la première provenance.
            self.fields["provenance"].help_text = _(
                "Aucune provenance n'existe encore : créez-en une depuis "
                "Avancé → Provenances."
            )

    def clean_external_code(self):
        """FEAT-063 : normalise, valide la forme, refuse un code déjà pris.

        L'unicité est aussi garantie en base (contrainte partielle) ; on la
        vérifie ici pour rendre un message lisible plutôt qu'une IntegrityError.
        """
        code = normalize_external_code(self.cleaned_data.get("external_code") or "")
        if not code:
            return ""
        if not is_valid_external_code(code):
            raise forms.ValidationError(
                _("Le code externe doit être alphanumérique et faire %(n)s caractères au plus.")
                % {"n": EXTERNAL_CODE_MAX_LENGTH}
            )
        taken = Item.objects.filter(external_code=code)
        if self.instance and self.instance.pk:
            taken = taken.exclude(pk=self.instance.pk)
        other = taken.first()
        if other is not None:
            raise forms.ValidationError(
                _("Ce code externe est déjà porté par l'exemplaire %(code)s (%(title)s).")
                % {"code": other.ean13, "title": other.record.title}
            )
        return code


class ItemBulkCreateForm(ItemForm):
    """Création groupée d'exemplaires depuis une notice (SPEC §6.1)."""

    copies = forms.IntegerField(
        label=_("Nombre d'exemplaires"),
        min_value=1,
        max_value=20,
        initial=1,
        help_text=_("Jusqu'à 20 exemplaires identiques d'un coup."),
    )

    field_order = ["copies"]

    def clean(self):
        """Un code externe désigne un exemplaire : pas de duplication possible."""
        cleaned = super().clean()
        if cleaned.get("external_code") and (cleaned.get("copies") or 1) > 1:
            self.add_error(
                "external_code",
                _("Un code externe ne peut être attribué qu'à un seul exemplaire : "
                  "créez-les sans code, puis saisissez le code sur l'exemplaire concerné."),
            )
        return cleaned


class LocationForm(forms.ModelForm):
    """FEAT-032 : création/édition d'un emplacement par un bibliothécaire."""

    class Meta:
        model = Location
        fields = ["code", "description", "parent"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "code": _("Court, sans espace : A1, JEU-BD, RES…"),
            "parent": _("Sous-emplacement de… (optionnel)."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].required = False
        self.fields["description"].required = False
        qs = Location.objects.all()
        if self.instance and self.instance.pk:
            # éviter de proposer self comme parent
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = qs.order_by("code")

    def clean(self):
        cleaned = super().clean()
        code = cleaned.get("code")
        parent = cleaned.get("parent")
        if code:
            qs = Location.objects.filter(code=code, parent=parent)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "code",
                    _("Un emplacement avec ce code existe déjà pour ce parent."),
                )
        if parent and self.instance.pk and parent.pk == self.instance.pk:
            self.add_error("parent", _("Un emplacement ne peut pas être son propre parent."))
        return cleaned


class CategoryForm(forms.ModelForm):
    """FEAT-067 : création/édition d'une catégorie par un bibliothécaire.

    Jusqu'ici les catégories n'existaient que dans le seed et dans /admin/ —
    hors de portée des bibliothécaires, donc impossible d'y saisir la cote.
    """

    class Meta:
        model = Category
        fields = ["code", "name", "abbreviation", "parent", "default_loan_duration_days"]
        labels = {
            "code": _("Code"),
            "name": _("Nom"),
            "abbreviation": _("Abréviation"),
            "parent": _("Catégorie parente"),
            "default_loan_duration_days": _("Durée de prêt (jours)"),
        }
        help_texts = {
            "code": _("Court, sans espace : ENF-ALB, ADU-ROM…"),
            "abbreviation": _(
                "Cote imprimée sur l'étiquette de tranche. Ex. « RO FI ADO » pour "
                "« Romans fiction pour adolescents »."
            ),
            "parent": _("Sous-catégorie de… (optionnel)."),
            "default_loan_duration_days": _("Vide = durée par défaut de la bibliothèque."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("abbreviation", "parent", "default_loan_duration_days"):
            self.fields[name].required = False
        qs = Category.objects.all()
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields["parent"].queryset = qs.order_by("code")


class LanguageForm(forms.ModelForm):
    """FEAT-070 : ajout/édition d'une langue par un bibliothécaire."""

    class Meta:
        model = Language
        fields = ["code", "name"]
        labels = {"code": _("Code"), "name": _("Nom")}
        help_texts = {
            "code": _(
                "Abréviation internationale principale, sans variante régionale : "
                "fr, en, pt, de… (« fr » couvre le français de France, du Canada "
                "et de Suisse)."
            ),
            "name": _("Nom de la langue dans la langue de saisie courante."),
        }

    def clean_code(self):
        return (self.cleaned_data.get("code") or "").strip().lower()


class ProvenanceForm(forms.ModelForm):
    """FEAT-064 : création/édition d'une provenance par un bibliothécaire."""

    class Meta:
        model = Provenance
        fields = ["code", "label", "notes"]
        widgets = {
            "notes": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "code": _("Code"),
            "label": _("Nom complet"),
            "notes": _("Notes"),
        }
        help_texts = {
            "code": _("Court, sans espace : OFELIA, BM-GE, DON-DUPONT…"),
            "label": _("Nom lisible affiché dans les listes. Ex. « Prêt Bibliothèque de Genève »."),
            "notes": _("Contact, date de restitution prévue, conditions du dépôt…"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["label"].required = False
        self.fields["notes"].required = False


class ScanCatalogSessionForm(forms.ModelForm):
    """FEAT-046 : démarrage d'un lot de catalogage caméra (défauts du lot)."""

    class Meta:
        model = ScanSession
        fields = ["label", "default_category", "default_location", "default_provenance"]
        labels = {
            "label": _("Nom du lot (optionnel)"),
            "default_category": _("Catégorie par défaut"),
            "default_location": _("Emplacement par défaut"),
            "default_provenance": _("Provenance par défaut"),
        }
        help_texts = {
            "default_category": _("Appliquée aux nouvelles notices ; modifiable ligne par ligne."),
            "default_location": _("Appliqué aux nouveaux exemplaires ; modifiable ligne par ligne."),
            "default_provenance": _(
                "Appliquée à tous les exemplaires du lot. Ex. des livres prêtés par "
                "une autre bibliothèque, à retrouver le jour du retour."
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["label"].required = False
        self.fields["default_category"].required = False
        self.fields["default_location"].required = False
        self.fields["default_provenance"].required = False
        self.fields["default_category"].queryset = Category.objects.all().order_by("code")
        self.fields["default_location"].queryset = Location.objects.all().order_by("code")
        self.fields["default_provenance"].queryset = Provenance.objects.all().order_by("code")
