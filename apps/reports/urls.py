from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_index, name="index"),
    path("overdue/", views.overdue_list, name="overdue"),
    path("reservations-pickup/", views.reservations_pickup_list, name="reservations_pickup"),
    path("inactive/", views.inactive_list, name="inactive"),
    path("loans.csv", views.loans_csv, name="loans_csv"),
    # FEAT-040 : nouveaux exports CSV
    path("catalog.csv", views.catalog_csv, name="catalog_csv"),
    path(
        "active-loans-reservations.csv",
        views.active_loans_reservations_csv,
        name="active_loans_reservations_csv",
    ),
    path("inactive-members.csv", views.inactive_members_csv, name="inactive_members_csv"),
    path("inactive-items.csv", views.inactive_items_csv, name="inactive_items_csv"),
    path("annual.pdf", views.annual_pdf, name="annual_pdf"),
]
