from django.urls import path

from . import views

app_name = "members"

urlpatterns = [
    path("", views.member_list, name="list"),
    path("new/", views.member_create, name="create"),
    path("<int:pk>/", views.member_detail, name="detail"),
    path("<int:pk>/edit/", views.member_edit, name="edit"),
    path("<int:pk>/history/", views.member_history, name="history"),
    path("<int:pk>/replace-card/", views.member_replace_card, name="replace_card"),
    path("<int:pk>/renew/", views.member_renew, name="renew"),
    path("<int:pk>/toggle-active/", views.member_toggle_active, name="toggle_active"),
    path("<int:pk>/delete/", views.member_delete, name="delete"),
]
