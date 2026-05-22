"""Installe les Schedule django-q2. Idempotent.

    python manage.py setup_schedules
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.tasks.scheduling import install_schedules


class Command(BaseCommand):
    help = "Installe / met à jour les planifications django-q2 (backup horaire, etc.)."

    def handle(self, *args, **options):
        n = install_schedules()
        self.stdout.write(self.style.SUCCESS(f"{n} planifications installées."))
