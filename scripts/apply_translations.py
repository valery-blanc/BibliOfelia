"""Applique des traductions aux 4 .po de BibliOfelia (FEAT-031 + Sprint 9).

Usage : `python scripts/apply_translations.py`.
Ne touche que les msgid présents dans TRANSLATIONS. Supprime les marqueurs
`fuzzy` quand on met à jour une entrée.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parent.parent / "locale"

# {msgid: {"en": "...", "es": "...", "mg": "..."}}
# FR garde le msgid comme msgstr (pas besoin de fournir).
TRANSLATIONS = {
    "Enrichissement métadonnées": {
        "en": "Metadata enrichment",
        "es": "Enriquecimiento de metadatos",
        "mg": "Fanatsarana metadata",
    },
    "Compléter ou écraser les métadonnées du catalogue depuis OpenLibrary, Google Books, BNF et BNE — en tâche de fond.": {
        "en": "Complete or overwrite catalog metadata from OpenLibrary, Google Books, BNF and BNE — as a background job.",
        "es": "Completar o sobrescribir los metadatos del catálogo desde OpenLibrary, Google Books, BNF y BNE — como tarea en segundo plano.",
        "mg": "Manatsara na manolo ny metadata-n'ny katalaogy avy amin'ny OpenLibrary, Google Books, BNF sy BNE — amin'ny asa aoriana.",
    },
    "Lancer un enrichissement": {
        "en": "Launch an enrichment", "es": "Iniciar un enriquecimiento",
        "mg": "Manomboka fanatsarana",
    },
    "Compléter seulement les champs vides": {
        "en": "Fill empty fields only", "es": "Completar solo los campos vacíos",
        "mg": "Fenoy ireo saha banga ihany",
    },
    "Écraser les données locales avec les sources externes": {
        "en": "Overwrite local data with external sources",
        "es": "Sobrescribir datos locales con fuentes externas",
        "mg": "Soloy amin'ny loharano ivelany ny angona an-toerana",
    },
    "Sources à interroger": {
        "en": "Sources to query", "es": "Fuentes a consultar",
        "mg": "Loharano hanontaniana",
    },
    "Toutes les notices avec un ISBN": {
        "en": "All records with an ISBN", "es": "Todas las fichas con un ISBN",
        "mg": "Ny rakitra rehetra manana ISBN",
    },
    "Notices sans auteur": {
        "en": "Records without author", "es": "Fichas sin autor",
        "mg": "Rakitra tsy misy mpanoratra",
    },
    "Notices sans éditeur": {
        "en": "Records without publisher", "es": "Fichas sin editor",
        "mg": "Rakitra tsy misy mpanonta",
    },
    "Liste d'ISBN (un par ligne)": {
        "en": "ISBN list (one per line)", "es": "Lista de ISBN (uno por línea)",
        "mg": "Lisitr'ISBN (iray isaky ny andalana)",
    },
    "Saisissez un ISBN par ligne (utilisé uniquement si « Liste d'ISBN » est sélectionnée).": {
        "en": "Enter one ISBN per line (used only if \"ISBN list\" is selected).",
        "es": "Introduzca un ISBN por línea (utilizado solo si se selecciona «Lista de ISBN»).",
        "mg": "Atao iray isaky ny andalana ny ISBN (ampiasaina raha voafidy ny « Lisitr'ISBN » ihany).",
    },
    "Lancer": {"en": "Launch", "es": "Iniciar", "mg": "Manomboka"},
    "Tag…": {"en": "Tag…", "es": "Etiqueta…", "mg": "Marika…"},
    "Sous-titre": {"en": "Subtitle", "es": "Subtítulo", "mg": "Lohateny faharoa"},
    "Aucune source activée.": {
        "en": "No source enabled.", "es": "Ninguna fuente activada.",
        "mg": "Tsy misy loharano voafantina.",
    },
    "Configurer les sources de métadonnées": {
        "en": "Configure metadata sources", "es": "Configurar fuentes de metadatos",
        "mg": "Hamboatra ny loharanon'ny metadata",
    },
    "Historique": {"en": "History", "es": "Historial", "mg": "Tantara"},
    "Lancé le": {"en": "Started at", "es": "Iniciado el", "mg": "Natomboka tamin'ny"},
    "Traitées": {"en": "Processed", "es": "Procesadas", "mg": "Voakarakara"},
    "Mises à jour": {"en": "Updated", "es": "Actualizadas", "mg": "Nohavaozina"},
    "Erreurs": {"en": "Errors", "es": "Errores", "mg": "Tsy fetezana"},
    "Détails": {"en": "Details", "es": "Detalles", "mg": "Antsipiriany"},
    "Aucun enrichissement lancé.": {
        "en": "No enrichment launched.", "es": "Ningún enriquecimiento iniciado.",
        "mg": "Tsy nisy fanatsarana natomboka.",
    },
    "Champs modifiés (← source)": {
        "en": "Modified fields (← source)", "es": "Campos modificados (← fuente)",
        "mg": "Saha novaina (← loharano)",
    },
    "Couverture": {"en": "Cover", "es": "Portada", "mg": "Sarin'ny boky"},
    "Inchangées": {"en": "Unchanged", "es": "Sin cambios", "mg": "Tsy nivaina"},
    "Sources": {"en": "Sources", "es": "Fuentes", "mg": "Loharano"},
    "Rapport": {"en": "Report", "es": "Informe", "mg": "Tatitra"},
    "Terminé le": {"en": "Finished at", "es": "Finalizado el", "mg": "Vita tamin'ny"},
    # Suppressions / désactivation
    "Désactiver": {"en": "Deactivate", "es": "Desactivar", "mg": "Avao"},
    "Réactiver": {"en": "Reactivate", "es": "Reactivar", "mg": "Avereno mavitrika"},
    "Supprimer la sélection": {
        "en": "Delete selection", "es": "Eliminar selección",
        "mg": "Fafao ny safidy",
    },
    "Tout cocher": {"en": "Select all", "es": "Seleccionar todo", "mg": "Marihina avokoa"},
    "Suppression en masse de notices": {
        "en": "Bulk delete records", "es": "Eliminación masiva de fichas",
        "mg": "Famafana an-tapitrisany ny rakitra",
    },
    "Aucune notice sélectionnée.": {
        "en": "No record selected.", "es": "Ninguna ficha seleccionada.",
        "mg": "Tsy misy rakitra voafantina.",
    },
    "Retour au catalogue": {
        "en": "Back to catalog", "es": "Volver al catálogo",
        "mg": "Miverina any amin'ny katalaogy",
    },
    "Notices à supprimer": {
        "en": "Records to delete", "es": "Fichas a eliminar",
        "mg": "Rakitra hofafana",
    },
    "Réservations actives": {
        "en": "Active reservations", "es": "Reservas activas",
        "mg": "Famandrihana mavitrika",
    },
    "Confirmer la suppression": {
        "en": "Confirm deletion", "es": "Confirmar eliminación",
        "mg": "Hamafiso ny famafana",
    },
    # ----- Dashboard (core/dashboard.html) -----
    "Bonjour,": {"en": "Hello,", "es": "Hola,", "mg": "Manao ahoana,"},
    "Voici ce qui se passe à la bibliothèque aujourd'hui.": {
        "en": "Here's what's happening in the library today.",
        "es": "Esto es lo que sucede en la biblioteca hoy.",
        "mg": "Izay no mitranga ao amin'ny tranomboky androany.",
    },
    "Scanner une carte ou un livre": {
        "en": "Scan a card or a book",
        "es": "Escanear una tarjeta o un libro",
        "mg": "Manaova scan amin'ny karatra na boky",
    },
    "Caisse rapide — prêt, retour, recherche par code-barres": {
        "en": "Quick desk — loan, return, barcode search",
        "es": "Caja rápida — préstamo, devolución, búsqueda por código de barras",
        "mg": "Caisse haingana — fampindramana, famerenana, fikarohana amin'ny barcode",
    },
    "Actions rapides": {
        "en": "Quick actions", "es": "Acciones rápidas",
        "mg": "Hetsika haingana",
    },
    "Nouveau prêt": {"en": "New loan", "es": "Nuevo préstamo", "mg": "Fampindramana vaovao"},
    "Retour": {"en": "Return", "es": "Devolución", "mg": "Famerenana"},
    "Nouvelle notice": {"en": "New record", "es": "Nueva ficha", "mg": "Rakitra vaovao"},
    "Nouveau membre": {"en": "New member", "es": "Nuevo miembro", "mg": "Mpikambana vaovao"},
    "Réservations prêtes": {
        "en": "Ready reservations", "es": "Reservas listas",
        "mg": "Famandrihana vonona",
    },
    "Prêts en retard": {
        "en": "Overdue loans", "es": "Préstamos vencidos",
        "mg": "Fampindramana tara",
    },
    "Prêts en cours": {
        "en": "Active loans", "es": "Préstamos activos",
        "mg": "Fampindramana mandeha",
    },
    "Membres actifs (mois)": {
        "en": "Active members (month)", "es": "Miembros activos (mes)",
        "mg": "Mpikambana mavitrika (volana)",
    },
    "Membres actifs (année)": {
        "en": "Active members (year)", "es": "Miembros activos (año)",
        "mg": "Mpikambana mavitrika (taona)",
    },
    "Membres inscrits": {
        "en": "Registered members", "es": "Miembros registrados",
        "mg": "Mpikambana voasoratra anarana",
    },
    "Notices ajoutées (mois)": {
        "en": "Records added (month)", "es": "Fichas añadidas (mes)",
        "mg": "Rakitra nampiana (volana)",
    },
    "Notices ajoutées (année)": {
        "en": "Records added (year)", "es": "Fichas añadidas (año)",
        "mg": "Rakitra nampiana (taona)",
    },
    "Exemplaires ajoutés (mois)": {
        "en": "Copies added (month)", "es": "Ejemplares añadidos (mes)",
        "mg": "Kopia nampiana (volana)",
    },
    "Tendance — 30 derniers jours": {
        "en": "Trend — last 30 days", "es": "Tendencia — últimos 30 días",
        "mg": "Fironana — 30 andro farany",
    },
    "Top 10 ce mois-ci": {
        "en": "Top 10 this month", "es": "Top 10 este mes",
        "mg": "10 voalohany volana ity",
    },
    "Aucun prêt ce mois.": {
        "en": "No loan this month.", "es": "Ningún préstamo este mes.",
        "mg": "Tsy nisy fampindramana volana ity.",
    },
    "Pas encore de données": {
        "en": "No data yet", "es": "Aún no hay datos",
        "mg": "Mbola tsy misy angona",
    },
    "Pas encore de prêts enregistrés sur la période.": {
        "en": "No loans recorded for the period.",
        "es": "Aún no hay préstamos registrados en el período.",
        "mg": "Mbola tsy nisy fampindramana voasoratra amin'ny vanim-potoana.",
    },
    "État système": {"en": "System status", "es": "Estado del sistema", "mg": "Toetry ny rafitra"},
    "Version": {"en": "Version", "es": "Versión", "mg": "Version"},
    "Espace disque": {"en": "Disk space", "es": "Espacio en disco", "mg": "Habetsahan'ny disque"},
    "Dernière sauvegarde": {
        "en": "Last backup", "es": "Última copia de seguridad",
        "mg": "Backup farany",
    },
    "Réseau": {"en": "Network", "es": "Red", "mg": "Tambajotra"},
    "Activité": {"en": "Activity", "es": "Actividad", "mg": "Asa"},
    "Livres en attente": {
        "en": "Pending books", "es": "Libros pendientes", "mg": "Boky miandry",
    },
    "Aucune": {"en": "None", "es": "Ninguna", "mg": "Tsy misy"},
    "> 24h": {"en": "> 24h", "es": "> 24h", "mg": "> 24h"},
    "Sections principales": {
        "en": "Main sections", "es": "Secciones principales", "mg": "Fizarana lehibe",
    },
    "Sections": {"en": "Sections", "es": "Secciones", "mg": "Fizarana"},
    "Recherche globale": {
        "en": "Global search", "es": "Búsqueda global", "mg": "Fikarohana ankapobeny",
    },
    "Titre, auteur, ISBN, n° de carte…": {
        "en": "Title, author, ISBN, card number…",
        "es": "Título, autor, ISBN, n.º de tarjeta…",
        "mg": "Lohateny, mpanoratra, ISBN, laharan-karatra…",
    },
    "Prêts par jour": {
        "en": "Loans per day", "es": "Préstamos por día", "mg": "Fampindramana isan'andro",
    },
    # ----- Tile strip (tuiles de navigation) -----
    "Accueil": {"en": "Home", "es": "Inicio", "mg": "Fandraisana"},
    "Catalogue": {"en": "Catalog", "es": "Catálogo", "mg": "Katalaogy"},
    "Membres": {"en": "Members", "es": "Miembros", "mg": "Mpikambana"},
    "Prêt": {"en": "Loan", "es": "Préstamo", "mg": "Fampindramana"},
    "Réservations": {"en": "Reservations", "es": "Reservas", "mg": "Famandrihana"},
    "Avancé": {"en": "Advanced", "es": "Avanzado", "mg": "Mandroso"},
    "Scanner": {"en": "Scanner", "es": "Escáner", "mg": "Scanner"},
    "Prêter un livre": {
        "en": "Lend a book", "es": "Prestar un libro", "mg": "Mampindrana boky",
    },
    "Enregistrer un nouveau prêt": {
        "en": "Record a new loan", "es": "Registrar un nuevo préstamo",
        "mg": "Manoratra fampindramana vaovao",
    },
    "Enregistrer un retour": {
        "en": "Record a return", "es": "Registrar una devolución",
        "mg": "Manoratra famerenana",
    },
    "Ajouter un livre": {
        "en": "Add a book", "es": "Añadir un libro", "mg": "Manampy boky",
    },
    "Tous les livres et leurs exemplaires": {
        "en": "All books and their copies",
        "es": "Todos los libros y sus ejemplares",
        "mg": "Ny boky rehetra sy ny kopiany",
    },
    "Inscrire un lecteur": {
        "en": "Register a reader", "es": "Registrar un lector",
        "mg": "Manoratra mpamaky",
    },
    "Lecteurs inscrits, cartes et historique": {
        "en": "Registered readers, cards and history",
        "es": "Lectores registrados, tarjetas e historial",
        "mg": "Mpamaky voasoratra, karatra sy tantara",
    },
    "Impression, rapports, paramètres": {
        "en": "Printing, reports, settings",
        "es": "Impresión, informes, parámetros",
        "mg": "Fanontana, tatitra, parameter",
    },
    "Notices": {"en": "Records", "es": "Fichas", "mg": "Rakitra"},
    "Exemplaires": {"en": "Copies", "es": "Ejemplares", "mg": "Kopia"},
    # ----- Topbar / login -----
    "Bibliothèque communautaire": {
        "en": "Community library", "es": "Biblioteca comunitaria",
        "mg": "Tranomboky iombonana",
    },
    "Connectez-vous à votre bibliothèque": {
        "en": "Sign in to your library", "es": "Inicie sesión en su biblioteca",
        "mg": "Midira amin'ny tranombokinao",
    },
    "Identifiants invalides. Veuillez réessayer.": {
        "en": "Invalid credentials. Please try again.",
        "es": "Credenciales no válidas. Inténtelo de nuevo.",
        "mg": "Diso ny tonon-baovao. Andramo indray.",
    },
    "Menu utilisateur": {
        "en": "User menu", "es": "Menú de usuario", "mg": "Karazana mpampiasa",
    },
    # ----- /loans/lend/ -----
    "1 · Membre": {"en": "1 · Member", "es": "1 · Miembro", "mg": "1 · Mpikambana"},
    "2 · Livres": {"en": "2 · Books", "es": "2 · Libros", "mg": "2 · Boky"},
    "3 · Confirmer": {"en": "3 · Confirm", "es": "3 · Confirmar", "mg": "3 · Hamafiso"},
    "Scanner la carte": {
        "en": "Scan the card", "es": "Escanear la tarjeta",
        "mg": "Manaova scan amin'ny karatra",
    },
    "Scanner un livre": {
        "en": "Scan a book", "es": "Escanear un libro",
        "mg": "Manaova scan amin'ny boky",
    },
    "Panier": {"en": "Cart", "es": "Carrito", "mg": "Vata"},
    "Membre": {"en": "Member", "es": "Miembro", "mg": "Mpikambana"},
    "Vider": {"en": "Clear", "es": "Vaciar", "mg": "Foano"},
    "À temps": {"en": "On time", "es": "A tiempo", "mg": "Ara-potoana"},
    "Pos.": {"en": "Pos.", "es": "Pos.", "mg": "Pos."},
    "Exp.": {"en": "Exp.", "es": "Exp.", "mg": "Exp."},
    # ----- /loans/return/ -----
    "Scanner un livre à rendre": {
        "en": "Scan a book to return",
        "es": "Escanear un libro para devolver",
        "mg": "Manaova scan amin'ny boky averina",
    },
    # ----- /loans/reservations/ -----
    "Prêtes à retirer": {
        "en": "Ready for pickup", "es": "Listas para retirar",
        "mg": "Vonona haka",
    },
    "Prête": {"en": "Ready", "es": "Lista", "mg": "Vonona"},
    "réservé le": {"en": "reserved on", "es": "reservado el", "mg": "voafandrika ny"},
    # ----- /advanced/ -----
    "Outils complémentaires": {
        "en": "Additional tools", "es": "Herramientas complementarias",
        "mg": "Fitaovana fanampiny",
    },
    "Petit guide pour démarrer": {
        "en": "Quick start guide", "es": "Guía rápida para empezar",
        "mg": "Torolalana fohy hanombohana",
    },
    # ----- /admin/diagnostics/ et settings -----
    "État du système, sauvegardes, planificateur": {
        "en": "System status, backups, scheduler",
        "es": "Estado del sistema, copias de seguridad, planificador",
        "mg": "Toetry ny rafitra, backup, mpandamina",
    },
    "Nom de la bibliothèque, contact, fuseau horaire": {
        "en": "Library name, contact, time zone",
        "es": "Nombre de la biblioteca, contacto, zona horaria",
        "mg": "Anaran'ny tranomboky, contact, faritry ny ora",
    },
    "Langues actives et langue par défaut": {
        "en": "Active languages and default language",
        "es": "Idiomas activos y idioma predeterminado",
        "mg": "Fiteny mavitrika sy fiteny default",
    },
    "Fréquence locale et destination cloud (rclone)": {
        "en": "Local frequency and cloud destination (rclone)",
        "es": "Frecuencia local y destino en la nube (rclone)",
        "mg": "Tetiandro an-toerana sy toerana rakitra (rclone)",
    },
    "Format des étiquettes codes Ofelia": {
        "en": "Format of Ofelia code labels",
        "es": "Formato de etiquetas con códigos Ofelia",
        "mg": "Endriky ny étiquette code Ofelia",
    },
    "Réseau privé pour accès à distance": {
        "en": "Private network for remote access",
        "es": "Red privada para acceso remoto",
        "mg": "Tambajotra manokana ho an'ny fidirana lavitra",
    },
    "Paramètres à saisir dans l'application mobile pour qu'elle se connecte à cette box.": {
        "en": "Settings to enter in the mobile app so it connects to this box.",
        "es": "Parámetros a introducir en la aplicación móvil para que se conecte a esta caja.",
        "mg": "Parameter hampidirina ao amin'ny rindranasa finday mba hifandraisany amin'ity boaty ity.",
    },
    "Complète le catalogue depuis OpenLibrary, Google Books, BNF et BNE.": {
        "en": "Complete the catalog from OpenLibrary, Google Books, BNF and BNE.",
        "es": "Completar el catálogo desde OpenLibrary, Google Books, BNF y BNE.",
        "mg": "Mameno ny katalaogy avy amin'ny OpenLibrary, Google Books, BNF sy BNE.",
    },
    # ----- Sources de metadata (formulaire) -----
    "Clé API Google Books": {
        "en": "Google Books API key", "es": "Clave API de Google Books",
        "mg": "Fanalahidy API Google Books",
    },
    "Obligatoire pour activer Google Books. Gratuite via Google Cloud Console.": {
        "en": "Required to enable Google Books. Free via Google Cloud Console.",
        "es": "Obligatorio para activar Google Books. Gratuita en Google Cloud Console.",
        "mg": "Ilaina hampandeha ny Google Books. Maimaim-poana amin'ny Google Cloud Console.",
    },
    "Google Books": {"en": "Google Books", "es": "Google Books", "mg": "Google Books"},
    "BNF (livres FR)": {
        "en": "BNF (French books)", "es": "BNF (libros FR)",
        "mg": "BNF (boky FR)",
    },
    "BNE (livres ES)": {
        "en": "BNE (Spanish books)", "es": "BNE (libros ES)",
        "mg": "BNE (boky ES)",
    },
    # ----- EnrichmentJob / state -----
    "Compléter les champs vides uniquement": {
        "en": "Fill empty fields only", "es": "Completar solo los campos vacíos",
        "mg": "Fenoy ireo saha banga ihany",
    },
    "Écraser avec les données externes": {
        "en": "Overwrite with external data",
        "es": "Sobrescribir con datos externos",
        "mg": "Soloy amin'ny angona ivelany",
    },
    "Terminé": {"en": "Finished", "es": "Finalizado", "mg": "Vita"},
    "Échec": {"en": "Failed", "es": "Fallido", "mg": "Tsy nahomby"},
    "Auto-détection": {"en": "Auto-detect", "es": "Detección automática", "mg": "Auto-détection"},
    "Ouverte": {"en": "Open", "es": "Abierta", "mg": "Misokatra"},
    "EAN13": {"en": "EAN13", "es": "EAN13", "mg": "EAN13"},
    "item scanné": {"en": "scanned item", "es": "ítem escaneado", "mg": "akora voakaroka"},
    "items scannés": {"en": "scanned items", "es": "ítems escaneados", "mg": "akora voakaroka"},
    "Annulé": {"en": "Cancelled", "es": "Cancelado", "mg": "Nofoanana"},
    "Carte membre": {"en": "Member card", "es": "Tarjeta de miembro", "mg": "Karatra mpikambana"},
    "session de scan": {"en": "scan session", "es": "sesión de escaneo", "mg": "session-na scan"},
    "sessions de scan": {"en": "scan sessions", "es": "sesiones de escaneo", "mg": "session-na scan"},
    "enrichissement métadonnées": {
        "en": "metadata enrichment", "es": "enriquecimiento de metadatos",
        "mg": "fanatsarana metadata",
    },
    "enrichissements métadonnées": {
        "en": "metadata enrichments", "es": "enriquecimientos de metadatos",
        "mg": "fanatsarana metadata",
    },
    "Enrichissement #%(id)s lancé. Suivez l'avancement ici.": {
        "en": "Enrichment #%(id)s launched. Follow progress here.",
        "es": "Enriquecimiento #%(id)s iniciado. Siga el progreso aquí.",
        "mg": "Fanatsarana #%(id)s natomboka. Araho eto ny fivoarana.",
    },
    "Enrichissement #%(id)s": {
        "en": "Enrichment #%(id)s", "es": "Enriquecimiento #%(id)s",
        "mg": "Fanatsarana #%(id)s",
    },
    "Enrichissement": {"en": "Enrichment", "es": "Enriquecimiento", "mg": "Fanatsarana"},
    "Total": {"en": "Total", "es": "Total", "mg": "Totaly"},
    "Mode": {"en": "Mode", "es": "Modo", "mg": "Mode"},
    "Erreur": {"en": "Error", "es": "Error", "mg": "Hadisoana"},
    "Notice": {"en": "Record", "es": "Ficha", "mg": "Rakitra"},
    # ----- Misc / messages -----
    "Vous ne pouvez pas supprimer votre propre compte.": {
        "en": "You cannot delete your own account.",
        "es": "No puede eliminar su propia cuenta.",
        "mg": "Tsy azonao fafana ny kaonty manokananao.",
    },
    "Impossible : il doit rester au moins un superadmin actif.": {
        "en": "Impossible: at least one active superadmin must remain.",
        "es": "Imposible: debe permanecer al menos un superadmin activo.",
        "mg": "Tsy azo atao : tsy maintsy mijanona iray farafahakeliny ny superadmin mavitrika.",
    },
    "Compte %(u)s supprimé.": {
        "en": "Account %(u)s deleted.", "es": "Cuenta %(u)s eliminada.",
        "mg": "Voafafa ny kaonty %(u)s.",
    },
    "Exemplaire supprimé.": {
        "en": "Copy deleted.", "es": "Ejemplar eliminado.",
        "mg": "Voafafa ny kopia.",
    },
    "%(n)s notice(s) supprimée(s).": {
        "en": "%(n)s record(s) deleted.", "es": "%(n)s ficha(s) eliminada(s).",
        "mg": "%(n)s rakitra voafafa.",
    },
    "Usager %(status)s : prêt impossible.": {
        "en": "Member %(status)s: loan not possible.",
        "es": "Usuario %(status)s: préstamo imposible.",
        "mg": "Mpikambana %(status)s : tsy azo atao ny fampindramana.",
    },
    "Usager désactivé.": {
        "en": "Member deactivated.", "es": "Usuario desactivado.",
        "mg": "Natsahatra ny mpikambana.",
    },
    "Usager réactivé.": {
        "en": "Member reactivated.", "es": "Usuario reactivado.",
        "mg": "Naverina mavitrika ny mpikambana.",
    },
    "Usager %(n)s supprimé.": {
        "en": "Member %(n)s deleted.", "es": "Usuario %(n)s eliminado.",
        "mg": "Voafafa ny mpikambana %(n)s.",
    },
    "Supprimer le compte": {
        "en": "Delete account", "es": "Eliminar cuenta", "mg": "Fafao ny kaonty",
    },
    "Confirmez-vous la suppression du compte <strong>%(username)s</strong> ?": {
        "en": "Confirm deletion of account <strong>%(username)s</strong>?",
        "es": "¿Confirma la eliminación de la cuenta <strong>%(username)s</strong>?",
        "mg": "Hamafiso ve ny famafana ny kaonty <strong>%(username)s</strong> ?",
    },
    "Historique conservé (référence remplacée par « —»)": {
        "en": "History kept (reference replaced by \"—\")",
        "es": "Historial conservado (referencia sustituida por «—»)",
        "mg": "Voatahiry ny tantara (« — » no nosoloina ny fanondroana)",
    },
    "prêt(s) gérés": {
        "en": "loan(s) handled", "es": "préstamo(s) gestionado(s)",
        "mg": "fampindramana voatantana",
    },
    "notice(s) créée(s)": {
        "en": "record(s) created", "es": "ficha(s) creada(s)",
        "mg": "rakitra noforonina",
    },
    "session(s) de scan OfeliaScan": {
        "en": "OfeliaScan scan session(s)", "es": "sesión(es) de escaneo OfeliaScan",
        "mg": "session-na scan OfeliaScan",
    },
    "Bibliothécaires, contributeurs, administration": {
        "en": "Librarians, contributors, administration",
        "es": "Bibliotecarios, contribuidores, administración",
        "mg": "Mpitan-tranomboky, mpandray anjara, fitantanana",
    },
    "Suppression en masse": {
        "en": "Bulk delete", "es": "Eliminación masiva",
        "mg": "Famafana an-tapitrisany",
    },
    "Confirmez-vous la suppression de « %(title)s » ? Cette action est irréversible.": {
        "en": "Confirm deletion of \"%(title)s\"? This action is irreversible.",
        "es": "¿Confirma la eliminación de «%(title)s»? Esta acción es irreversible.",
        "mg": "Hamafiso ve ny famafana an'ny « %(title)s » ? Tsy azo averina io hetsika io.",
    },
    "Notice catalogue": {
        "en": "Catalog record", "es": "Ficha de catálogo", "mg": "Rakitr'ny katalaogy",
    },
    "Pilonner cet exemplaire ? Il restera en base avec le statut « Pilonné ».": {
        "en": "Discard this copy? It will remain in the database with status \"Discarded\".",
        "es": "¿Pilonar este ejemplar? Permanecerá en la base con estado «Pilonado».",
        "mg": "Hofafana ity kopia ity? Hijanona ao amin'ny tahirin-tsoratra miaraka amin'ny toetra « Voafafa » izy.",
    },
    "Pilonner": {"en": "Discard", "es": "Pilonar", "mg": "Hofafana"},
    "Supprimer définitivement cet exemplaire ? Cette action est irréversible.": {
        "en": "Permanently delete this copy? This action is irreversible.",
        "es": "¿Eliminar definitivamente este ejemplar? Esta acción es irreversible.",
        "mg": "Hofafana tanteraka ity kopia ity? Tsy azo averina io hetsika io.",
    },
    "Tous types": {"en": "All types", "es": "Todos los tipos", "mg": "Karazana rehetra"},
    "Toutes langues": {"en": "All languages", "es": "Todos los idiomas", "mg": "Fiteny rehetra"},
    "notice(s) sélectionnée(s)": {
        "en": "record(s) selected", "es": "ficha(s) seleccionada(s)",
        "mg": "rakitra voafantina",
    },
    "Ex.": {"en": "Cop.", "es": "Ej.", "mg": "Kop."},
    "ex.": {"en": "cop.", "es": "ej.", "mg": "kop."},
    "Scanner un code Ofelia": {
        "en": "Scan an Ofelia code", "es": "Escanear un código Ofelia",
        "mg": "Manaova scan amin'ny code Ofelia",
    },
    "Sessions de récolement et historique": {
        "en": "Inventory sessions and history",
        "es": "Sesiones de inventario e historial",
        "mg": "Session-na fanisana sy tantara",
    },
    "Supprimer l'usager": {
        "en": "Delete member", "es": "Eliminar usuario", "mg": "Fafao ny mpikambana",
    },
    "Confirmez-vous la suppression de l'usager <strong>%(name)s</strong> ? Cette action est irréversible.": {
        "en": "Confirm deletion of member <strong>%(name)s</strong>? This action is irreversible.",
        "es": "¿Confirma la eliminación del usuario <strong>%(name)s</strong>? Esta acción es irreversible.",
        "mg": "Hamafiso ve ny famafana ny mpikambana <strong>%(name)s</strong> ? Tsy azo averina io hetsika io.",
    },
    "Impacts": {"en": "Impacts", "es": "Impactos", "mg": "Vokany"},
    "prêt(s) en cours seront clôturés (exemplaires libérés) :": {
        "en": "active loan(s) will be closed (copies released):",
        "es": "préstamo(s) activo(s) serán cerrados (ejemplares liberados):",
        "mg": "fampindramana mandeha ho ovaina (afaka ny kopia) :",
    },
    "réservation(s) active(s) seront annulées.": {
        "en": "active reservation(s) will be cancelled.",
        "es": "reserva(s) activa(s) serán canceladas.",
        "mg": "famandrihana mavitrika hofoanana.",
    },
    "prêt(s) passé(s) seront supprimés (historique perdu).": {
        "en": "past loan(s) will be deleted (history lost).",
        "es": "préstamo(s) pasado(s) serán eliminados (historial perdido).",
        "mg": "fampindramana lasa hofafana (very ny tantara).",
    },
    "compte(s) rattaché(s) verront leur lien rompu :": {
        "en": "linked account(s) will have their link broken:",
        "es": "cuenta(s) vinculada(s) tendrán su enlace roto:",
        "mg": "kaonty mifandray ho tapaka :",
    },
    "Aucun impact : usager sans prêt, réservation ni dépendant.": {
        "en": "No impact: member with no loan, reservation or dependent.",
        "es": "Sin impacto: usuario sin préstamos, reservas ni dependientes.",
        "mg": "Tsy misy vokany : mpikambana tsy manana fampindramana, famandrihana na zanaka.",
    },
    "Actifs ce mois": {
        "en": "Active this month", "es": "Activos este mes",
        "mg": "Mavitrika volana ity",
    },
    "Nouveaux ce mois": {
        "en": "New this month", "es": "Nuevos este mes",
        "mg": "Vaovao volana ity",
    },
    "Aucun membre ne correspond.": {
        "en": "No member matches.", "es": "Ningún miembro coincide.",
        "mg": "Tsy misy mpikambana mifanaraka.",
    },
    "Sélectionnez les usagers puis générez la planche PDF": {
        "en": "Select members then generate the PDF sheet",
        "es": "Seleccione los usuarios y genere la lámina PDF",
        "mg": "Safidio ireo mpikambana dia mamorona ny takelaka PDF",
    },
    "Sélectionnez les exemplaires à imprimer puis générez le PDF": {
        "en": "Select copies to print then generate the PDF",
        "es": "Seleccione los ejemplares a imprimir y genere el PDF",
        "mg": "Safidio ireo kopia atao printy dia mamorona ny PDF",
    },
    "Usagers et exemplaires sans activité récente": {
        "en": "Members and copies without recent activity",
        "es": "Usuarios y ejemplares sin actividad reciente",
        "mg": "Mpikambana sy kopia tsy nanao asa farany",
    },
    "Listes imprimables, exports CSV et rapport annuel PDF.": {
        "en": "Printable lists, CSV exports and annual PDF report.",
        "es": "Listas imprimibles, exportaciones CSV e informe anual PDF.",
        "mg": "Lisitra azo atao printy, export CSV sy tatitra isan-taona PDF.",
    },
    "Retards de plus de 7 jours par défaut": {
        "en": "Overdue more than 7 days by default",
        "es": "Retrasos de más de 7 días por defecto",
        "mg": "Fahatarana mihoatra ny 7 andro amin'ny default",
    },
    "Liste de relance pour les usagers": {
        "en": "Reminder list for members",
        "es": "Lista de recordatorio para usuarios",
        "mg": "Lisitra fampahatsiahivana ho an'ireo mpikambana",
    },
    "Usagers et exemplaires inactifs": {
        "en": "Inactive members and copies",
        "es": "Usuarios y ejemplares inactivos",
        "mg": "Mpikambana sy kopia tsy mavitrika",
    },
    "Les prêts en cours seront marqués « Perdu » et les réservations actives seront annulées.": {
        "en": "Active loans will be marked \"Lost\" and active reservations will be cancelled.",
        "es": "Los préstamos activos se marcarán «Perdidos» y las reservas activas se cancelarán.",
        "mg": "Hosoratana « Very » ny fampindramana mbola misy ary hofoanana ny famandrihana mavitrika.",
    },
}

def quote_po(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


_STR_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')
_ESCAPES = {"\\\\": "\\", '\\"': '"', "\\n": "\n", "\\t": "\t", "\\r": "\r"}


def _unescape(s: str) -> str:
    """Unescape uniquement les séquences \\X. Préserve l'UTF-8 tel quel."""
    out = []
    i = 0
    while i < len(s):
        if s[i] == "\\" and i + 1 < len(s):
            pair = s[i:i + 2]
            out.append(_ESCAPES.get(pair, pair))
            i += 2
        else:
            out.append(s[i])
            i += 1
    return "".join(out)


