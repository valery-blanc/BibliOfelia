from django.contrib import admin

from .models import (
    CashMovement,
    Invoice,
    InvoiceLine,
    OutboundEmail,
    Payment,
    Tariff,
)


class InvoiceLineInline(admin.TabularInline):
    model = InvoiceLine
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "member", "issue_date", "due_date", "status",
                    "total_amount", "amount_paid")
    list_filter = ("status", "issue_date")
    search_fields = ("number", "member__last_name", "member__card_number")
    inlines = [InvoiceLineInline]


admin.site.register(Tariff)
admin.site.register(Payment)
admin.site.register(CashMovement)
admin.site.register(OutboundEmail)
