"""Batch de traductions Sprint 17 / FEAT-045 (récolement caméra continu).

Chaînes ajoutées par le scan caméra continu du récolement : libellés du panneau
de scan de la page rapport, feedback live, mode continu du viseur, et messages
serveur. Les clés FR doivent matcher exactement les msgid extraits par
makemessages.

Usage : `python scripts/translations_sprint18.py`.
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
    "Code vide.": {
        "en": "Empty code.",
        "es": "Código vacío.",
        "mg": "Kaody foana.",
    },
    "Terminer": {
        "en": "Finish",
        "es": "Terminar",
        "mg": "Vita",
    },
    "Choisissez le périmètre à pointer, puis lancez le scan caméra.": {
        "en": "Choose the scope to check, then start the camera scan.",
        "es": "Elija el alcance a inventariar y luego inicie el escaneo con la cámara.",
        "mg": "Fidio ny faritra hojerena, dia atombohy ny fakana sary amin'ny fakan-tsary.",
    },
    "Inconnu du catalogue": {
        "en": "Not in catalogue",
        "es": "Desconocido en el catálogo",
        "mg": "Tsy ao amin'ny katalaogy",
    },
    "Ouverture…": {
        "en": "Opening…",
        "es": "Abriendo…",
        "mg": "Misokatra…",
    },
    "Continuer l'inventaire": {
        "en": "Continue inventory",
        "es": "Continuar el inventario",
        "mg": "Tohizo ny fanisana",
    },
    "attendus": {
        "en": "expected",
        "es": "esperados",
        "mg": "andrasana",
    },
    "Saisir un code Ofelia à la main": {
        "en": "Enter an Ofelia code by hand",
        "es": "Introducir un código Ofelia a mano",
        "mg": "Soraty an-tanana ny kaody Ofelia",
    },
    "Scannés :": {
        "en": "Scanned:",
        "es": "Escaneados:",
        "mg": "Voafaka sary:",
    },
    "Déjà pointé": {
        "en": "Already checked",
        "es": "Ya inventariado",
        "mg": "Efa voamarika",
    },
    "pointés": {
        "en": "checked",
        "es": "inventariados",
        "mg": "voamarika",
    },
    # Itération 2 — rapport par notice + libellés de pastilles.
    "Exemplaires par notice": {
        "en": "Copies by record",
        "es": "Ejemplares por registro",
        "mg": "Kopia isaky ny rakitra",
    },
    "Trouvé": {
        "en": "Found",
        "es": "Encontrado",
        "mg": "Hita",
    },
    "Manquant": {
        "en": "Missing",
        "es": "Faltante",
        "mg": "Tsy hita",
    },
    "Auteur": {
        "en": "Author",
        "es": "Autor",
        "mg": "Mpanoratra",
    },
    "Codes Ofelia": {
        "en": "Ofelia codes",
        "es": "Códigos Ofelia",
        "mg": "Kaody Ofelia",
    },
    "Aucun exemplaire attendu dans ce périmètre.": {
        "en": "No copies expected in this scope.",
        "es": "No se espera ningún ejemplar en este alcance.",
        "mg": "Tsy misy kopia andrasana amin'ity faritra ity.",
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
