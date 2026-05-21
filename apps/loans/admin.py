"""Admin minimal pour prêts et réservations."""
from django.contrib import admin

from .models import InHouseConsultation, Loan, Reservation


@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ("id", "item", "member", "loan_date", "due_date", "return_date", "status")
    list_filter = ("status",)
    search_fields = ("item__internal_id", "item__ean13", "member__card_number", "member__last_name")
    autocomplete_fields = ("item", "member", "librarian")


@admin.register(InHouseConsultation)
class InHouseConsultationAdmin(admin.ModelAdmin):
    list_display = ("date", "item", "member", "count")
    list_filter = ("date",)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("id", "record", "member", "status", "created_at", "expires_at")
    list_filter = ("status",)
    search_fields = ("record__title", "member__last_name", "member__card_number")
    autocomplete_fields = ("record", "member", "fulfilled_by_item", "fulfilled_by_loan")
