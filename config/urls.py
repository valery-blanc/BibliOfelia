"""URL roots de BibliOfelia.

Note : `FORCE_SCRIPT_NAME` est utilisé en prod pour servir l'app sous
`/bibliofelia/` derrière nginx. Les routes ci-dessous sont relatives.
"""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core.i18n_views import set_language as core_set_language

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.api.urls", namespace="api")),
    # BUG-013 (récurrent) : wrapper qui force `FORCE_SCRIPT_NAME` sur la
    # redirection de `set_language`. Remplace `django.conf.urls.i18n` qui
    # casse en prod quand l'URL courante ne se résout pas.
    path("i18n/setlang/", core_set_language, name="set_language"),
    path("setup/", include("apps.setup.urls", namespace="setup")),
]

# Tout le reste sous i18n_patterns : préfixe de langue sur TOUTES les URLs
# (`/fr/…`, `/en/…`, etc.). `prefix_default_language=True` est indispensable
# pour que le sélecteur de langue et le cookie de préférence soient respectés
# partout (cf. FEAT-005 / discussion i18n Sprint 2).
#
# `accounts/` (login + logout + gestion comptes, Sprint 4) est sous i18n_patterns :
# LocaleMiddleware redirige `/accounts/login/` → `/<lang>/accounts/login/`
# automatiquement, et `/fr/accounts/users/` (FEAT-011) fonctionne.
urlpatterns += i18n_patterns(
    path("", include("apps.core.urls", namespace="core")),
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("catalog/", include("apps.catalog.urls", namespace="catalog")),
    path("members/", include("apps.members.urls", namespace="members")),
    path("loans/", include("apps.loans.urls", namespace="loans")),
    path("inventory/", include("apps.inventory.urls", namespace="inventory")),
    path("printing/", include("apps.printing.urls", namespace="printing")),
    path("reports/", include("apps.reports.urls", namespace="reports")),
    path("finance/", include("apps.finance.urls", namespace="finance")),
    path("closing/", include("apps.closing.urls", namespace="closing")),
    prefix_default_language=True,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
    except ImportError:
        pass

# La racine `/` (sans préfixe) ne matche aucune route : LocaleMiddleware la
# redirige vers `/<langue>/` selon le cookie / l'en-tête Accept-Language. Pas
# de RedirectView maison : elle bouclerait sur core:dashboard (BUG-002).
