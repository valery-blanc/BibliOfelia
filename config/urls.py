"""URL roots de BibliOfelia.

Note : `FORCE_SCRIPT_NAME` est utilisé en prod pour servir l'app sous
`/bibliofelia/` derrière nginx. Les routes ci-dessous sont relatives.
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api.urls", namespace="api")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("setup/", include("apps.setup.urls", namespace="setup")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
]

# Tout le reste sous i18n_patterns (préfixe langue dans l'URL)
urlpatterns += i18n_patterns(
    path("", include("apps.core.urls", namespace="core")),
    path("catalog/", include("apps.catalog.urls", namespace="catalog")),
    path("members/", include("apps.members.urls", namespace="members")),
    path("loans/", include("apps.loans.urls", namespace="loans")),
    path("inventory/", include("apps.inventory.urls", namespace="inventory")),
    path("printing/", include("apps.printing.urls", namespace="printing")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

# Page racine → dashboard ou setup
urlpatterns = [path("", RedirectView.as_view(pattern_name="core:dashboard", permanent=False))] + urlpatterns
