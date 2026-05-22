"""Supprime les données de démonstration installées par le wizard. SPEC §11.4.

    python manage.py remove_demo
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.setup.demo import remove_demo


class Command(BaseCommand):
    help = "Supprime les données de démo (marqueur '[DEMO]')."

    def handle(self, *args, **options):
        counters = remove_demo()
        self.stdout.write(self.style.SUCCESS(
            "Suppression : " + ", ".join(f"{k}={v}" for k, v in counters.items())
        ))
