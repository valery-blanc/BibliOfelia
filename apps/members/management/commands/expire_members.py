"""Marque les cartes d'usager échues comme `expired`. SPEC §6.2.

Destiné à être planifié quotidiennement via django-q2 (Schedule créé au
premier démarrage / paramétrage — Task #15). Exécutable manuellement :

    python manage.py expire_members
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.members.services import mark_expired_members


class Command(BaseCommand):
    help = "Passe en statut 'expired' les cartes d'usager dont la date est échue."

    def handle(self, *args, **options):
        count = mark_expired_members()
        self.stdout.write(self.style.SUCCESS(f"{count} carte(s) marquée(s) expirée(s)."))
