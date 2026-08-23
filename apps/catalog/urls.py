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
    # FEAT-069 : affectation en masse depuis la page catalogue (sans page intermédiaire)
    path("bulk-assign/", views.record_bulk_assign, name="record_bulk_assign"),
    # FEAT-032 : gestion des emplacements
    path("locations/", views.location_list, name="location_list"),
    path("locations/new/", views.location_create, name="location_create"),
    path("locations/<int:pk>/edit/", views.location_edit, name="location_edit"),
    path("locations/<int:pk>/delete/", views.location_delete, name="location_delete"),
    # FEAT-070 : gestion des langues
    path("languages/", views.language_list, name="language_list"),
    path("languages/new/", views.language_create, name="language_create"),
    path("languages/<int:pk>/edit/", views.language_edit, name="language_edit"),
    path("languages/<int:pk>/delete/", views.language_delete, name="language_delete"),
    # FEAT-067 : gestion des catégories
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    # FEAT-064 : gestion des provenances
    path("provenances/", views.provenance_list, name="provenance_list"),
    path("provenances/new/", views.provenance_create, name="provenance_create"),
    path("provenances/<int:pk>/edit/", views.provenance_edit, name="provenance_edit"),
    path("provenances/<int:pk>/delete/", views.provenance_delete, name="provenance_delete"),
    # FEAT-064 / FEAT-069 : actions de masse sur les exemplaires
    path("items/bulk-assign/", views.item_bulk_assign, name="item_bulk_assign"),
    path(
        "items/bulk-delete/",
        views.item_bulk_delete_confirm,
        name="item_bulk_delete_confirm",
    ),
    path(
        "items/bulk-delete/apply/",
        views.item_bulk_delete,
        name="item_bulk_delete",
    ),
    # FEAT-046 : catalogage en scan caméra continu
    path("scan/", views.scan_session_list, name="scan_session_list"),
    path("scan/new/", views.scan_session_create, name="scan_session_create"),
    # FEAT-054 : catalogage à la douchette USB (keyboard-wedge)
    path("scan/new-douchette/", views.scan_douchette_create, name="scan_douchette_create"),
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
    # FEAT-078 : export Excel de tout le catalogue (téléchargement direct)
    path(
        "excel-catalog/export/",
        views.excel_catalog_export,
        name="excel_catalog_export",
    ),
    # FEAT-079 : mise à jour d'exemplaires existants à partir d'un .xlsx
    path(
        "excel-catalog/update/",
        views.excel_catalog_update_create,
        name="excel_catalog_update",
    ),
    path("excel-catalog/<int:pk>/", views.excel_catalog_detail, name="excel_catalog_detail"),
    path(
        "excel-catalog/<int:pk>/download/",
        views.excel_catalog_download,
        name="excel_catalog_download",
    ),
]
