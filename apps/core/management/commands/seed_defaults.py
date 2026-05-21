"""Crée les objets par défaut au premier démarrage (idempotent).

Étoffé dans le slice modèles (§5.2 seed catégories, MemberCategory) et le wizard (§11.3).
"""
from django.core.management.base import BaseCommand

from apps.core.models import Setting


class Command(BaseCommand):
    help = "Crée les Setting par défaut si absents (idempotent)."

    DEFAULTS = {
        "library_name": ("BibliOfelia", "Nom de la bibliothèque"),
        "library_address": ("", "Adresse de la bibliothèque"),
        "default_language": ("fr", "Langue par défaut"),
        "enabled_languages": (["fr", "en", "es", "mg"], "Langues activées"),
        "reservation_expiry_days": (7, "Délai d'expiration d'une réservation pending"),
        "pickup_hold_days": (5, "Délai de garde après mise à dispo"),
        "overdue_grace_days": (0, "Tolérance retard avant notification"),
        "backup_usb_path": ("/backup", "Chemin de la clé USB de sauvegarde"),
        "cloud_backup_enabled": (False, "Sauvegarde cloud activée"),
        "printer_label_format": (
            {"width_mm": 50, "height_mm": 25},
            "Format étiquette exemplaire",
        ),
        "printer_card_format": (
            {"per_sheet": 8, "paper": "A4"},
            "Format carte membre",
        ),
        "setup_completed": (False, "Wizard d'installation terminé"),
    }

    def handle(self, *args, **opts):
        created = 0
        for key, (value, description) in self.DEFAULTS.items():
            obj, was_created = Setting.objects.get_or_create(
                pk=key, defaults={"value": value, "description": description}
            )
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"seed_defaults : {created} Setting créé(s)."))
