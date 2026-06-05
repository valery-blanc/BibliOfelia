"""Admin minimal pour naviguer les modèles catalogue."""
from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import (
    Author,
    BibliographicRecord,
    Category,
    ExcelCatalogJob,
    Item,
    Location,
    Tag,
)


@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    search_fields = ("full_name",)
    list_display = ("full_name", "birth_year", "death_year")


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("code", "name", "parent", "default_loan_duration_days")
    list_filter = ("parent",)
    search_fields = ("code", "name")


@admin.register(Tag)
class TagAdmin(TranslationAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("code", "parent", "description")
    list_filter = ("parent",)
    search_fields = ("code",)


@admin.register(BibliographicRecord)
class BibliographicRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "publication_year", "language", "isbn_13", "document_type", "category")
    list_filter = ("document_type", "language", "metadata_source", "metadata_quality", "category")
    search_fields = ("title", "subtitle", "isbn_13", "isbn_10", "series_name")
    filter_horizontal = ("authors", "tags")
    autocomplete_fields = ("category",)


@admin.register(ExcelCatalogJob)
class ExcelCatalogJobAdmin(admin.ModelAdmin):
    list_display = ("pk", "mode", "state", "total", "processed", "created_by", "created_at")
    list_filter = ("mode", "state")
    readonly_fields = ("created_at", "finished_at")


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("internal_id", "ean13", "record", "status", "state", "location")
    list_filter = ("status", "state", "acquisition_source")
    search_fields = ("internal_id", "ean13", "record__title")
    autocomplete_fields = ("record", "location")
    readonly_fields = ("internal_id", "ean13", "created_at", "updated_at")
