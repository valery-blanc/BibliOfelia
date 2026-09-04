from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.cash_index, name="cash_index"),
    path("cash/new/", views.cash_movement_create, name="cash_movement_create"),
    path("currencies/", views.currency_search, name="currency_search"),
    path("outbox/", views.outbox_list, name="outbox_list"),
    path("outbox/flush/", views.outbox_flush, name="outbox_flush"),
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/pay/", views.invoice_pay, name="invoice_pay"),
    path("invoices/<int:pk>/cancel/", views.invoice_cancel, name="invoice_cancel"),
    path("invoices/<int:pk>/pdf/", views.invoice_pdf, name="invoice_pdf"),
    path("invoices/<int:pk>/email/", views.invoice_email, name="invoice_email"),
    path("members/<int:member_pk>/account/", views.member_account_view, name="member_account"),
    path("members/<int:member_pk>/invoice/new/", views.invoice_create, name="invoice_create"),
    path("members/<int:member_pk>/fee/<str:kind>/", views.fee_create, name="fee_create"),
    path("tariffs/", views.tariff_list, name="tariff_list"),
    path("tariffs/<int:pk>/edit/", views.tariff_edit, name="tariff_edit"),
    path("tariffs/<int:pk>/delete/", views.tariff_delete, name="tariff_delete"),
    path(
        "tariffs/categories/new/",
        views.member_category_create,
        name="member_category_create",
    ),
    path(
        "tariffs/categories/<int:pk>/edit/",
        views.member_category_edit,
        name="member_category_edit",
    ),
    path(
        "tariffs/categories/<int:pk>/delete/",
        views.member_category_delete,
        name="member_category_delete",
    ),
]
