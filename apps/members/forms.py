"""Formulaires usagers. SPEC §6.2."""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from django import forms
from django.conf import settings
from django.core.validators import MaxLengthValidator
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import DocumentType
from apps.core.models import Setting

from .languages import spoken_language_choices
from .models import Member, MemberCategory, MemberFamilyMember


class LanguageChecklistWidget(forms.CheckboxSelectMultiple):
    """FEAT-065 : les 22 langues en cases à cocher, dans un encadré.

    Des cases plutôt qu'un multi-select : sur un téléphone, un `<select
    multiple>` se manipule mal, et une bibliothécaire doit pouvoir cocher deux
    langues sans savoir qu'il faut maintenir Ctrl.
    """

    def __init__(self, attrs=None):
        merged = {"class": "lang-grid"}
        merged.update(attrs or {})
        # FEAT-070 : `choices` est un callable — la liste vit en base et peut
        # être complétée pendant que le serveur tourne.
        super().__init__(attrs=merged, choices=spoken_language_choices)


class SpokenLanguagesField(forms.MultipleChoiceField):
    """Champ des langues parlées, stocké en JSON (liste de codes)."""

    def __init__(self, **kwargs):
        kwargs.setdefault("choices", spoken_language_choices)
        kwargs.setdefault("widget", LanguageChecklistWidget)
        kwargs.setdefault("required", False)
        kwargs.setdefault("label", _("Langues parlées"))
        super().__init__(**kwargs)


