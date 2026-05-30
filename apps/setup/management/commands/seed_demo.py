"""Installe les données de démo (apps.setup.demo) + extras documentation +
un compte librarian stable pour les captures d'écran du guide utilisateur.

Idempotent : safe à relancer. Utiliser --reset pour repartir d'un état propre.

    python manage.py seed_demo
    python manage.py seed_demo --reset
    python manage.py seed_demo --librarian-password ChangeMe123!
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.setup.demo import install_demo, install_doc_extras, remove_demo


class Command(BaseCommand):
    help = "Seed données de démo + extras doc + compte librarian stable."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Supprime la démo existante avant de la réinstaller (état propre).",
        )
        parser.add_argument(
            "--librarian-username", default="demo_librarian",
            help="Nom d'utilisateur du compte librarian de demo.",
        )
        parser.add_argument(
            "--librarian-password", default="OfeliaDemo2026!",
            help="Mot de passe du compte librarian de demo.",
        )

    def handle(self, *args, **options):
        from apps.accounts.models import Role

        User = get_user_model()

        # 1) Compte librarian (créé en premier pour servir aux prêts)
        username = options["librarian_username"]
        password = options["librarian_password"]
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": "Demo",
                "last_name": "Librarian",
                "email": f"{username}@example.invalid",
                "role": Role.LIBRARIAN,
            },
        )
        user.set_password(password)
        user.role = Role.LIBRARIAN
        user.is_staff = False
        user.is_superuser = False
        user.save()  # post_save signal sync le Group librarian
        action = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(
            f"Compte librarian {action} : username={username} password={password}"
        ))

        # 2) Reset éventuel
        if options["reset"]:
            removed = remove_demo()
            self.stdout.write(self.style.WARNING(
                "Démo supprimée : " + ", ".join(f"{k}={v}" for k, v in removed.items())
            ))

        # 3) Données de base (idempotent : skip si déjà installé)
        counters = install_demo(librarian=user)
        if counters.get("skipped"):
            self.stdout.write(
                "Données de démo : déjà présentes — "
                + ", ".join(f"{k}={v}" for k, v in counters.items() if k != "skipped")
            )
        else:
            self.stdout.write(self.style.SUCCESS(
                "Données de démo : " + ", ".join(f"{k}={v}" for k, v in counters.items())
            ))

        # 4) Extras documentation (réservations, retards, carte expirée)
        extras = install_doc_extras(librarian=user)
        if extras.get("skipped"):
            self.stdout.write("Extras documentation : déjà installés (skip)")
        elif extras.get("error"):
            self.stdout.write(self.style.ERROR(f"Extras documentation : {extras['error']}"))
        else:
            self.stdout.write(self.style.SUCCESS(
                "Extras documentation : "
                + ", ".join(f"{k}={v}" for k, v in extras.items())
            ))
