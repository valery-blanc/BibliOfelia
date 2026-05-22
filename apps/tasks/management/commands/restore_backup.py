"""Restauration d'une sauvegarde locale. SPEC §8.3.

    python manage.py restore_backup /backup/db/daily/bibliofelia-...sqlite3

L'app doit être stoppée le temps de la restauration (recommandation).
La BD actuelle est sauvegardée à côté (`.pre-restore.<ts>`).
"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.tasks.backup import restore_from_file


class Command(BaseCommand):
    help = "Restaure la BD SQLite depuis un fichier de sauvegarde."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Chemin du fichier .sqlite3[.gz]")
        parser.add_argument("--yes", action="store_true",
                            help="Confirme sans demander.")

    def handle(self, *args, **options):
        path = options["path"]
        if not options["yes"]:
            answer = input(
                f"Restaurer {path} en écrasant la BD courante ? Tapez OUI : "
            )
            if answer.strip() != "OUI":
                raise CommandError("Annulé.")
        try:
            restore_from_file(path)
        except Exception as exc:
            raise CommandError(f"Échec restauration : {exc}") from exc
        self.stdout.write(self.style.SUCCESS("Restauration terminée."))
