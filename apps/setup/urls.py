from django.urls import path

from . import views

app_name = "setup"

urlpatterns = [
    path("", views.wizard_index, name="wizard"),
    path("step/<slug:step>/", views.wizard_step, name="step"),
    path("finalize/", views.wizard_finalize, name="finalize"),
]
