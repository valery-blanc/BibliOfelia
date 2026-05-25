"""Batch de traductions Sprint 12 (BUG-013 v2 + FEAT-038 + FEAT-039 + arriéré).

Couvre toutes les chaînes manquantes/fuzzy détectées par
`scripts/i18n_check.py` au 2026-05-26 (Sprint 10 → Sprint 12).

Usage : `python scripts/translations_sprint12.py`.
"""
from __future__ import annotations

from pathlib import Path
import importlib.util

# Charge process_file/quote_po depuis apply_translations.py sans déclencher
# le `for lang in …` du bas du fichier (qui s'exécute si on importe naïvement).
_AT = Path(__file__).parent / "apply_translations.py"
_source = _AT.read_text(encoding="utf-8")
_trimmed = _source.split("\nfor lang in")[0]
_globals: dict = {"__name__": "__main__", "__file__": str(_AT)}
exec(compile(_trimmed, str(_AT), "exec"), _globals)  # noqa: S102
process_file = _globals["process_file"]
ROOT = Path(__file__).parent.parent / "locale"


# {msgid: {"en", "es", "mg"}}
TRANSLATIONS = {
    # --- FEAT-032 emplacements (résiduel) -------------------------------
    "Court, sans espace : A1, JEU-BD, RES…": {
        "en": "Short, no space: A1, GAME-CB, RES…",
        "es": "Corto, sin espacio: A1, JUE-CM, RES…",
        "mg": "Fohy, tsy misy elanelana: A1, KIL-BD, RES…",
    },
    "Sous-emplacement de… (optionnel).": {
        "en": "Sub-location of… (optional).",
        "es": "Sub-ubicación de… (opcional).",
        "mg": "Toerana ambany an'i… (azo atao).",
    },
    "Un emplacement avec ce code existe déjà pour ce parent.": {
        "en": "A location with this code already exists for this parent.",
        "es": "Ya existe una ubicación con este código para este padre.",
        "mg": "Efa misy toerana manana io kaody io ho an'ity ray ity.",
    },
    "Un emplacement ne peut pas être son propre parent.": {
        "en": "A location cannot be its own parent.",
        "es": "Una ubicación no puede ser su propio padre.",
        "mg": "Tsy afaka ho ray ny tenany ny toerana iray.",
    },
    "Emplacement créé.": {
        "en": "Location created.",
        "es": "Ubicación creada.",
        "mg": "Toerana noforonina.",
    },
    "Nouvel emplacement": {
        "en": "New location",
        "es": "Nueva ubicación",
        "mg": "Toerana vaovao",
    },
    "Emplacement mis à jour.": {
        "en": "Location updated.",
        "es": "Ubicación actualizada.",
        "mg": "Toerana nohavaozina.",
    },
    "Modifier l'emplacement": {
        "en": "Edit location",
        "es": "Editar ubicación",
        "mg": "Hanova ny toerana",
    },
    "Emplacement supprimé.": {
        "en": "Location deleted.",
        "es": "Ubicación eliminada.",
        "mg": "Toerana voafafa.",
    },
    "Supprimer l'emplacement": {
        "en": "Delete location",
        "es": "Eliminar ubicación",
        "mg": "Hamafa ny toerana",
    },
    "Emplacements": {
        "en": "Locations",
        "es": "Ubicaciones",
        "mg": "Toerana",
    },
    "Confirmez-vous la suppression de l'emplacement <strong>%(code)s</strong> ?": {
        "en": "Confirm deletion of location <strong>%(code)s</strong>?",
        "es": "¿Confirma la eliminación de la ubicación <strong>%(code)s</strong>?",
        "mg": "Marina ve ny famafana ny toerana <strong>%(code)s</strong> ?",
    },
    "Conséquences": {
        "en": "Consequences",
        "es": "Consecuencias",
        "mg": "Vokany",
    },
    "Les sessions de récolement passées qui ciblaient cet emplacement conservent leur historique.": {
        "en": "Past inventory sessions targeting this location keep their history.",
        "es": "Las sesiones de inventario pasadas dirigidas a esta ubicación conservan su historial.",
        "mg": "Ireo fotoam-pandanjana lasa nikendry ity toerana ity dia mitazona ny tantarany.",
    },
    "Zones de rangement utilisées au catalogage et au récolement": {
        "en": "Storage zones used in cataloging and inventory",
        "es": "Zonas de almacenamiento utilizadas en catalogación e inventario",
        "mg": "Toerana fitehirizana ampiasaina amin'ny fanaovana katalaogy sy ny fandanjana",
    },
    "Code": {
        "en": "Code", "es": "Código", "mg": "Kaody",
    },
    "Description": {
        "en": "Description", "es": "Descripción", "mg": "Famaritana",
    },
    "Parent": {
        "en": "Parent", "es": "Padre", "mg": "Ray",
    },
    "Aucun emplacement défini. Cliquez sur « Nouvel emplacement » pour commencer.": {
        "en": "No location defined. Click \"New location\" to begin.",
        "es": "Ninguna ubicación definida. Haga clic en «Nueva ubicación» para comenzar.",
        "mg": "Tsy misy toerana voafaritra. Tsindrio « Toerana vaovao » hanombohana.",
    },
    "Définir les zones de rangement (Salle adulte, Réserve, A1…). Utilisé au catalogage et au récolement.": {
        "en": "Define storage zones (Adult room, Reserve, A1…). Used in cataloging and inventory.",
        "es": "Definir las zonas de almacenamiento (Sala adulta, Reserva, A1…). Utilizado en catalogación e inventario.",
        "mg": "Famaritana ny toerana fitehirizana (Efitra olon-dehibe, Tahirim-bola, A1…). Ampiasaina amin'ny fanaovana katalaogy sy ny fandanjana.",
    },

    # --- FEAT-038 / FEAT-039 impressions -------------------------------
    "Logo OFELIA en fond": {
        "en": "OFELIA logo as background",
        "es": "Logo OFELIA de fondo",
        "mg": "Logo OFELIA ho ambadika",
    },
    "Affiche le logo grandes lettres OFELIA centré sur chaque carte.": {
        "en": "Display the OFELIA large-letter logo centered on each card.",
        "es": "Muestra el logo OFELIA en grandes letras centrado en cada tarjeta.",
        "mg": "Aseho afovoany amin'ny karatra tsirairay ny logo OFELIA litera lehibe.",
    },
    "Photo du membre": {
        "en": "Member photo",
        "es": "Foto del miembro",
        "mg": "Sary an'ilay mpikambana",
    },
    "Affiche la photo en haut à gauche quand le membre en a une.": {
        "en": "Display the photo at the top-left when the member has one.",
        "es": "Muestra la foto arriba a la izquierda cuando el miembro tiene una.",
        "mg": "Aseho eo ambony havia ny sary raha manana izany ilay mpikambana.",
    },
    "Largeur (mm)": {
        "en": "Width (mm)", "es": "Ancho (mm)", "mg": "Sakany (mm)",
    },
    "Hauteur (mm)": {
        "en": "Height (mm)", "es": "Alto (mm)", "mg": "Halavany (mm)",
    },
    "Cumulé sur les lignes du titre.": {
        "en": "Cumulative over title lines.",
        "es": "Acumulado en las líneas del título.",
        "mg": "Manangona amin'ny andalan'ny lohateny.",
    },
    "Lignes de titre": {
        "en": "Title lines", "es": "Líneas de título", "mg": "Andalan'ny lohateny",
    },
    "Lignes d'auteurs": {
        "en": "Author lines", "es": "Líneas de autores", "mg": "Andalan'ny mpanoratra",
    },
    "Logo Ofelia": {
        "en": "Ofelia logo", "es": "Logo Ofelia", "mg": "Logo Ofelia",
    },
    # --- Settings sections (admin_views.FORMS labels) -----------------
    "Identité": {
        "en": "Identity", "es": "Identidad", "mg": "Mombamomba",
    },
    "Langues": {
        "en": "Languages", "es": "Idiomas", "mg": "Fiteny",
    },
    "Durées prêts & réservations": {
        "en": "Loan & reservation durations",
        "es": "Duración de préstamos y reservas",
        "mg": "Faharetan'ny fampindramana sy famandrihana",
    },
    "Impressions — Cartes membres": {
        "en": "Printing — Member cards",
        "es": "Impresiones — Tarjetas de miembro",
        "mg": "Fanontana — Karatra mpikambana",
    },
    "Impressions — Étiquettes codes Ofelia": {
        "en": "Printing — Ofelia code labels",
        "es": "Impresiones — Etiquetas códigos Ofelia",
        "mg": "Fanontana — Marika kaody Ofelia",
    },
    "Sources de métadonnées": {
        "en": "Metadata sources",
        "es": "Fuentes de metadatos",
        "mg": "Loharanon'ny metadata",
    },
    "Cartes membres : nombre par A4, photo, logo OFELIA": {
        "en": "Member cards: number per A4, photo, OFELIA logo",
        "es": "Tarjetas de miembro: número por A4, foto, logo OFELIA",
        "mg": "Karatra mpikambana : isa isaky ny A4, sary, logo OFELIA",
    },
    "Étiquettes codes Ofelia : dimensions, titre, logo": {
        "en": "Ofelia code labels: dimensions, title, logo",
        "es": "Etiquetas códigos Ofelia: dimensiones, título, logo",
        "mg": "Marika kaody Ofelia : haben'izany, lohateny, logo",
    },

    # --- FEAT-035 / settings_index -------------------------------------
    "Durée par défaut d'un prêt (jours)": {
        "en": "Default loan duration (days)",
        "es": "Duración predeterminada del préstamo (días)",
        "mg": "Faharetan'ny fampindramana mahazatra (andro)",
    },
    "Utilisée si ni la catégorie de document ni la catégorie de membre n'en définit une. Défaut : 21 jours (3 semaines).": {
        "en": "Used if neither the document category nor the member category defines one. Default: 21 days (3 weeks).",
        "es": "Se utiliza si ni la categoría de documento ni la categoría de miembro definen una. Predeterminado: 21 días (3 semanas).",
        "mg": "Ampiasaina raha tsy mamaritra izany ny sokajin'ny boky na ny sokajin'ny mpikambana. Mahazatra : 21 andro (herinandro 3).",
    },
    "Validité d'une réservation en attente (jours)": {
        "en": "Pending reservation validity (days)",
        "es": "Validez de una reserva pendiente (días)",
        "mg": "Faharetan'ny famandrihana miandry (andro)",
    },
    "Délai au-delà duquel une réservation pour laquelle aucun exemplaire ne s'est libéré expire automatiquement.": {
        "en": "Period after which a reservation for which no copy became available expires automatically.",
        "es": "Plazo tras el cual una reserva para la que ningún ejemplar quedó disponible expira automáticamente.",
        "mg": "Fe-potoana izay maharitra ny famandrihana izay tsy nahazoana boky malalaka dia tapitra ho azy.",
    },
    "Durée de mise de côté à retirer (jours)": {
        "en": "Pickup hold period (days)",
        "es": "Plazo de reserva para retirar (días)",
        "mg": "Faharetan'ny fanavahana mba ho zahana (andro)",
    },
    "Une fois un exemplaire mis de côté pour un membre, il a ce délai pour venir le retirer avant que la réservation ne bascule au membre suivant.": {
        "en": "Once a copy is held for a member, they have this period to pick it up before the reservation passes to the next member.",
        "es": "Una vez reservado un ejemplar para un miembro, éste dispone de este plazo para retirarlo antes de que la reserva pase al siguiente miembro.",
        "mg": "Rehefa voatokana ho an'ny mpikambana iray ny boky, dia manana izay fe-potoana izay izy mba haka azy alohan'ny hifindran'ny famandrihana amin'ny mpikambana manaraka.",
    },
    "Durée par défaut d'un prêt et délais de réservation": {
        "en": "Default loan duration and reservation periods",
        "es": "Duración predeterminada del préstamo y plazos de reserva",
        "mg": "Faharetan'ny fampindramana mahazatra sy ny fe-potoana famandrihana",
    },

    # --- FEAT-036 réservations / dashboard -----------------------------
    "Notification enregistrée pour %(m)s.": {
        "en": "Notification recorded for %(m)s.",
        "es": "Notificación registrada para %(m)s.",
        "mg": "Voarakitra ny fampahafantarana ho an'i %(m)s.",
    },
    "Ce membre a déjà été notifié.": {
        "en": "This member has already been notified.",
        "es": "Este miembro ya ha sido notificado.",
        "mg": "Efa nampahafantarina ity mpikambana ity.",
    },
    "Mis de côté pour %(member)s (%(card)s)": {
        "en": "Held for %(member)s (%(card)s)",
        "es": "Reservado para %(member)s (%(card)s)",
        "mg": "Natokana ho an'i %(member)s (%(card)s)",
    },
    "à retirer avant le %(d)s": {
        "en": "to pick up before %(d)s",
        "es": "a retirar antes del %(d)s",
        "mg": "alaina alohan'ny %(d)s",
    },
    "à retirer avant le": {
        "en": "to pick up before",
        "es": "a retirar antes del",
        "mg": "alaina alohan'ny",
    },
    "À retirer avant le": {
        "en": "To pick up before",
        "es": "A retirar antes del",
        "mg": "Alaina alohan'ny",
    },
    "à retirer": {
        "en": "to pick up", "es": "a retirar", "mg": "alaina",
    },
    "À retirer": {
        "en": "To pick up", "es": "A retirar", "mg": "Alaina",
    },
    "Liste d'attente": {
        "en": "Waiting list", "es": "Lista de espera", "mg": "Lisitry ny fiandrasana",
    },
    "Réservé le": {
        "en": "Reserved on", "es": "Reservado el", "mg": "Voafandrika tamin'ny",
    },
    "Annuler cette réservation ?": {
        "en": "Cancel this reservation?",
        "es": "¿Cancelar esta reserva?",
        "mg": "Foanana ity famandrihana ity ?",
    },
    "Notifier": {
        "en": "Notify", "es": "Notificar", "mg": "Mampahafantatra",
    },
    "Notifié": {
        "en": "Notified", "es": "Notificado", "mg": "Voampahafantatra",
    },
    "Notifications à faire": {
        "en": "Notifications to send",
        "es": "Notificaciones por enviar",
        "mg": "Fampahafantarana hatao",
    },
    "Réservations à relancer": {
        "en": "Reservations to follow up",
        "es": "Reservas por reactivar",
        "mg": "Famandrihana arenina",
    },
    "Contacter ces membres pour qu'ils viennent retirer leur livre avant qu'il ne reparte au suivant.": {
        "en": "Contact these members so they pick up their book before it passes to the next.",
        "es": "Contactar a estos miembros para que retiren su libro antes de que pase al siguiente.",
        "mg": "Antsoy ireto mpikambana ireto mba ho avy haka ny bokiny alohan'ny hifindran'izany amin'ny manaraka.",
    },
    "Expire aujourd'hui": {
        "en": "Expires today", "es": "Vence hoy", "mg": "Tapitra androany",
    },
    "Encore %(n)s jours": {
        "en": "%(n)s days left",
        "es": "Quedan %(n)s días",
        "mg": "Mbola %(n)s andro",
    },

    # --- FEAT-035 dashboard relances -----------------------------------
    "Relances à faire": {
        "en": "Reminders to send",
        "es": "Recordatorios por enviar",
        "mg": "Fampahatsiarovana hatao",
    },
    "Retard": {
        "en": "Overdue", "es": "Atraso", "mg": "Tara",
    },
    "Voir tout": {
        "en": "View all", "es": "Ver todo", "mg": "Hijery rehetra",
    },
    "voir tout": {
        "en": "view all", "es": "ver todo", "mg": "hijery rehetra",
    },
    "+%(n)s autres": {
        "en": "+%(n)s others",
        "es": "+%(n)s otros",
        "mg": "+%(n)s hafa",
    },

    # --- BUG-014 / FEAT-037 ------------------------------------------
    "Valider": {
        "en": "Submit", "es": "Validar", "mg": "Hankato",
    },
    "Scanner le code-barres": {
        "en": "Scan the barcode",
        "es": "Escanear el código de barras",
        "mg": "Hi-scan ny code-barres",
    },
    "Photo actuelle": {
        "en": "Current photo", "es": "Foto actual", "mg": "Sary amin'izao fotoana",
    },
}


def main() -> None:
    total = 0
    for lang in ("en", "es", "mg"):
        po_file = ROOT / lang / "LC_MESSAGES" / "django.po"
        # Patch process_file's TRANSLATIONS expectation via globals
        _globals["TRANSLATIONS"] = TRANSLATIONS
        replaced, fuzzy_removed = process_file(po_file, lang)
        print(f"  {lang}: {replaced} traductions appliquées, {fuzzy_removed} fuzzy supprimés")
        total += replaced
    print(f"\nTotal : {total} entrées remplacées sur les 3 langues.")


if __name__ == "__main__":
    main()
