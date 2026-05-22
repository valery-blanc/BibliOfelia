"""Expire les réservations échues. SPEC §6.4.

À planifier quotidiennement via django-q2 (Schedule créé au paramétrage —
Task #15). Exécutable manuellement :

    python manage.py expire_reservations
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.loans.services import expire_stale_reservations


class Command(BaseCommand):
    help = "Expire les réservations en attente échues et les mises de côté non retirées."

    def handle(self, *args, **options):
        result = expire_stale_reservations()
        self.stdout.write(
            self.style.SUCCESS(
                f"{result['pending_expired']} réservation(s) en attente expirée(s), "
                f"{result['pickup_expired']} mise(s) de côté libérée(s)."
            )
        )
