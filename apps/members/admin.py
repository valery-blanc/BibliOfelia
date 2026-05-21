"""Admin minimal pour usagers."""
from django.contrib import admin

from .models import Member, MemberCategory


@admin.register(MemberCategory)
class MemberCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "max_concurrent_loans",
        "default_loan_duration_days",
        "card_validity_months",
    )
    search_fields = ("code", "name")


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        "card_number",
        "last_name",
        "first_name",
        "category",
        "status",
        "expiration_date",
    )
    list_filter = ("status", "category")
    search_fields = ("card_number", "last_name", "first_name", "contact_phone")
    autocomplete_fields = ("category", "parent_account")
    readonly_fields = ("card_number",)
