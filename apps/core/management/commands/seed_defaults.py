"""Crée les objets par défaut au premier démarrage (idempotent).

SPEC §5.2 : seed Settings + Categories + MemberCategories.
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Setting


CATEGORIES = [
    # (code, name_fr, parent_code, default_loan_duration_days)
    ("ENF", "Enfance", None, None),
    ("ENF-ALB", "Albums", "ENF", None),
    ("ENF-LEC", "Premières lectures", "ENF", None),
    ("ENF-ROM", "Romans jeunesse", "ENF", None),
    ("ADU", "Adultes", None, None),
    ("ADU-ROM", "Romans", "ADU", None),
    ("ADU-NOU", "Nouvelles", "ADU", None),
    ("ADU-POE", "Poésie", "ADU", None),
    ("ADU-THE", "Théâtre", "ADU", None),
    ("DOC", "Documentaires", None, None),
    ("DOC-SCI", "Sciences", "DOC", None),
    ("DOC-HIS", "Histoire", "DOC", None),
    ("DOC-GEO", "Géographie", "DOC", None),
    ("DOC-PRA", "Pratique", "DOC", None),
    ("DOC-REL", "Religions", "DOC", None),
    ("PER", "Périodiques", None, 7),
]

MEMBER_CATEGORIES = [
    # (code, name, max_concurrent_loans, default_loan_duration_days, card_validity_months)
    ("ENFANT", "Enfant (< 14 ans)", 3, 21, 12),
    ("ADO", "Adolescent (14-17 ans)", 5, 21, 12),
    ("ADULTE", "Adulte", 5, 21, 12),
    ("ENSEIGNANT", "Enseignant", 15, 60, 12),
    ("COLLECTIF", "Collectif (école/famille)", 20, 30, 12),
]


class Command(BaseCommand):
    help = "Crée Settings, Catégories et MemberCategories par défaut si absents (idempotent)."

    DEFAULTS = {
        "library_name": ("BibliOfelia", "Nom de la bibliothèque"),
        "library_address": ("", "Adresse de la bibliothèque"),
        "default_language": ("fr", "Langue par défaut"),
        "enabled_languages": (["fr", "en", "es", "mg"], "Langues activées"),
        "default_loan_days": (21, "Durée par défaut d'un prêt (fallback global)"),
        "reservation_expiry_days": (7, "Délai d'expiration d'une réservation pending"),
        "pickup_hold_days": (5, "Délai de garde après mise à dispo"),
        "overdue_grace_days": (0, "Tolérance retard avant notification"),
        "backup_usb_path": ("/backup", "Chemin de la clé USB de sauvegarde"),
        "cloud_backup_enabled": (False, "Sauvegarde cloud activée"),
        "printer_label_format": (
            {"width_mm": 50, "height_mm": 25},
            "Format étiquette exemplaire (legacy)",
        ),
        "printer_card_format": (
            {"per_sheet": 8, "paper": "A4"},
            "Format carte membre (legacy)",
        ),
        "card_format": (
            {"per_a4": 8, "show_logo": True, "show_photo": True},
            "Format cartes membres (FEAT-038)",
        ),
        "item_label_format": (
            {"width_mm": 70, "height_mm": 42, "title_max_chars": 50,
             "title_lines": 2, "author_lines": 2, "show_logo": True},
            "Format étiquettes codes Ofelia (FEAT-039)",
        ),
        "setup_completed": (False, "Wizard d'installation terminé"),
    }

    @transaction.atomic
    def handle(self, *args, **opts):
        from apps.catalog.models import Category
        from apps.members.models import MemberCategory

        settings_created = 0
        for key, (value, description) in self.DEFAULTS.items():
            _, created = Setting.objects.get_or_create(
                pk=key, defaults={"value": value, "description": description}
            )
            if created:
                settings_created += 1

        cat_created = 0
        cat_by_code: dict[str, Category] = {}
        for code, name, parent_code, dur in CATEGORIES:
            parent = cat_by_code.get(parent_code) if parent_code else None
            obj, created = Category.objects.get_or_create(
                code=code,
                defaults={"name": name, "parent": parent, "default_loan_duration_days": dur},
            )
            cat_by_code[code] = obj
            if created:
                cat_created += 1

        mcat_created = 0
        for code, name, max_loans, dur, validity in MEMBER_CATEGORIES:
            _, created = MemberCategory.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "max_concurrent_loans": max_loans,
                    "default_loan_duration_days": dur,
                    "card_validity_months": validity,
                },
            )
            if created:
                mcat_created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_defaults : {settings_created} Setting, "
                f"{cat_created} Category, {mcat_created} MemberCategory créés."
            )
        )
