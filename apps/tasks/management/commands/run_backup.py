"""Sauvegarde manuelle. SPEC §8.

    python manage.py run_backup [--force-daily] [--force-cloud]

Planifiée par django-q2 toutes les heures via `apps.tasks.scheduling`.
"""
from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.tasks.backup import run_backup


class Command(BaseCommand):
    help = "Sauvegarde la BD SQLite et le dossier media."

    def add_arguments(self, parser):
        parser.add_argument("--force-daily", action="store_true",
                            help="Force la promotion daily/weekly/monthly et le rsync media.")
        parser.add_argument("--force-cloud", action="store_true",
                            help="Force le push cloud rclone (si activé).")

    def handle(self, *args, **options):
        result = run_backup(
            force_daily=options["force_daily"],
            force_cloud=options["force_cloud"],
        )
        if result.status == "ok":
            self.stdout.write(self.style.SUCCESS(
                f"Backup OK → {result.db_path} ({result.size_bytes} octets)"
            ))
        else:
            self.stderr.write(self.style.ERROR(f"Backup KO : {result.error}"))
