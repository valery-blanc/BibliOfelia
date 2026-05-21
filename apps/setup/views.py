"""Wizard d'installation — implémenté complètement dans Task #15.

Vue placeholder qui rend juste "à venir" pour que les routes existent.
"""
from django.http import HttpResponse


def wizard_index(request):
    return HttpResponse(
        "Wizard d'installation BibliOfelia — à implémenter (Task #15).",
        content_type="text/plain; charset=utf-8",
    )