def unquote_po(raw: str) -> str:
    """Concatène toutes les "..." du raw et applique l'unescape POSIX."""
    return "".join(_unescape(p) for p in _STR_RE.findall(raw))


def process_file(po_file: Path, lang: str) -> tuple[int, int]:
    """Pour chaque msgid recherché, remplace la/les ligne(s) msgstr qui suivent.

    Stratégie simple : on scanne ligne par ligne. Pour chaque ligne
    ``msgid "..."`` qui matche un msgid de TRANSLATIONS (single-line ou
    multi-line), on remplace le bloc msgstr qui suit par une ligne unique.
    """
    lines = po_file.read_text(encoding="utf-8").splitlines(keepends=True)
    out: list[str] = []
    i = 0
    replaced = 0
    fuzzy_removed = 0

    while i < len(lines):
        line = lines[i]
        if line.startswith("msgid "):
            # Reconstituer le msgid complet (multi-lignes possibles)
            msgid_start = i
            i += 1
            while i < len(lines) and lines[i].startswith('"'):
                i += 1
            msgid_raw = lines[msgid_start][len("msgid "):] + "".join(
                lines[msgid_start + 1:i]
            )
            msgid_text = unquote_po(msgid_raw)

            # Reconstituer le msgstr qui suit
            if i < len(lines) and lines[i].startswith("msgstr "):
                msgstr_start = i
                i += 1
                while i < len(lines) and lines[i].startswith('"'):
                    i += 1
                msgstr_end = i

                if msgid_text in TRANSLATIONS:
                    trans = TRANSLATIONS[msgid_text].get(lang)
                    if trans:
                        # Strip fuzzy markers en remontant dans `out`
                        j = len(out) - 1
                        while j >= 0 and out[j].startswith("#"):
                            j -= 1
                        # j+1 .. len(out)-1 = header de cette entrée
                        new_header = [
                            l for l in out[j + 1:]
                            if not l.startswith("#, fuzzy")
                            and not l.startswith("#|")
                        ]
                        if len(new_header) != len(out) - 1 - j:
                            fuzzy_removed += 1
                        out = out[:j + 1] + new_header
                        # msgid inchangé
                        out.extend(lines[msgid_start:msgstr_start])
                        # msgstr réécrit single line
                        out.append(f"msgstr {quote_po(trans)}\n")
                        replaced += 1
                        continue

                # Pas remplacé : on copie le bloc msgid+msgstr tel quel
                out.extend(lines[msgid_start:msgstr_end])
                continue

            # msgid sans msgstr (malformé) : on copie
            out.extend(lines[msgid_start:i])
            continue

        out.append(line)
        i += 1

    po_file.write_text("".join(out), encoding="utf-8")
    return replaced, fuzzy_removed


for lang in ("en", "es", "mg"):
    po_file = ROOT / lang / "LC_MESSAGES" / "django.po"
    replaced, fuzzy_removed = process_file(po_file, lang)
    print(f"  {lang}: {replaced} traductions appliquées, "
          f"{fuzzy_removed} fuzzy supprimés")

print("OK")
