from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.record_list, name="record_list"),
    path("new/", views.record_create, name="record_create"),
    path("isbn-lookup/", views.isbn_lookup, name="isbn_lookup"),
    path("<int:pk>/", views.record_detail, name="record_detail"),
    path("<int:pk>/edit/", views.record_edit, name="record_edit"),
    path("<int:pk>/delete/", views.record_delete, name="record_delete"),
    path("<int:record_pk>/items/new/", views.item_create, name="item_create"),
    path("items/<int:pk>/edit/", views.item_edit, name="item_edit"),
    path("items/<int:pk>/discard/", views.item_discard, name="item_discard"),
    path("items/<int:pk>/delete/", views.item_delete, name="item_delete"),
    path(
        "bulk-delete/",
        views.record_bulk_delete_confirm,
        name="record_bulk_delete_confirm",
    ),
    path(
        "bulk-delete/apply/",
        views.record_bulk_delete,
        name="record_bulk_delete",
    ),
    # FEAT-032 : gestion des emplacements
    path("locations/", views.location_list, name="location_list"),
    path("locations/new/", views.location_create, name="location_create"),
    path("locations/<int:pk>/edit/", views.location_edit, name="location_edit"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location_delete"),
]
