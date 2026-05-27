"""Batch de traductions Sprint 13 (FEAT-040 + FEAT-041 + FEAT-042).

Couvre toutes les chaînes manquantes/fuzzy détectées par
`scripts/i18n_check.py` au 2026-05-27 sur les 3 features du Sprint 13.

Usage : `python scripts/translations_sprint13.py`.
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
    # --- FEAT-040 exports CSV --------------------------------------------
    "Exports CSV": {
        "en": "CSV exports",
        "es": "Exportaciones CSV",
        "mg": "Fanondranana CSV",
    },
    "Export CSV des prêts (par période)": {
        "en": "Loans CSV export (by period)",
        "es": "Exportación CSV de préstamos (por período)",
        "mg": "Fanondranana CSV ny fampindramana (araka ny vanim-potoana)",
    },
    "Catalogue complet (CSV)": {
        "en": "Full catalog (CSV)",
        "es": "Catálogo completo (CSV)",
        "mg": "Katalaogy feno (CSV)",
    },
    "Une ligne par exemplaire, toutes les métadonnées de la notice.": {
        "en": "One row per copy, all bibliographic metadata.",
        "es": "Una línea por ejemplar, todos los metadatos del registro.",
        "mg": "Andalana iray isaky ny kopia, ny metadata rehetra amin'ny rakitra.",
    },
    "Prêts et réservations en cours (CSV)": {
        "en": "Active loans and reservations (CSV)",
        "es": "Préstamos y reservas en curso (CSV)",
        "mg": "Fampindramana sy fanokanana mandeha (CSV)",
    },
    "Tous les prêts actifs / en retard et toutes les réservations en attente ou prêtes au retrait.": {
        "en": "All active / overdue loans and all pending or ready-for-pickup reservations.",
        "es": "Todos los préstamos activos / atrasados y todas las reservas pendientes o listas para retirar.",
        "mg": "Ny fampindramana mandeha / tara rehetra sy ny fanokanana miandry na vonona haka rehetra.",
    },
    "CSV usagers": {
        "en": "Members CSV",
        "es": "CSV usuarios",
        "mg": "CSV mpikambana",
    },
    "CSV exemplaires": {
        "en": "Copies CSV",
        "es": "CSV ejemplares",
        "mg": "CSV kopia",
    },
    "Dernière activité": {
        "en": "Last activity",
        "es": "Última actividad",
        "mg": "Hetsika farany",
    },
    "Aucune activité": {
        "en": "No activity",
        "es": "Sin actividad",
        "mg": "Tsy misy hetsika",
    },

    # --- FEAT-041 bulk affect category + location ------------------------
    "Affecter une catégorie": {
        "en": "Assign a category",
        "es": "Asignar una categoría",
        "mg": "Manendry sokajy",
    },
    "Affecter un emplacement": {
        "en": "Assign a location",
        "es": "Asignar una ubicación",
        "mg": "Manendry toerana",
    },
    "Affecter une catégorie en masse": {
        "en": "Bulk assign a category",
        "es": "Asignar una categoría en masa",
        "mg": "Manendry sokajy faobe",
    },
    "Affecter un emplacement en masse": {
        "en": "Bulk assign a location",
        "es": "Asignar una ubicación en masa",
        "mg": "Manendry toerana faobe",
    },
    "Notices concernées": {
        "en": "Records affected",
        "es": "Registros afectados",
        "mg": "Rakitra voakasika",
    },
    "Catégorie actuelle": {
        "en": "Current category",
        "es": "Categoría actual",
        "mg": "Sokajy ankehitriny",
    },
    "Nouvelle catégorie": {
        "en": "New category",
        "es": "Nueva categoría",
        "mg": "Sokajy vaovao",
    },
    "— (vider la catégorie)": {
        "en": "— (clear category)",
        "es": "— (vaciar categoría)",
        "mg": "— (mamafa ny sokajy)",
    },
    "— (vider l'emplacement)": {
        "en": "— (clear location)",
        "es": "— (vaciar ubicación)",
        "mg": "— (mamafa ny toerana)",
    },
    "Nouvel emplacement (appliqué à tous les exemplaires)": {
        "en": "New location (applied to all copies)",
        "es": "Nueva ubicación (aplicada a todos los ejemplares)",
        "mg": "Toerana vaovao (ampiharina amin'ny kopia rehetra)",
    },
    "Appliquer": {
        "en": "Apply",
        "es": "Aplicar",
        "mg": "Mampihatra",
    },
    "%(n)s notice(s) affectée(s) à la catégorie %(c)s.": {
        "en": "%(n)s record(s) assigned to category %(c)s.",
        "es": "%(n)s registro(s) asignado(s) a la categoría %(c)s.",
        "mg": "%(n)s rakitra natendry ho amin'ny sokajy %(c)s.",
    },
    "%(n)s notice(s) sans catégorie (catégorie vidée).": {
        "en": "%(n)s record(s) without category (category cleared).",
        "es": "%(n)s registro(s) sin categoría (categoría vaciada).",
        "mg": "%(n)s rakitra tsy misy sokajy (sokajy nofafàna).",
    },
    "%(n)s exemplaire(s) affecté(s) à l'emplacement %(l)s.": {
        "en": "%(n)s copy(ies) assigned to location %(l)s.",
        "es": "%(n)s ejemplar(es) asignado(s) a la ubicación %(l)s.",
        "mg": "%(n)s kopia natendry ho amin'ny toerana %(l)s.",
    },
    "%(n)s exemplaire(s) sans emplacement (emplacement vidé).": {
        "en": "%(n)s copy(ies) without location (location cleared).",
        "es": "%(n)s ejemplar(es) sin ubicación (ubicación vaciada).",
        "mg": "%(n)s kopia tsy misy toerana (toerana nofafàna).",
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
