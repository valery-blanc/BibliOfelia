"""Enregistrement modeltranslation pour les usagers. SPEC §6.9.

Champs traduits :
- MemberCategory.name → name_fr, name_en, name_es, name_mg
"""
from modeltranslation.translator import TranslationOptions, register

from .models import MemberCategory


@register(MemberCategory)
class MemberCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)
