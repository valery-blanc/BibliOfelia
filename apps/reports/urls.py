from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_index, name="index"),
    path("overdue/", views.overdue_list, name="overdue"),
    path("reservations-pickup/", views.reservations_pickup_list, name="reservations_pickup"),
    path("inactive/", views.inactive_list, name="inactive"),
    path("loans.csv", views.loans_csv, name="loans_csv"),
    path("annual.pdf", views.annual_pdf, name="annual_pdf"),
]
