from django.urls import path

from . import views

app_name = "printing"

urlpatterns = [
    path("labels/", views.labels_picker, name="labels"),
    path("labels.pdf", views.labels_pdf, name="labels_pdf"),
    path("cards/", views.cards_picker, name="cards"),
    path("cards.pdf", views.cards_pdf, name="cards_pdf"),
    # FEAT-062 — ruban continu Brother QL-810W
    path("labels-roll.pdf", views.labels_roll_pdf, name="labels_roll_pdf"),
    path("cards-roll.pdf", views.cards_roll_pdf, name="cards_roll_pdf"),
    # FEAT-068 — étiquettes de tranche (cote de catégorie)
    # FEAT-075 : écran de sélection dédié, distinct des étiquettes « code Ofelia »
    path("spine-labels/", views.spine_labels_picker, name="spine_labels"),
    path("spine-labels.pdf", views.spine_labels_pdf, name="spine_labels_pdf"),
    path(
        "spine-labels-roll.pdf",
        views.spine_labels_roll_pdf,
        name="spine_labels_roll_pdf",
    ),
]
