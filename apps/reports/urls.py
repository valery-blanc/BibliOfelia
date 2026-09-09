from django.urls import path, re_path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.reports_index, name="index"),
    # Exports CSV de données brutes (FEAT-040) — déclarés avant le motif
    # générique, sinon `catalog.csv` serait pris pour un slug de rapport.
    path("loans.csv", views.loans_csv, name="loans_csv"),
    path("catalog.csv", views.catalog_csv, name="catalog_csv"),
    path(
        "active-loans-reservations.csv",
        views.active_loans_reservations_csv,
        name="active_loans_reservations_csv",
    ),
    path("inactive-members.csv", views.inactive_members_csv, name="inactive_members_csv"),
    path("inactive-items.csv", views.inactive_items_csv, name="inactive_items_csv"),
    # Anciennes adresses, conservées : le guide utilisateur et les favoris des
    # bibliothécaires y renvoient (FEAT-093). `overdue/` et `inactive/` n'ont
    # pas besoin de redirection — leur slug est resté le même, elles tombent
    # sur le motif générique. En redéclarer une ici la ferait rediriger vers
    # elle-même, en boucle.
    path("reservations-pickup/", views.reservations_pickup_list, name="reservations_pickup"),
    path("annual.pdf", views.annual_pdf, name="annual_pdf"),
    # Un écran, ses deux exports (FEAT-093).
    re_path(r"^(?P<slug>[a-z-]+)\.pdf$", views.report_pdf, name="pdf"),
    re_path(r"^(?P<slug>[a-z-]+)\.xlsx$", views.report_xlsx, name="xlsx"),
    path("<slug:slug>/", views.report_view, name="view"),
]
