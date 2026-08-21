"""FEAT-071 — reprise des catégories existantes vers la liste officielle Ofelia.

Deux héritages à traiter :

1. **Le préfixe de langue** — grand-saconnex range ses livres en
   « Français Adultes Fiction » / `FR AD FIC`. La langue est une propriété du
   livre, pas de son rayon : la dupliquer dans la catégorie multiplie les lignes
   sans rien apporter. On retire le préfixe et on fusionne dans `AD FIC`.
2. **Les anciennes catégories du seed** (`ADU-ROM`, `DOC-SCI`…) — remplacées par
   la liste officielle. Décision Val 2026-08-20 : remapper puis supprimer, pour
   que les notices gardent une catégorie.

La commande est idempotente et ne supprime **jamais** une catégorie qu'elle n'a
pas su reclasser : celles-là sont laissées en place et signalées.

    python manage.py migrate_categories [--dry-run]
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import BibliographicRecord, Category
from apps.core.management.commands.seed_defaults import CATEGORIES

# Préfixes de langue rencontrés en tête de code (« FR AD FIC ») et de nom
# (« Français Adultes Fiction »). Volontairement limité aux langues du projet :
# on ne veut pas décapiter une catégorie dont le nom commence par un mot
# ressemblant à une langue.
_LANG_CODE_PREFIXES = ("FR", "EN", "ES", "MG", "PT", "DE", "IT", "AR")
_LANG_NAME_PREFIXES = (
    "Français", "Francais", "Anglais", "Espagnol", "Malgache",
    "Portugais", "Allemand", "Italien", "Arabe",
)

# Anciennes catégories du seed BibliOfelia → catégorie officielle.
_LEGACY_MAP = {
    "ADU-ROM": "AD FIC",
    "ADU-NOU": "AD FIC",
    "ADU-POE": "AD FIC",
    "ADU-THE": "AD FIC",
    "DOC-SCI": "AD DOC",
    "DOC-HIS": "AD DOC",
    "DOC-GEO": "AD DOC",
    "DOC-PRA": "AD DOC",
    "DOC-REL": "AD DOC",
    "PER": "AD DOC",
    "ENF-ALB": "EN ALB",
    "ENF-LEC": "EN FIC",
    "ENF-ROM": "EN FIC",
    # Catégories « chapeau » sans contenu propre : supprimées si elles sont vides.
    "ENF": None,
    "ADU": None,
    "DOC": None,
}

_TARGET_CODES = {row[0] for row in CATEGORIES}


def _strip_language_prefix(code: str) -> str | None:
    """« FR AD FIC » → « AD FIC », si le reste est une catégorie officielle."""
    parts = (code or "").strip().split(" ", 1)
    if len(parts) != 2:
        return None
    head, rest = parts[0].upper(), parts[1].strip()
    if head in _LANG_CODE_PREFIXES and rest in _TARGET_CODES:
        return rest
    return None


def _target_for(category: Category) -> tuple[str | None, str]:
    """Code cible et raison, ou `(None, raison)` si on ne sait pas reclasser."""
    if category.code in _TARGET_CODES:
        return category.code, "déjà officielle"
    stripped = _strip_language_prefix(category.code)
    if stripped:
        return stripped, "préfixe de langue retiré"
    if category.code in _LEGACY_MAP:
        target = _LEGACY_MAP[category.code]
        return target, "ancienne catégorie du seed"
    return None, "inconnue — laissée en place"


class Command(BaseCommand):
    help = "Reclasse les catégories existantes vers la liste officielle Ofelia."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Affiche ce qui serait fait, sans rien modifier.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        created = self._ensure_targets(dry_run)

        moved = deleted = untouched = 0
        lines: list[str] = []
        with transaction.atomic():
            for category in Category.objects.exclude(code__in=_TARGET_CODES):
                n_records = BibliographicRecord.objects.filter(category=category).count()
                target_code, reason = _target_for(category)

                if target_code is None:
                    if category.code in _LEGACY_MAP:
                        # Catégorie chapeau (ENF, ADU, DOC) : traitée plus bas,
                        # ne pas la compter comme « laissée en place ».
                        continue
                    untouched += 1
                    lines.append(
                        f"  = {category.code!r} ({n_records} notices) — {reason}"
                    )
                    continue

                target = Category.objects.filter(code=target_code).first()
                if target is None:
                    untouched += 1
                    lines.append(
                        f"  = {category.code!r} — cible {target_code!r} absente, laissée en place"
                    )
                    continue

                if n_records and not dry_run:
                    BibliographicRecord.objects.filter(category=category).update(
                        category=target
                    )
                if not dry_run:
                    category.delete()
                moved += n_records
                deleted += 1
                lines.append(
                    f"  → {category.code!r} vers {target_code!r} "
                    f"({n_records} notices) — {reason}"
                )

            # Catégories chapeau vides encore présentes (ENF, ADU, DOC).
            for code, target in _LEGACY_MAP.items():
                if target is not None:
                    continue
                empty = Category.objects.filter(code=code).first()
                if empty and not BibliographicRecord.objects.filter(category=empty).exists():
                    if not dry_run:
                        empty.delete()
                    deleted += 1
                    lines.append(f"  ✕ {code!r} supprimée (vide)")

            if dry_run:
                transaction.set_rollback(True)

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(f"{prefix}{created} catégorie(s) officielle(s) créée(s)")
        for line in lines:
            self.stdout.write(prefix + line)
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}{deleted} ancienne(s) supprimée(s), {moved} notice(s) "
                f"déplacée(s), {untouched} laissée(s) en place."
            )
        )

    def _ensure_targets(self, dry_run: bool) -> int:
        """Crée les catégories officielles manquantes (mêmes valeurs que le seed)."""
        created = 0
        for code, _parent, dur, fr, en, es, mg, abbr in CATEGORIES:
            if Category.objects.filter(code=code).exists():
                continue
            created += 1
            if not dry_run:
                Category.objects.create(
                    code=code,
                    name=fr,
                    name_fr=fr,
                    name_en=en,
                    name_es=es,
                    name_mg=mg,
                    abbreviation=abbr,
                    default_loan_duration_days=dur,
                )
        return created
