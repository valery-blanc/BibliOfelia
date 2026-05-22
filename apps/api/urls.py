"""Routes de l'API OfeliaScan v1. SPEC §6.10 / SPEC-CORR-001.

Chemins SANS slash final : OfeliaScan concatène les chemins relatifs à la base
URL (dont le slash final est significatif) et appelle p. ex. `<base>auth/login`.
"""
from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("auth/login", views.LoginView.as_view(), name="auth-login"),
    path("auth/refresh", views.RefreshView.as_view(), name="auth-refresh"),
    path("auth/logout", views.LogoutView.as_view(), name="auth-logout"),
    path("pairing/info", views.PairingInfoView.as_view(), name="pairing-info"),
    path("isbn/<str:isbn>", views.IsbnLookupView.as_view(), name="isbn-lookup"),
    path("health", views.HealthView.as_view(), name="health"),
    # FEAT-021 — Sessions de scan (catalogage) et récolement OfeliaScan
    path("scan-sessions", views.ScanSessionCreateView.as_view(), name="scan-create"),
    path(
        "scan-sessions/<uuid:session_id>/items",
        views.ScanSessionItemsView.as_view(),
        name="scan-items",
    ),
    path(
        "scan-sessions/<uuid:session_id>/finalize",
        views.ScanSessionFinalizeView.as_view(),
        name="scan-finalize",
    ),
    path(
        "inventory-sessions",
        views.InventorySessionCreateView.as_view(),
        name="inventory-create",
    ),
    path(
        "inventory-sessions/<uuid:session_id>/items",
        views.InventorySessionItemsView.as_view(),
        name="inventory-items",
    ),
    path(
        "inventory-sessions/<uuid:session_id>/close",
        views.InventorySessionCloseView.as_view(),
        name="inventory-close",
    ),
]
