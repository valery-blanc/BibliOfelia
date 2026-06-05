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
    # FEAT-041 : affectation en masse catégorie / emplacement
    path(
        "bulk-assign-category/",
        views.record_bulk_assign_category_confirm,
        name="record_bulk_assign_category_confirm",
    ),
    path(
        "bulk-assign-category/apply/",
        views.record_bulk_assign_category,
        name="record_bulk_assign_category",
    ),
    path(
        "bulk-assign-location/",
        views.record_bulk_assign_location_confirm,
        name="record_bulk_assign_location_confirm",
    ),
    path(
        "bulk-assign-location/apply/",
        views.record_bulk_assign_location,
        name="record_bulk_assign_location",
    ),
    # FEAT-032 : gestion des emplacements
    path("locations/", views.location_list, name="location_list"),
    path("locations/new/", views.location_create, name="location_create"),
    path("locations/<int:pk>/edit/", views.location_edit, name="location_edit"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location_delete"),
    # FEAT-046 : catalogage en scan caméra continu
    path("scan/", views.scan_session_list, name="scan_session_list"),
    path("scan/new/", views.scan_session_create, name="scan_session_create"),
    path("scan/<int:pk>/", views.scan_session, name="scan_session"),
    path("scan/<int:pk>/add/", views.scan_add, name="scan_add"),
    path(
        "scan/<int:pk>/items/<int:item_pk>/delete/",
        views.scan_item_delete,
        name="scan_item_delete",
    ),
    path("scan/<int:pk>/commit/", views.scan_session_commit, name="scan_session_commit"),
    # FEAT-050 : catalogage Excel (vérification + import)
    path("excel-catalog/", views.excel_catalog_index, name="excel_catalog_index"),
    path(
        "excel-catalog/verify/",
        views.excel_catalog_verify_create,
        name="excel_catalog_verify",
    ),
    path(
        "excel-catalog/import/",
        views.excel_catalog_import_create,
        name="excel_catalog_import",
    ),
    path("excel-catalog/<int:pk>/", views.excel_catalog_detail, name="excel_catalog_detail"),
    path(
        "excel-catalog/<int:pk>/download/",
        views.excel_catalog_download,
        name="excel_catalog_download",
    ),
]
