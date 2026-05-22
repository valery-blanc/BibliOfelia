"""Formulaires du catalogue. SPEC §6.1."""
from __future__ import annotations

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from .models import Author, BibliographicRecord, Item


class BibliographicRecordForm(forms.ModelForm):
    """Notice bibliographique. Les auteurs sont saisis en texte libre
    (point-virgule) plutôt qu'en multi-select, plus simple pour les
    bibliothécaires (SPEC §10.1)."""

    authors_text = forms.CharField(
        label=_("Auteur(s)"),
        required=False,
        help_text=_("Séparez plusieurs auteurs par un point-virgule."),
    )

    class Meta:
        model = BibliographicRecord
        fields = [
            "title", "subtitle", "publisher", "publication_year", "language",
            "isbn_13", "isbn_10", "summary", "cover_image", "category", "tags",
            "series_name", "series_volume", "document_type",
        ]
        widgets = {
            "summary": forms.Textarea(attrs={"rows": 3}),
            "tags": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["language"].widget = forms.Select(choices=settings.LANGUAGES)
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
            "location", "state", "acquisition_date", "acquisition_source",
            "donor", "notes",
        ]
        widgets = {
            "acquisition_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


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