class MemberForm(forms.ModelForm):
    """Inscription / édition d'un usager.

    `card_number` et `expiration_date` sont calculés par `Member.save()` si
    laissés vides ; `expiration_date` reste ajustable (SPEC §6.2).
    """

    spoken_languages = SpokenLanguagesField()

    class Meta:
        model = Member
        fields = [
            "first_name", "last_name", "category", "preferred_language",
            "spoken_languages", "spoken_languages_other",
            "birth_date", "email", "contact_phone",
            # FEAT-083 : adresse découpée, dans l'ordre où on l'écrit sur une
            # enveloppe.
            "address_street", "address_extra", "address_postal_code",
            "address_city", "address_state", "address_country",
            "registration_date",
            "expiration_date", "photo", "notes",
        ]
        widgets = {
            # BUG-015 : format ISO obligatoire pour <input type="date">,
            # sinon Django rend au format locale (« 25 mai 2026 »), illisible
            # par le widget HTML5 → input vide en édition.
            "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "registration_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "expiration_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "notes": forms.Textarea(attrs={"rows": 3, "maxlength": 500}),
        }
        labels = {
            "spoken_languages_other": _("Autres langues"),
        }
        help_texts = {
            "spoken_languages_other": _(
                "Langues absentes de la liste, séparées par des virgules."
            ),
            "email": _("Reçoit les factures et les relances."),
            "address_state": _("Facultatif."),
            "notes": _("Commentaire libre, 500 caractères au maximum."),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["expiration_date"].required = False
        self.fields["spoken_languages_other"].required = False
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
        # FEAT-083 : `notes` est le « commentaire libre optionnel (500
        # caractères) » demandé par Val. La limite est portée par le
        # formulaire : la contrainte ne doit pas invalider les notes déjà
        # saisies avant cette version.
        self.fields["notes"].max_length = 500
        self.fields["notes"].validators.append(MaxLengthValidator(500))
        if not (self.instance and self.instance.pk) and not self.initial.get(
            "address_country"
        ):
            identity = Setting.get("library_identity", {}) or {}
            self.fields["address_country"].initial = identity.get("country", "")
        self.fields["preferred_language"].widget = forms.Select(
            choices=[("", _("Langue de la bibliothèque"))] + list(settings.LANGUAGES)
        )


class MemberFamilyMemberForm(forms.ModelForm):
    """FEAT-072 : une ligne « famille » du formulaire usager."""

    KIND_CHILD = "child"
    KIND_ADULT = "adult"

    kind = forms.ChoiceField(
        label=_("Adulte ou enfant"),
        required=False,
        choices=[(KIND_CHILD, _("Enfant")), (KIND_ADULT, _("Adulte"))],
        initial=KIND_CHILD,
    )
    languages = SpokenLanguagesField()

    class Meta:
        model = MemberFamilyMember
        fields = ["gender", "first_name", "birth_year", "languages", "languages_other"]
        labels = {
            "gender": _("Sexe"),
            "first_name": _("Prénom"),
            "birth_year": _("Année de naissance"),
            "languages_other": _("Autres langues"),
        }

    field_order = ["first_name", "gender", "kind", "birth_year"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("gender", "first_name", "birth_year", "languages_other"):
            self.fields[name].required = False
        current_year = date.today().year
        self.fields["birth_year"].widget.attrs.update(
            {"min": current_year - 120, "max": current_year, "placeholder": "2019"}
        )
        self.fields["birth_year"].help_text = _("Pour un enfant : l'âge est calculé.")
        if self.instance and self.instance.pk:
            self.fields["kind"].initial = (
                self.KIND_ADULT if self.instance.is_adult else self.KIND_CHILD
            )

    def clean(self):
        cleaned = super().clean()
        is_adult = cleaned.get("kind") == self.KIND_ADULT
        cleaned["is_adult"] = is_adult
        if is_adult:
            # Une année de naissance n'apporte rien pour un adulte : on l'efface
            # plutôt que de garder une donnée qui ne sera jamais affichée.
            cleaned["birth_year"] = None
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.is_adult = self.cleaned_data.get("is_adult", False)
        if instance.is_adult:
            instance.birth_year = None
        if commit:
            instance.save()
        return instance


class BaseMemberFamilyFormSet(forms.BaseInlineFormSet):
    """Ignore les lignes laissées vides plutôt que de bloquer l'enregistrement.

    Le formulaire propose toujours une ligne libre : sans ça, enregistrer une
    fiche sans toucher à la famille renverrait « ce champ est obligatoire ».
    """

    def clean(self):
        # L'ordre compte : `BaseModelFormSet.clean()` appelle `validate_unique()`,
        # qui lit `self.deleted_forms` — une `cached_property`. Marquer les
        # suppressions APRÈS le super() les rendrait invisibles à `save()`, et
        # la ligne vidée serait enregistrée telle quelle au lieu d'être
        # supprimée (constaté en test 2026-08-19).
        for form in self.forms:
            if getattr(form, "cleaned_data", None) is None:
                continue
            if form.cleaned_data.get("first_name"):
                continue
            # Ligne sans prénom : rien à enregistrer, on la marque supprimée.
            form.cleaned_data["DELETE"] = True
            form.errors.clear()
        super().clean()


MemberFamilyFormSet = forms.inlineformset_factory(
    Member,
    MemberFamilyMember,
    form=MemberFamilyMemberForm,
    formset=BaseMemberFamilyFormSet,
    extra=1,
    can_delete=True,
)


class MemberCategoryForm(forms.ModelForm):
    """FEAT-089 : création / édition hors /admin/.

    Les 4 noms sont des colonnes réelles (`name_fr`…), pas le proxy
    `name` de modeltranslation : un superadmin pose les traductions
    d'un coup, sans changer la langue de l'écran.
    """

    allowed_document_types = forms.MultipleChoiceField(
        choices=DocumentType.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "lang-grid"}),
        label=_("Types de documents autorisés"),
        help_text=_("Aucun coché = tous les types sont autorisés."),
    )

    class Meta:
        model = MemberCategory
        fields = [
            "code",
            "name_fr",
            "name_en",
            "name_es",
            "name_mg",
            "membership_fee",
            "card_validity_months",
            "max_concurrent_loans",
            "default_loan_duration_days",
        ]
        labels = {
            "code": _("Code"),
            "name_fr": _("Nom (français)"),
            "name_en": _("Nom (anglais)"),
            "name_es": _("Nom (espagnol)"),
            "name_mg": _("Nom (malgache)"),
            "membership_fee": _("Cotisation annuelle"),
            "card_validity_months": _("Validité de la carte (mois)"),
            "max_concurrent_loans": _("Prêts simultanés maximum"),
            "default_loan_duration_days": _("Durée de prêt (jours)"),
        }
        help_texts = {
            "code": _("Court, sans espace : ADULTE, ENFANT…"),
            "name_fr": _(
                "Nom affiché si les autres traductions manquent."
            ),
            "membership_fee": _(
                "0 = gratuit : aucune facture à l'inscription ni au "
                "renouvellement."
            ),
        }
        widgets = {
            "membership_fee": forms.NumberInput(
                attrs={"step": "0.01", "min": "0", "inputmode": "decimal"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("name_en", "name_es", "name_mg", "membership_fee"):
            self.fields[name].required = False
        self.fields["name_fr"].required = True
        if self.instance and self.instance.pk:
            self.fields["allowed_document_types"].initial = (
                self.instance.allowed_document_types or []
            )

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9_-]+", code):
            raise forms.ValidationError(
                _("Lettres, chiffres, tiret et underscore uniquement, sans espace.")
            )
        return code

    def clean_membership_fee(self):
        value = self.cleaned_data.get("membership_fee")
        if value in (None, ""):
            return Decimal("0")
        if value < 0:
            raise forms.ValidationError(_("Le montant ne peut pas être négatif."))
        return value

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.name = instance.name_fr
        instance.allowed_document_types = list(
            self.cleaned_data.get("allowed_document_types") or []
        )
        if commit:
            instance.save()
        return instance

