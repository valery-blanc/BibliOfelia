"""Admin Django pour les paramètres globaux (réservé superadmin / support).

Expose `Setting` afin de pouvoir renseigner des réglages techniques non
exposés dans l'UI Paramètres — notamment la clé API Google Books
(`metadata.google_books_api_key`) utilisée par le catalogage Excel (FEAT-050)
et l'enrichissement (FEAT-031). La valeur étant un JSONField, une chaîne se
saisit entre guillemets : `"AIzaSy…"`.
"""
from django.contrib import admin

from .models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_at")
    search_fields = ("key", "description")
    readonly_fields = ("updated_at",)
    fields = ("key", "value", "description", "updated_at")
