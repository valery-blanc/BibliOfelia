"""Batch de traductions Sprint 14 (FEAT-043 + UX bulk-delete).

Couvre les chaînes manquantes/fuzzy détectées par `scripts/i18n_check.py`
au 2026-05-28 pour le Sprint 14.

Usage : `python scripts/translations_sprint14.py`.
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
    # --- UX bulk-delete --------------------------------------------------
    "Supprimer les notices sélectionnées": {
        "en": "Delete selected records",
        "es": "Eliminar los registros seleccionados",
        "mg": "Hamafa ireo rakitra voafantina",
    },
    "Les notices et tous leurs exemplaires seront supprimés. Les prêts en cours seront marqués « Perdu » et les réservations actives seront annulées. Ces suppressions sont définitives.": {
        "en": "The records and all their copies will be deleted. Active loans will be marked “Lost” and active reservations will be cancelled. These deletions are permanent.",
        "es": "Los registros y todos sus ejemplares serán eliminados. Los préstamos en curso se marcarán como «Perdido» y las reservas activas serán canceladas. Estas eliminaciones son definitivas.",
        "mg": "Ho fafàna ireo rakitra sy ireo kopia rehetra. Ireo fampindramana mandeha dia ho voamarika hoe « Very » ary ireo fanokanana mavitrika dia hofoanana. Tsy azo averina intsony ireo famafana ireo.",
    },
    # --- FEAT-043 RetiredItemCode ---------------------------------------
    "code Ofelia retiré": {
        "en": "retired Ofelia code",
        "es": "código Ofelia retirado",
        "mg": "kaody Ofelia nesorina",
    },
    "codes Ofelia retirés": {
        "en": "retired Ofelia codes",
        "es": "códigos Ofelia retirados",
        "mg": "kaody Ofelia nesorina",
    },
    "Suppression en masse de notices": {
        "en": "Bulk record deletion",
        "es": "Eliminación masiva de registros",
        "mg": "Famafana rakitra an-tapitrisany",
    },
    "Suppression d'exemplaire": {
        "en": "Copy deletion",
        "es": "Eliminación de ejemplar",
        "mg": "Famafana kopia",
    },
    # --- Page 405 custom ------------------------------------------------
    "Méthode non autorisée": {
        "en": "Method not allowed",
        "es": "Método no permitido",
        "mg": "Fomba tsy azo atao",
    },
    "Page précédente": {
        "en": "Previous page",
        "es": "Página anterior",
        "mg": "Pejy teo aloha",
    },
    "Cette page ne peut pas être ouverte directement depuis un lien : elle attend une action validée depuis une autre page.": {
        "en": "This page cannot be opened directly from a link: it expects an action validated from another page.",
        "es": "Esta página no puede abrirse directamente desde un enlace: espera una acción validada desde otra página.",
        "mg": "Tsy azo sokafana mivantana avy amin'ny rohy ity pejy ity : miandry hetsika nankatoavina avy amin'ny pejy hafa izy.",
    },
    "Vous pouvez revenir à la page précédente ou retourner à l'accueil.": {
        "en": "You can go back to the previous page or return to the home page.",
        "es": "Puede volver a la página anterior o regresar a la página de inicio.",
        "mg": "Azonao atao ny miverina amin'ny pejy teo aloha na miverina any amin'ny fandraisana.",
    },
    # --- Pages erreur 400 / 403 / 404 -----------------------------------
    "Requête invalide": {
        "en": "Bad request",
        "es": "Solicitud no válida",
        "mg": "Fangatahana tsy mety",
    },
    "La requête envoyée au serveur n'a pas été comprise.": {
        "en": "The request sent to the server was not understood.",
        "es": "La solicitud enviada al servidor no se entendió.",
        "mg": "Tsy azo ny fangatahana nalefa tany amin'ny serveur.",
    },
    "Réessayez l'opération, ou revenez à la page précédente.": {
        "en": "Try the operation again, or go back to the previous page.",
        "es": "Vuelva a intentar la operación o regrese a la página anterior.",
        "mg": "Andramo indray ilay hetsika, na miverina amin'ny pejy teo aloha.",
    },
    "Accès interdit": {
        "en": "Access denied",
        "es": "Acceso denegado",
        "mg": "Tsy azo idirana",
    },
    "Vous n'avez pas les droits nécessaires pour accéder à cette page.": {
        "en": "You do not have the required rights to access this page.",
        "es": "No tiene los permisos necesarios para acceder a esta página.",
        "mg": "Tsy manana ny zo ilaina ianao mba hidirana amin'ity pejy ity.",
    },
    "Connectez-vous avec un compte autorisé, ou demandez à un administrateur d'élargir vos droits.": {
        "en": "Sign in with an authorized account, or ask an administrator to extend your permissions.",
        "es": "Inicie sesión con una cuenta autorizada o solicite a un administrador que amplíe sus permisos.",
        "mg": "Midira amin'ny kaonty manana alalana, na angataho amin'ny mpitantana mba hanitatra ny zonao.",
    },
    "Page introuvable": {
        "en": "Page not found",
        "es": "Página no encontrada",
        "mg": "Pejy tsy hita",
    },
    "La page demandée n'existe pas ou a été déplacée.": {
        "en": "The requested page does not exist or has been moved.",
        "es": "La página solicitada no existe o ha sido movida.",
        "mg": "Tsy misy na nafindra toerana ny pejy nangatahana.",
    },
    "Vérifiez l'URL, ou revenez à la page précédente ou à l'accueil.": {
        "en": "Check the URL, or go back to the previous page or to the home page.",
        "es": "Compruebe la URL, o vuelva a la página anterior o al inicio.",
        "mg": "Hamarino ny URL, na miverina amin'ny pejy teo aloha na amin'ny fandraisana.",
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
