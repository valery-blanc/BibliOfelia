"""Batch de traductions Sprint 16 (FEAT-044 — scanner caméra mode unique).

Couvre les 9 chaînes d'erreur caméra ajoutées dans `templates/base.html`
(`#scan-mode-i18n`). Les clés FR doivent matcher exactement les msgid extraits
par makemessages (apostrophes typographiques ’ incluses).

Usage : `python scripts/translations_sprint16.py`.
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
    "Caméra indisponible": {
        "en": "Camera unavailable",
        "es": "Cámara no disponible",
        "mg": "Tsy misy fakantsary",
    },
    "Saisissez le code à la main.": {
        "en": "Enter the code by hand.",
        "es": "Introduzca el código a mano.",
        "mg": "Soraty an-tanana ny kaody.",
    },
    "Accès caméra impossible : la page n’est pas en HTTPS.": {
        "en": "Camera access impossible: the page is not on HTTPS.",
        "es": "Acceso a la cámara imposible: la página no usa HTTPS.",
        "mg": "Tsy azo idirana ny fakantsary : tsy HTTPS ny pejy.",
    },
    "Ce navigateur ne permet pas l’accès à la caméra.": {
        "en": "This browser does not allow camera access.",
        "es": "Este navegador no permite el acceso a la cámara.",
        "mg": "Tsy mamela ny fidirana amin'ny fakantsary ity navigateur ity.",
    },
    "Permission caméra refusée.": {
        "en": "Camera permission denied.",
        "es": "Permiso de cámara denegado.",
        "mg": "Nolavina ny alalana hampiasa ny fakantsary.",
    },
    "Aucune caméra détectée sur cet appareil.": {
        "en": "No camera detected on this device.",
        "es": "No se detectó ninguna cámara en este dispositivo.",
        "mg": "Tsy nisy fakantsary hita amin'ity fitaovana ity.",
    },
    "La caméra est déjà utilisée par une autre application.": {
        "en": "The camera is already in use by another application.",
        "es": "La cámara ya está siendo utilizada por otra aplicación.",
        "mg": "Efa ampiasain'ny rindranasa hafa ny fakantsary.",
    },
    "Le scanner n’a pas pu être chargé.": {
        "en": "The scanner could not be loaded.",
        "es": "No se pudo cargar el escáner.",
        "mg": "Tsy afaka nampidirina ny scanner.",
    },
    "Impossible de démarrer la caméra.": {
        "en": "Unable to start the camera.",
        "es": "No se puede iniciar la cámara.",
        "mg": "Tsy afaka nanomboka ny fakantsary.",
    },
    # Fuzzy résiduel Sprint 15 (bouton « ? » topbar) re-marqué par makemessages -a.
    "Guide utilisateur": {
        "en": "User guide",
        "es": "Guía del usuario",
        "mg": "Torolàlana ho an'ny mpampiasa",
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
