from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.session_list, name="list"),
    path("new/", views.session_create, name="create"),
    path("<int:pk>/scan/", views.add_scan, name="add_scan"),
    path("<int:pk>/close/", views.session_close, name="close"),
    path("<int:pk>/reopen/", views.session_reopen, name="reopen"),
    path("<int:pk>/finalize/", views.session_finalize, name="finalize"),
    path("<int:pk>/report/", views.session_report, name="report"),
]
