"""Enregistrement modeltranslation pour le catalogue. SPEC §6.9.

Champs traduits :
- Category.name  → name_fr, name_en, name_es, name_mg
- Tag.name       → idem
"""
from modeltranslation.translator import TranslationOptions, register

from .models import Category, Tag


@register(Category)
class CategoryTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Tag)
class TagTranslationOptions(TranslationOptions):
    fields = ("name",)
