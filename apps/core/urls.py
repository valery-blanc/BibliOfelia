from django.urls import path

from . import admin_views, views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("search/", views.global_search, name="search"),
    path("help/", views.help_page, name="help"),
    path("advanced/", views.advanced_index, name="advanced"),
    path("preferences/advanced/", views.toggle_advanced, name="toggle_advanced"),
    # Administration UI (paramètres) — superadmin uniquement
    path("admin/settings/", admin_views.settings_index, name="settings_index"),
    path("admin/settings/<slug:section>/", admin_views.settings_section, name="settings_section"),
    path("admin/backup/now/", admin_views.backup_now, name="backup_now"),
    path("admin/backup/restore/", admin_views.backup_restore, name="backup_restore"),
    path("admin/ofeliascan/", admin_views.ofeliascan_access, name="ofeliascan"),
    path("admin/diagnostics/", admin_views.diagnostics, name="diagnostics"),
    path("admin/enrichment/", admin_views.enrichment_index, name="enrichment_index"),
    path("admin/enrichment/start/", admin_views.enrichment_start, name="enrichment_start"),
    path("admin/enrichment/<int:pk>/", admin_views.enrichment_detail, name="enrichment_detail"),
]
