from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("search/", views.global_search, name="search"),
    path("help/", views.help_page, name="help"),
    path("preferences/advanced/", views.toggle_advanced, name="toggle_advanced"),
]
