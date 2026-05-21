"""Routes API v1. Endpoints implémentés dans Task #16. /health/ déjà fonctionnel."""
from django.urls import path

from apps.core.views import health

app_name = "api"

urlpatterns = [
    path("health/", health, name="health"),
]
