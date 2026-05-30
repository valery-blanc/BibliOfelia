"""Batch de traductions Sprint 17 (corrections i18n — BUG-016).

Couvre les chaînes signalées par Val après FEAT-044 :
- libellés du formulaire « Ajouter des exemplaires » (ItemForm) restés en
  anglais faute de `labels` traduits ;
- libellé « réservé au support technique » (remplace « réservé Claude /
  support distant ») dans templates/core/advanced.html.

Les clés FR doivent matcher exactement les msgid extraits par makemessages.

Usage : `python scripts/translations_sprint17.py`.
"""
from __future__ import annotations

from pathlib import Path

_AT = Path(__file__).parent / "apply_translations.py"
_source = _AT.read_text(encoding="utf-8")
_trimmed = _source.split("\nfor lang in")[0]
_globals: dict = {"__name__": "__main__", "__file__": str(_AT)}
exec(compile(_trimmed, str(_AT), "exec"), _globals)  # noqa: S102
process_file = _globals["process_file"]
ROOT = Path(__file__).parent.parent / "locale"


TRANSLATIONS = {
    "Date d'acquisition": {
        "en": "Acquisition date",
        "es": "Fecha de adquisición",
        "mg": "Daty fahazoana",
    },
    "Source d'acquisition": {
        "en": "Acquisition source",
        "es": "Origen de adquisición",
        "mg": "Loharanon'ny fahazoana",
    },
    "Donateur": {
        "en": "Donor",
        "es": "Donante",
        "mg": "Mpanome",
    },
    "Notes": {
        "en": "Notes",
        "es": "Notas",
        "mg": "Fanamarihana",
    },
    "Gestion fine : catégories, tags, emplacements, catégories d'usagers "
    "(réservé au support technique).": {
        "en": "Fine-grained management: categories, tags, locations, user "
              "categories (reserved for technical support).",
        "es": "Gestión fina: categorías, etiquetas, ubicaciones, categorías de "
              "usuarios (reservado al soporte técnico).",
        "mg": "Fitantanana madinika: sokajy, marika, toerana, sokajin'ny "
              "mpampiasa (natokana ho an'ny tohana ara-teknika).",
    },
}


def main() -> None:
    total = 0
    for lang in ("en", "es", "mg"):
        po_file = ROOT / lang / "LC_MESSAGES" / "django.po"
        _globals["TRANSLATIONS"] = TRANSLATIONS
        replaced, fuzzy_removed = process_file(po_file, lang)
        print(f"  {lang}: {replaced} traductions appliquées, {fuzzy_removed} fuzzy supprimés")
        total += replaced
    print(f"\nTotal : {total} entrées remplacées sur les 3 langues.")


if __name__ == "__main__":
    main()
