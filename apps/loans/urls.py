from django.urls import path

from . import views

app_name = "loans"

urlpatterns = [
    path("lend/", views.lend, name="lend"),
    path("return/", views.return_items, name="return_items"),
    path("consultation/", views.consultation, name="consultation"),
    path("renew/<int:pk>/", views.renew_loan_view, name="renew_loan"),
    path("lost/<int:pk>/", views.mark_lost, name="mark_lost"),
    path("reservations/", views.reservation_list, name="reservations"),
    path("reservations/new/<int:record_pk>/", views.reservation_create, name="reservation_create"),
    path("reservations/<int:pk>/cancel/", views.reservation_cancel, name="reservation_cancel"),
]
