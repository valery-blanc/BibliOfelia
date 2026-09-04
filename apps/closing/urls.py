from django.urls import path

from . import views

app_name = "closing"

urlpatterns = [
    path("", views.day_closing, name="day_closing"),
    path("activities/", views.activity_list, name="activity_list"),
    path("activities/<int:pk>/delete/", views.activity_delete, name="activity_delete"),
    path("animations/", views.animation_list, name="animation_list"),
    path("animations/<int:pk>/", views.animation_detail, name="animation_detail"),
    path("animations/<int:pk>/attendee/", views.animation_add_attendee, name="animation_add_attendee"),
    path(
        "animations/<int:pk>/attendee/<int:attendance_pk>/remove/",
        views.animation_remove_attendee,
        name="animation_remove_attendee",
    ),
    path("animations/<int:pk>/delete/", views.animation_delete, name="animation_delete"),
    path("types/", views.type_list, name="type_list"),
    path("types/<str:kind>/<int:pk>/toggle/", views.type_toggle, name="type_toggle"),
    path("stats/", views.stats, name="stats"),
    path("stats/csv/", views.stats_csv, name="stats_csv"),
]
