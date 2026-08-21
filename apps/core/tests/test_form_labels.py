"""BUG-028 — aucun libellé de formulaire ne doit rester en anglais.

Quand un `ModelForm` ne fournit ni `labels` dans son `Meta`, ni `verbose_name`
sur le champ du modèle, Django **fabrique** le libellé à partir du nom Python du
champ : `publication_year` → « Publication year ». Cette chaîne n'existe nulle
part dans le code, elle n'est donc jamais extraite par `makemessages` et
`i18n_check.py` ne peut pas la voir — la page sort en anglais sans que rien ne
proteste (constaté sur la fiche notice, 2026-08-21).

Ce test est le pendant du gate `.po` : `i18n_check.py` vérifie que les chaînes
extraites sont **traduites**, celui-ci vérifie qu'elles sont bien **extraites**.
"""
from __future__ import annotations

import pytest
from django import forms as djforms
from django.utils import translation
from django.utils.functional import Promise

pytestmark = pytest.mark.django_db


def _project_forms():
    """Tous les formulaires déclarés dans les apps du projet."""
    import importlib
    import pkgutil

    import apps

    found = []
    for module_info in pkgutil.walk_packages(apps.__path__, prefix="apps."):
        if not module_info.name.endswith(".forms"):
            continue
        module = importlib.import_module(module_info.name)
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, djforms.BaseForm)
                and obj.__module__ == module.__name__
            ):
                found.append((module.__name__, name, obj))
    return found


def test_project_has_forms_to_audit():
    """Garde-fou : si la découverte casse, le test principal passerait à vide."""
    assert len(_project_forms()) >= 10


def test_no_form_label_is_left_in_english():
    """Chaque libellé doit être un objet de traduction, pas une chaîne dérivée.

    Un libellé posé par `verbose_name=_()` ou par `labels` reste **lazy**
    jusqu'au rendu ; un libellé fabriqué par Django à partir du nom du champ est
    une `str` ordinaire. Tester la nature de l'objet plutôt que comparer des
    mots évite de maintenir une liste de mots identiques dans les deux langues
    (« Code », « Notes », « Date », « Tags »…) — et surtout de laisser passer un
    vrai oubli qui se trouverait ressembler à du français.
    """
    offenders = []
    for module_name, form_name, form_class in _project_forms():
        try:
            form = form_class()
        except Exception:
            # Formulaire qui exige des arguments : hors de portée de cet audit.
            continue
        for field_name, field in form.fields.items():
            if field.label is None or isinstance(field.label, Promise):
                continue
            offenders.append(
                f"{module_name}.{form_name}.{field_name} → {str(field.label)!r}"
            )

    assert not offenders, (
        "Libellés non traduits (posez un `verbose_name=_()` sur le champ du "
        "modèle, ou un `labels` dans le Meta du formulaire) :\n  "
        + "\n  ".join(offenders)
    )


def test_the_record_form_is_french():
    """Le cas signalé par Val : /fr/catalog/<pk>/edit/."""
    from apps.catalog.forms import BibliographicRecordForm

    with translation.override("fr"):
        labels = {n: str(f.label) for n, f in BibliographicRecordForm().fields.items()}
    assert labels["title"] == "Titre"
    assert labels["language"] == "Langue"
    assert labels["publisher"] == "Éditeur"
    assert labels["summary"] == "Résumé"
    assert labels["category"] == "Catégorie"
    assert labels["publication_year"] == "Année de publication"


def test_the_member_form_is_french():
    from apps.members.forms import MemberForm

    with translation.override("fr"):
        labels = {n: str(f.label) for n, f in MemberForm().fields.items()}
    assert labels["first_name"] == "Prénom"
    assert labels["last_name"] == "Nom"
    assert labels["birth_date"] == "Date de naissance"
    assert labels["contact_phone"] == "Téléphone"


def test_labels_are_translatable_objects():
    """Les libellés passent par gettext, donc `makemessages` les voit.

    On vérifie le **mécanisme**, pas le résultat traduit : ce dernier dépend des
    `.mo` compilés, absents d'un poste sans gettext. Que les traductions
    existent est l'affaire de `scripts/i18n_check.py`.
    """
    from apps.catalog.models import BibliographicRecord

    for name in ("title", "language", "publisher", "summary"):
        field = BibliographicRecord._meta.get_field(name)
        assert isinstance(field.verbose_name, Promise), (
            f"{name} : verbose_name doit être un `gettext_lazy`, sinon la chaîne "
            "n'est pas extraite dans les .po"
        )
