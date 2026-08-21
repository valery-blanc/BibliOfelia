"""Crée les objets par défaut au premier démarrage (idempotent).

SPEC §5.2 : seed Settings + Categories + MemberCategories.

FEAT-042 (Sprint 13) : les noms de Categories et MemberCategories du seed
sont fournis dans les 4 langues activées (fr/en/es/mg) et `seed_defaults`
backfille `name_en`/`name_es`/`name_mg` sur les installations existantes
**uniquement si le champ est vide** (préserve les traductions manuelles).
"""
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Setting


# FEAT-071 : catégories officielles Ofelia — 5 tranches d'âge × 4 types de
# document. Le **code est la cote** imprimée sur l'étiquette de tranche : c'est
# déjà la convention des bibliothèques Ofelia, et une cote différente du code
# n'aurait ici aucune justification.
#
# Construites par produit des deux tables ci-dessous plutôt qu'écrites à la
# main : 20 lignes × 5 colonnes recopiées, c'est une coquille assurée — et la
# structure « tranche d'âge × type » se lit d'un coup d'œil.
_AGE_GROUPS = [
    ("AD",  "Adultes",        "Adults",          "Adultos",          "Olon-dehibe"),
    ("JE",  "Jeunesse",       "Youth",           "Juvenil",          "Tanora"),
    ("ADO", "Adolescents",    "Teens",           "Adolescentes",     "Zatovo"),
    ("EN",  "Enfants",        "Children",        "Infantil",         "Ankizy"),
    ("PE",  "Petite enfance", "Early childhood", "Primera infancia", "Zaza madinika"),
]
_DOC_KINDS = [
    ("FIC", "Fiction",        "Fiction",       "Ficción",    "Tantara foronina"),
    ("DOC", "Documentaire",   "Non-fiction",   "Documental", "Fampianarana"),
    ("ALB", "Album",          "Picture books",  "Álbum",     "Boky misy sary"),
    ("BD",  "Bande dessinée", "Comics",        "Cómic",      "Tantara an-tsary"),
]

# (code, parent_code, default_loan_duration_days, name_fr, name_en, name_es,
#  name_mg, abbreviation) — cf. FEAT-042 pour les traductions, FEAT-067 pour la
# cote. Plus de hiérarchie parent : une tranche d'âge n'est pas un rayon.
CATEGORIES = [
    (
        f"{age_code} {kind_code}",
        None,
        None,
        f"{age_fr} {kind_fr}",
        f"{age_en} {kind_en}",
        f"{age_es} {kind_es}",
        f"{age_mg} {kind_mg}",
        f"{age_code} {kind_code}",
    )
    for age_code, age_fr, age_en, age_es, age_mg in _AGE_GROUPS
    for kind_code, kind_fr, kind_en, kind_es, kind_mg in _DOC_KINDS
]

# FEAT-070 : (code, name_fr, name_en, name_es, name_mg). Codes internationaux
# principaux, sans variante régionale : `fr` couvre le français de France, du
# Canada et de Suisse ; `pt` le portugais et le brésilien. La liste est
# extensible depuis l'écran Avancé → Langues.
LANGUAGES_SEED = [
    ("fr",       "Français",     "French",          "Francés",     "Frantsay"),
    ("en",       "Anglais",      "English",         "Inglés",      "Anglisy"),
    ("pt",       "Portugais",    "Portuguese",      "Portugués",   "Portogey"),
    ("es",       "Espagnol",     "Spanish",         "Español",     "Espaniola"),
    ("it",       "Italien",      "Italian",         "Italiano",    "Italiana"),
    ("de",       "Allemand",     "German",          "Alemán",      "Alemana"),
    ("ar",       "Arabe",        "Arabic",          "Árabe",       "Arabo"),
    ("sq",       "Albanais",     "Albanian",        "Albanés",     "Albaney"),
    ("tr",       "Turc",         "Turkish",         "Turco",       "Tiorka"),
    ("ru",       "Russe",        "Russian",         "Ruso",        "Rosiana"),
    ("sh",       "Serbo-croate", "Serbo-Croatian",  "Serbocroata", "Serbo-kroaty"),
    ("ta",       "Tamoul",       "Tamil",           "Tamil",       "Tamoly"),
    ("zh",       "Chinois",      "Chinese",         "Chino",       "Sinoa"),
    ("pl",       "Polonais",     "Polish",          "Polaco",      "Poloney"),
    ("fa",       "Persan",       "Persian",         "Persa",       "Persana"),
    ("fa-farsi", "Farsi",        "Farsi",           "Farsi",       "Farsy"),
    ("el",       "Grec",         "Greek",           "Griego",      "Grika"),
    ("so",       "Somali",       "Somali",          "Somalí",      "Somaly"),
    ("ro",       "Roumain",      "Romanian",        "Rumano",      "Romaniana"),
    ("uk",       "Ukrainien",    "Ukrainian",       "Ucraniano",   "Okrainiana"),
    ("ja",       "Japonais",     "Japanese",        "Japonés",     "Japoney"),
    ("mg",       "Malgache",     "Malagasy",        "Malgache",    "Malagasy"),
]

