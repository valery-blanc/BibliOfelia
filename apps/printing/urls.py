from django.urls import path

from . import views

app_name = "printing"

urlpatterns = [
    path("labels/", views.labels_picker, name="labels"),
    path("labels.pdf", views.labels_pdf, name="labels_pdf"),
    path("labels/send/", views.labels_send, name="labels_send"),
    path("cards/", views.cards_picker, name="cards"),
    path("cards.pdf", views.cards_pdf, name="cards_pdf"),
]