# FEAT-042 : (code, max_loans, default_loan_duration_days, card_validity_months,
#            name_fr, name_en, name_es, name_mg)
MEMBER_CATEGORIES = [
    ("ENFANT",     3,  21, 12, "Enfant (< 14 ans)",          "Child (under 14)",        "Niño (menor de 14 años)",       "Ankizy (latsaky ny 14 taona)"),
    ("ADO",        5,  21, 12, "Adolescent (14-17 ans)",     "Teenager (14-17)",        "Adolescente (14-17 años)",      "Tanora (14-17 taona)"),
    ("ADULTE",     5,  21, 12, "Adulte",                     "Adult",                   "Adulto",                        "Olon-dehibe"),
    ("ENSEIGNANT", 15, 60, 12, "Enseignant",                 "Teacher",                 "Docente",                       "Mpampianatra"),
    ("COLLECTIF",  20, 30, 12, "Collectif (école/famille)",  "Group (school/family)",   "Colectivo (escuela/familia)",   "Vondrona (sekoly/fianakaviana)"),
]


def _backfill_translations(obj, name_fr: str, name_en: str, name_es: str, name_mg: str) -> bool:
    """Remplit les `name_<lang>` vides sans écraser les traductions existantes."""
    changed = False
    for attr, value in (
        ("name_fr", name_fr),
        ("name_en", name_en),
        ("name_es", name_es),
        ("name_mg", name_mg),
    ):
        current = getattr(obj, attr, None)
        if not current and value:
            setattr(obj, attr, value)
            changed = True
    return changed


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
        "roll_printer_format": (
            {"enabled": True, "tape_width_mm": 62, "label_length_mm": 35,
             "card_length_mm": 89, "two_color": True, "show_logo": True},
            "Imprimante à ruban continu Brother QL-810W (FEAT-062)",
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
        cat_backfilled = 0
        cat_by_code: dict[str, Category] = {}
        for code, parent_code, dur, name_fr, name_en, name_es, name_mg, abbr in CATEGORIES:
            parent = cat_by_code.get(parent_code) if parent_code else None
            obj, created = Category.objects.get_or_create(
                code=code,
                defaults={
                    "name": name_fr,
                    "name_fr": name_fr,
                    "name_en": name_en,
                    "name_es": name_es,
                    "name_mg": name_mg,
                    "abbreviation": abbr,
                    "parent": parent,
                    "default_loan_duration_days": dur,
                },
            )
            cat_by_code[code] = obj
            if created:
                cat_created += 1
            else:
                changed = _backfill_translations(obj, name_fr, name_en, name_es, name_mg)
                # FEAT-067 : ne remplit que si vide — une cote ajustée à la main
                # ne doit pas être écrasée au redémarrage.
                if not obj.abbreviation and abbr:
                    obj.abbreviation = abbr
                    changed = True
                if changed:
                    obj.save()
                    cat_backfilled += 1

        # FEAT-070 : langues (documents + langues parlées des usagers).
        from apps.catalog.models import Language

        lang_created = 0
        lang_backfilled = 0
        for code, name_fr, name_en, name_es, name_mg in LANGUAGES_SEED:
            obj, created = Language.objects.get_or_create(
                code=code,
                defaults={
                    "name": name_fr,
                    "name_fr": name_fr,
                    "name_en": name_en,
                    "name_es": name_es,
                    "name_mg": name_mg,
                },
            )
            if created:
                lang_created += 1
            elif _backfill_translations(obj, name_fr, name_en, name_es, name_mg):
                obj.save()
                lang_backfilled += 1

        mcat_created = 0
        mcat_backfilled = 0
        for code, max_loans, dur, validity, name_fr, name_en, name_es, name_mg in MEMBER_CATEGORIES:
            obj, created = MemberCategory.objects.get_or_create(
                code=code,
                defaults={
                    "name": name_fr,
                    "name_fr": name_fr,
                    "name_en": name_en,
                    "name_es": name_es,
                    "name_mg": name_mg,
                    "max_concurrent_loans": max_loans,
                    "default_loan_duration_days": dur,
                    "card_validity_months": validity,
                },
            )
            if created:
                mcat_created += 1
            else:
                if _backfill_translations(obj, name_fr, name_en, name_es, name_mg):
                    obj.save()
                    mcat_backfilled += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"seed_defaults : {settings_created} Setting, "
                f"{cat_created} Category créées (+{cat_backfilled} backfill traductions), "
                f"{mcat_created} MemberCategory créées (+{mcat_backfilled} backfill traductions), "
                f"{lang_created} Language créées (+{lang_backfilled} backfill traductions)."
            )
        )
