#!/usr/bin/env python3
"""Traductions Sprint 34 — FR → EN/ES/MG.

FEAT-093 : refonte complète des rapports (dix écrans, leurs deux exports, le
sélecteur de période, le modèle `CardRenewal`).

Le tableau est écrit une fois en quatre colonnes plutôt qu'en trois
dictionnaires séparés : aligner les quatre langues côte à côte est le seul
moyen de voir qu'une entrée manque quelque part.

À rejouer APRÈS `makemessages` :
    python scripts/translations_sprint34.py
"""
from __future__ import annotations

from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

# fr: (en, es, mg)
TABLE: dict[str, tuple[str, str, str]] = {
    # ── Modèle CardRenewal ──
    "renouvelée le": ("renewed on", "renovada el", "nohavaozina ny"),
    "ancienne expiration": ("previous expiry", "vencimiento anterior", "fahataperana taloha"),
    "nouvelle expiration": ("new expiry", "nuevo vencimiento", "fahataperana vaovao"),
    "enregistrée par": ("recorded by", "registrada por", "noraketin'i"),
    "renouvellement de carte": ("card renewal", "renovación de tarjeta", "fanavaozana karatra"),
    "renouvellements de carte": (
        "card renewals", "renovaciones de tarjeta", "fanavaozana karatra"),

    # ── Registre des rapports ──
    "Les retards": ("Overdue books", "Los retrasos", "Ny fahatarana"),
    "Les livres qui auraient dû être rendus, du plus ancien au plus récent.": (
        "Books that should have been returned, oldest first.",
        "Los libros que deberían haberse devuelto, del más antiguo al más reciente.",
        "Ny boky tokony efa naverina, manomboka amin'ny tranainy indrindra."),
    "Relancer les retards": ("Chase overdue books", "Reclamar los retrasos",
                             "Manaraka ny fahatarana"),
    "Les réservations à retirer": ("Holds to collect", "Las reservas por retirar",
                                   "Ny famandrihana halaina"),
    "Les livres mis de côté et qui les attend.": (
        "Books set aside and who is waiting for them.",
        "Los libros apartados y quién los espera.",
        "Ny boky natokana sy izay miandry azy."),
    "Prévenir les usagers": ("Notify members", "Avisar a los usuarios",
                             "Mampandre ny mpampiasa"),
    "Les inactifs": ("Inactive members and books", "Los inactivos", "Ny tsy miasa"),
    "Les usagers et les livres sans mouvement depuis longtemps.": (
        "Members and books with no activity for a long time.",
        "Los usuarios y los libros sin movimiento desde hace mucho.",
        "Ny mpampiasa sy ny boky tsy nisy hetsika hatry ny ela."),
    "Voir les inactifs": ("See inactive items", "Ver los inactivos",
                          "Jereo ny tsy miasa"),
    "Vue d'ensemble": ("Overview", "Visión de conjunto", "Topi-maso"),
    "Tous les chiffres importants sur une page. À imprimer pour le comité.": (
        "All the key figures on one page. Print it for the committee.",
        "Todas las cifras importantes en una página. Para imprimir para el comité.",
        "Ny isa lehibe rehetra amin'ny pejy iray. Atontay ho an'ny komity."),
    "Le fonds": ("The collection", "El fondo", "Ny tahiry"),
    "Combien de livres, de quelle sorte, dans quel état, d'où ils viennent.": (
        "How many books, of what kind, in what condition, where they come from.",
        "Cuántos libros, de qué tipo, en qué estado, de dónde vienen.",
        "Firy ny boky, karazana inona, toe-javatra manao ahoana, avy aiza."),
    "Les prêts": ("Loans", "Los préstamos", "Ny fampindramana"),
    "Combien de prêts, et les livres les plus et les moins empruntés.": (
        "How many loans, and the most and least borrowed books.",
        "Cuántos préstamos, y los libros más y menos prestados.",
        "Firy ny fampindramana, sy ny boky be indrindra sy kely indrindra nindramina."),
    "Les usagers": ("Members", "Los usuarios", "Ny mpampiasa"),
    "Combien de personnes, qui elles sont, qui arrive et qui part.": (
        "How many people, who they are, who joins and who leaves.",
        "Cuántas personas, quiénes son, quién llega y quién se va.",
        "Firy ny olona, iza izy ireo, iza no tonga ary iza no lasa."),
    "La fréquentation": ("Attendance", "La asistencia", "Ny fanatrehana"),
    "Qui vient à la bibliothèque et aux animations, et de quel âge.": (
        "Who comes to the library and to activities, and at what age.",
        "Quién viene a la biblioteca y a las actividades, y de qué edad.",
        "Iza no tonga ao amin'ny tranomboky sy amin'ny hetsika, ary firy taona."),
    "Le travail de l'équipe": ("The team's work", "El trabajo del equipo",
                               "Ny asan'ny ekipa"),
    "Les heures faites, par nature de travail et par personne.": (
        "Hours worked, by kind of work and by person.",
        "Las horas realizadas, por tipo de trabajo y por persona.",
        "Ny ora vita, araka ny karazan'asa sy araka ny olona."),
    "L'argent": ("Money", "El dinero", "Ny vola"),
    "Ce qui a été facturé, ce qui a été encaissé, ce qui reste dû.": (
        "What was invoiced, what was collected, what is still owed.",
        "Lo facturado, lo cobrado y lo que queda por pagar.",
        "Izay nofakturina, izay voaray, sy izay mbola tsy voaloa."),

    # ── Écran fréquentation ──
    "Venues à la bibliothèque": ("Library visits", "Visitas a la biblioteca",
                                 "Fitsidihana ny tranomboky"),
    "présences enregistrées, membres et non-membres": (
        "attendances recorded, members and non-members",
        "asistencias registradas, socios y no socios",
        "fanatrehana voarakitra, mpikambana sy tsy mpikambana"),
    "Animations organisées": ("Activities held", "Actividades organizadas",
                              "Hetsika nokarakaraina"),
    "hors simple venue": ("not counting plain visits", "sin contar las simples visitas",
                          "tsy anisan'ny fitsidihana tsotra"),
    "Participations d'usagers": ("Member attendances", "Participaciones de usuarios",
                                 "Fandraisan'anjaran'ny mpampiasa"),
    "toutes séances confondues": ("across all sessions", "en todas las sesiones",
                                  "amin'ny fivoriana rehetra"),
    "venus sans être inscrits": ("came without being registered",
                                 "vinieron sin estar inscritos",
                                 "tonga nefa tsy voasoratra anarana"),
    "temps d'accueil et d'atelier": ("welcoming and workshop time",
                                     "tiempo de acogida y de taller",
                                     "fotoana fandraisana sy atrikasa"),
    "livres lus sans être empruntés": ("books read without being borrowed",
                                       "libros leídos sin ser prestados",
                                       "boky novakiana nefa tsy nindramina"),
    "« %(label)s » enregistre une simple venue à la bibliothèque : c'est l'animation "
    "principale, comptée à part des ateliers.": (
        "\u201c%(label)s\u201d records a plain visit to the library: it is the main "
        "activity, counted separately from workshops.",
        "\u00ab %(label)s \u00bb registra una simple visita a la biblioteca: es la "
        "actividad principal, contada aparte de los talleres.",
        "\u00ab %(label)s \u00bb dia mandrakitra fitsidihana tsotra ny tranomboky : "
        "izy no hetsika fototra, isaina misaraka amin'ny atrikasa."),
    "L'âge des personnes présentes": ("Ages of those present",
                                      "La edad de las personas presentes",
                                      "Ny taonan'ny olona tonga"),
    "Seuls les usagers inscrits ont un âge connu ; les non-membres sont comptés à part.": (
        "Only registered members have a known age; non-members are counted separately.",
        "Solo los usuarios inscritos tienen edad conocida; los no socios se cuentan aparte.",
        "Ny mpampiasa voasoratra ihany no fantatra taona ; isaina misaraka ny tsy mpikambana."),
    "La fréquentation mois par mois": ("Attendance month by month",
                                       "La asistencia mes a mes",
                                       "Ny fanatrehana isam-bolana"),
    "Ce qui a été organisé": ("What was held", "Lo que se organizó",
                              "Izay nokarakaraina"),
    "Séances": ("Sessions", "Sesiones", "Fivoriana"),
    "Usagers présents": ("Members present", "Usuarios presentes",
                         "Mpampiasa tonga"),
    "Aucune séance sur cette période.": ("No sessions in this period.",
                                         "Ninguna sesión en este período.",
                                         "Tsy nisy fivoriana tamin'io vanim-potoana io."),
    "Les présences par âge et par animation": (
        "Attendance by age and by activity",
        "Las asistencias por edad y por actividad",
        "Ny fanatrehana araka ny taona sy ny hetsika"),
    "Aucune présence enregistrée sur cette période.": (
        "No attendance recorded in this period.",
        "Ninguna asistencia registrada en este período.",
        "Tsy nisy fanatrehana voarakitra tamin'io vanim-potoana io."),
    "L'âge est celui de la personne le jour de la séance.": (
        "The age is the person's age on the day of the session.",
        "La edad es la de la persona el día de la sesión.",
        "Ny taona dia ny an'ilay olona tamin'ny andron'ny fivoriana."),

    # ── Écran fonds ──
    "Livres au total": ("Books in total", "Libros en total", "Boky manontolo"),
    "exemplaires du fonds": ("copies in the collection", "ejemplares del fondo",
                             "kopia ao amin'ny tahiry"),
    "Disponibles": ("Available", "Disponibles", "Misy"),
    "sur les rayons maintenant": ("on the shelves right now",
                                  "en los estantes ahora mismo",
                                  "eo amin'ny talantalana ankehitriny"),
    "Sortis": ("Out on loan", "Prestados", "Nindramina"),
    "chez des usagers": ("with members", "en manos de usuarios",
                         "any amin'ny mpampiasa"),
    "Titres différents": ("Distinct titles", "Títulos distintos",
                          "Lohateny samihafa"),
    "un titre peut avoir plusieurs exemplaires": (
        "one title may have several copies",
        "un título puede tener varios ejemplares",
        "ny lohateny iray dia mety hanana kopia maromaro"),
    "hors circulation": ("out of circulation", "fuera de circulación",
                         "tsy mandeha"),
    "Perdus": ("Lost", "Perdidos", "Very"),
    "depuis le début": ("since the beginning", "desde el principio",
                        "hatramin'ny voalohany"),
    "Pilonnés": ("Withdrawn", "Expurgados", "Nesorina"),
    "retirés du fonds": ("removed from the collection", "retirados del fondo",
                         "nesorina tao amin'ny tahiry"),
    "Rotation du fonds": ("Collection turnover", "Rotación del fondo",
                          "Fihodinan'ny tahiry"),
    "prêts par livre sur la période": ("loans per book over the period",
                                       "préstamos por libro en el período",
                                       "fampindramana isaky ny boky nandritra ny vanim-potoana"),
    "Les rayons : ce qu'on a et ce qui sort": (
        "The sections: what we hold and what goes out",
        "Las secciones: lo que tenemos y lo que sale",
        "Ny sokajy : izay ananantsika sy izay mivoaka"),
    "Rayon": ("Section", "Sección", "Sokajy"),
    "Livres": ("Books", "Libros", "Boky"),
    "Part du fonds": ("Share of the collection", "Parte del fondo",
                      "Ampahany amin'ny tahiry"),
    "Prêts sur la période": ("Loans in the period", "Préstamos en el período",
                             "Fampindramana nandritra ny vanim-potoana"),
    "Prêts par livre": ("Loans per book", "Préstamos por libro",
                        "Fampindramana isaky ny boky"),
    "Aucun livre catalogué.": ("No books catalogued.", "Ningún libro catalogado.",
                               "Tsy misy boky voasoratra."),
    "« Prêts par livre » compare les prêts de la période au nombre de livres en "
    "circulation du rayon : au-dessus de 1, chaque livre du rayon est sorti au moins "
    "une fois.": (
        "\u201cLoans per book\u201d compares the period's loans with the number of "
        "circulating books in the section: above 1, every book in the section went "
        "out at least once.",
        "\u00ab Pr\u00e9stamos por libro \u00bb compara los pr\u00e9stamos del "
        "per\u00edodo con el n\u00famero de libros en circulaci\u00f3n de la "
        "secci\u00f3n: por encima de 1, cada libro sali\u00f3 al menos una vez.",
        "\u00ab Fampindramana isaky ny boky \u00bb dia mampitaha ny fampindramana "
        "tamin'ny vanim-potoana amin'ny isan'ny boky mandeha ao amin'ny sokajy : "
        "mihoatra ny 1, dia nivoaka indray mandeha farafahakeliny ny boky tsirairay."),
    "Par sorte de document": ("By kind of document", "Por tipo de documento",
                              "Araka ny karazan-taratasy"),
    "Dans quel état": ("In what condition", "En qué estado",
                       "Amin'ny toe-javatra manao ahoana"),
    "Ce que la bibliothèque possède, et ce qui est entré ou sorti.": (
        "What the library holds, and what came in or went out.",
        "Lo que la biblioteca posee, y lo que entró o salió.",
        "Izay ananan'ny tranomboky, sy izay niditra na nivoaka."),
    "Sans rayon": ("No section", "Sin sección", "Tsy misy sokajy"),
    "Les livres par rayon": ("Books by section", "Los libros por sección",
                             "Ny boky araka ny sokajy"),
    "livres": ("books", "libros", "boky"),
    "Les langues : le fonds et le public": (
        "Languages: the collection and the public",
        "Las lenguas: el fondo y el público",
        "Ny fiteny : ny tahiry sy ny vahoaka"),
    "Titres": ("Titles", "Títulos", "Lohateny"),
    "Usagers qui la parlent": ("Members who speak it", "Usuarios que la hablan",
                               "Mpampiasa miteny azy"),
    "Part du public": ("Share of the public", "Parte del público",
                       "Ampahany amin'ny vahoaka"),
    "Aucune langue renseignée.": ("No language recorded.",
                                  "Ninguna lengua registrada.",
                                  "Tsy misy fiteny voarakitra."),
    "Sans emplacement": ("No location", "Sin ubicación", "Tsy misy toerana"),
    "Où sont les livres": ("Where the books are", "Dónde están los libros",
                           "Aiza ny boky"),
    "Part": ("Share", "Parte", "Ampahany"),
    "Aucun emplacement renseigné.": ("No location recorded.",
                                     "Ninguna ubicación registrada.",
                                     "Tsy misy toerana voarakitra."),
    "Fonds de la bibliothèque": ("The library's own collection",
                                 "Fondo propio de la biblioteca",
                                 "Tahirin'ny tranomboky"),
    "D'où viennent les livres": ("Where the books come from",
                                 "De dónde vienen los libros",
                                 "Avy aiza ny boky"),
    "Aucune provenance renseignée.": ("No source recorded.",
                                      "Ninguna procedencia registrada.",
                                      "Tsy misy fiaviana voarakitra."),
    "Comment ils sont arrivés": ("How they arrived", "Cómo llegaron",
                                 "Ahoana no nahatongavany"),
    "Origine": ("Origin", "Origen", "Fiaviana"),
    "Aucune origine renseignée.": ("No origin recorded.",
                                   "Ningún origen registrado.",
                                   "Tsy misy fiaviana voarakitra."),
    "Les livres entrés pendant la période": (
        "Books that came in during the period",
        "Los libros que entraron durante el período",
        "Ny boky niditra nandritra ny vanim-potoana"),
    "Titres nouveaux": ("New titles", "Títulos nuevos", "Lohateny vaovao"),
    "Aucun livre catalogué pendant cette période.": (
        "No books catalogued in this period.",
        "Ningún libro catalogado en este período.",
        "Tsy nisy boky voasoratra tamin'io vanim-potoana io."),
    "Les dons reçus pendant la période": ("Gifts received during the period",
                                          "Las donaciones recibidas en el período",
                                          "Ny fanomezana noraisina nandritra ny vanim-potoana"),
    "Livres donnés": ("Books given", "Libros donados", "Boky nomena"),
    "Aucun don enregistré pendant cette période.": (
        "No gifts recorded in this period.",
        "Ninguna donación registrada en este período.",
        "Tsy nisy fanomezana voarakitra tamin'io vanim-potoana io."),
    "Les livres qui n'ont jamais servi": ("Books that have never been used",
                                          "Los libros que nunca han servido",
                                          "Ny boky tsy mbola nampiasaina"),
    "Tous les livres en rayon depuis plus d'un an sont sortis au moins une fois.": (
        "Every book on the shelves for over a year has gone out at least once.",
        "Todos los libros en estantería desde hace más de un año han salido al menos una vez.",
        "Ny boky rehetra eo amin'ny talantalana efa mihoatra ny herintaona dia nivoaka "
        "indray mandeha farafahakeliny."),
    "Comptés : les livres en rayon depuis plus d'un an et jamais empruntés. Les "
    "nouveautés, les livres perdus, pilonnés ou en réparation sont écartés.": (
        "Counted: books on the shelves for over a year and never borrowed. New "
        "arrivals and books lost, withdrawn or under repair are left out.",
        "Contados: los libros en estantería desde hace más de un año y nunca "
        "prestados. Se excluyen las novedades y los libros perdidos, expurgados o en "
        "reparación.",
        "Isaina : ny boky eo amin'ny talantalana efa mihoatra ny herintaona ary tsy "
        "mbola nindramina. Esorina ny vaovao sy ny boky very, nesorina na amboarina."),

    # ── Écran prêts ──
    "pendant la période": ("during the period", "durante el período",
                           "nandritra ny vanim-potoana"),
    "Retours": ("Returns", "Devoluciones", "Famerenana"),
    "livres déjà rendus": ("books already returned", "libros ya devueltos",
                           "boky efa naverina"),
    "En retard aujourd'hui": ("Overdue today", "En retraso hoy",
                              "Tara androany"),
    "à relancer": ("to chase up", "por reclamar", "tokony arahina"),
    "Rendus en retard": ("Returned late", "Devueltos con retraso",
                         "Naverina tara"),
    "des livres rendus, sur la période": ("of the books returned, over the period",
                                          "de los libros devueltos, en el período",
                                          "amin'ny boky naverina, nandritra ny vanim-potoana"),
    "Durée d'un prêt": ("Length of a loan", "Duración de un préstamo",
                        "Faharetan'ny fampindramana"),
    "la moitié des prêts durent moins que cela": (
        "half the loans are shorter than this",
        "la mitad de los préstamos duran menos que esto",
        "ny antsasaky ny fampindramana dia fohy noho izany"),
    "Renouvellements": ("Renewals", "Renovaciones", "Fanavaozana"),
    "prolongations accordées": ("extensions granted", "prórrogas concedidas",
                                "fanitarana nomena"),
    "Combien de livres sont sortis, lesquels, et par qui.": (
        "How many books went out, which ones, and to whom.",
        "Cuántos libros salieron, cuáles, y por quién.",
        "Firy ny boky nivoaka, iza avy, ary an'iza."),
    "Les prêts mois par mois": ("Loans month by month", "Los préstamos mes a mes",
                                "Ny fampindramana isam-bolana"),
    "Ce qui se prête, par rayon": ("What gets borrowed, by section",
                                   "Lo que se presta, por sección",
                                   "Izay indramina, araka ny sokajy"),
    "Qui emprunte, par catégorie d'usager": (
        "Who borrows, by member category",
        "Quién presta, por categoría de usuario",
        "Iza no mindrana, araka ny sokajin'ny mpampiasa"),
    "Les livres les plus empruntés": ("The most borrowed books",
                                      "Los libros más prestados",
                                      "Ny boky be indrindra nindramina"),
    "Les %(n)s titres les plus sortis pendant la période.": (
        "The %(n)s titles that went out most during the period.",
        "Los %(n)s títulos más salidos durante el período.",
        "Ny lohateny %(n)s nivoaka be indrindra nandritra ny vanim-potoana."),
    "Les livres les moins empruntés": ("The least borrowed books",
                                       "Los libros menos prestados",
                                       "Ny boky kely indrindra nindramina"),
    "Les %(n)s titres les moins sortis parmi ceux qui sont sortis au moins une fois. "
    "Les livres jamais empruntés sont comptés séparément.": (
        "The %(n)s titles that went out least among those that went out at least "
        "once. Books never borrowed are counted separately.",
        "Los %(n)s títulos menos salidos entre los que salieron al menos una vez. Los "
        "libros nunca prestados se cuentan aparte.",
        "Ny lohateny %(n)s nivoaka kely indrindra amin'ireo nivoaka indray mandeha "
        "farafahakeliny. Isaina misaraka ny boky tsy mbola nindramina."),
    "Aucun prêt pendant cette période.": ("No loans in this period.",
                                          "Ningún préstamo en este período.",
                                          "Tsy nisy fampindramana tamin'io vanim-potoana io."),
    "Les livres jamais empruntés": ("Books never borrowed",
                                    "Los libros nunca prestados",
                                    "Ny boky tsy mbola nindramina"),
    "Tous les livres du fonds sont sortis au moins une fois.": (
        "Every book in the collection has gone out at least once.",
        "Todos los libros del fondo han salido al menos una vez.",
        "Ny boky rehetra ao amin'ny tahiry dia nivoaka indray mandeha farafahakeliny."),
    "Depuis leur entrée au catalogue, pas seulement sur la période.": (
        "Since they entered the catalogue, not just over the period.",
        "Desde su entrada en el catálogo, no solo en el período.",
        "Hatramin'ny nidirany tao amin'ny katalaogy, tsy amin'io vanim-potoana io ihany."),
    "Les réservations de la période": ("Holds placed in the period",
                                       "Las reservas del período",
                                       "Ny famandrihana tamin'ny vanim-potoana"),
    "Ce qu'elles sont devenues": ("What became of them", "En qué acabaron",
                                  "Izay nanjo azy ireo"),
    "Nombre": ("Number", "Número", "Isa"),
    "Aucune réservation pendant cette période.": (
        "No holds in this period.",
        "Ninguna reserva en este período.",
        "Tsy nisy famandrihana tamin'io vanim-potoana io."),
    "Jour par jour": ("Day by day", "Día a día", "Isan'andro"),
    "Jour": ("Day", "Día", "Andro"),
    "Aucun mouvement pendant cette période.": ("No activity in this period.",
                                               "Ningún movimiento en este período.",
                                               "Tsy nisy hetsika tamin'io vanim-potoana io."),
    "Seuls les jours où la bibliothèque a prêté ou reçu un livre sont listés.": (
        "Only days when the library lent or received a book are listed.",
        "Solo se listan los días en que la biblioteca prestó o recibió un libro.",
        "Ny andro nampindraman'ny tranomboky na nandraisany boky ihany no voatanisa."),

    # ── Écran usagers ──
    "Usagers inscrits": ("Registered members", "Usuarios inscritos",
                         "Mpampiasa voasoratra"),
    "depuis l'ouverture": ("since opening", "desde la apertura",
                           "hatramin'ny nanokafana"),
    "Cartes valides": ("Valid cards", "Tarjetas válidas", "Karatra manan-kery"),
    "aujourd'hui": ("today", "hoy", "androany"),
    "Familles": ("Families", "Familias", "Fianakaviana"),
    "cartes avec plusieurs personnes": ("cards covering several people",
                                        "tarjetas con varias personas",
                                        "karatra misy olona maromaro"),
    "Personnes touchées": ("People reached", "Personas alcanzadas",
                           "Olona voakasika"),
    "titulaires et personnes de leur foyer": (
        "cardholders and the people in their household",
        "titulares y personas de su hogar",
        "tompon-karatra sy ny olona ao an-tokantranony"),
    "Usagers venus": ("Members who came", "Usuarios que vinieron",
                      "Mpampiasa tonga"),
    "ont emprunté ou participé sur la période": (
        "borrowed or took part during the period",
        "prestaron o participaron durante el período",
        "nindrana na nandray anjara nandritra ny vanim-potoana"),
    "Nouveaux": ("New", "Nuevos", "Vaovao"),
    "inscrits sur la période": ("registered during the period",
                                "inscritos en el período",
                                "voasoratra nandritra ny vanim-potoana"),
    "Réinscriptions": ("Renewals", "Reinscripciones", "Fisoratana indray"),
    "Cartes perdues": ("Cards lost", "Tarjetas perdidas", "Karatra very"),
    "périmées sur la période et non renouvelées": (
        "expired during the period and not renewed",
        "vencidas en el período y no renovadas",
        "lany daty nandritra ny vanim-potoana ary tsy nohavaozina"),
    "Combien de personnes la bibliothèque touche, et qui elles sont.": (
        "How many people the library reaches, and who they are.",
        "A cuántas personas llega la biblioteca, y quiénes son.",
        "Firy ny olona tratran'ny tranomboky, ary iza izy ireo."),
    "comptées depuis le %(d)s": ("counted since %(d)s", "contadas desde el %(d)s",
                                 "isaina hatramin'ny %(d)s"),
    "cartes renouvelées sur la période": ("cards renewed during the period",
                                          "tarjetas renovadas en el período",
                                          "karatra nohavaozina nandritra ny vanim-potoana"),
    "« Usagers venus » réunit les emprunteurs et les participants aux animations : "
    "quelqu'un qui a fait les deux n'est compté qu'une fois.": (
        "\u201cMembers who came\u201d covers both borrowers and activity "
        "participants: someone who did both is counted only once.",
        "\u00ab Usuarios que vinieron \u00bb re\u00fane a los prestatarios y a los "
        "participantes en actividades: quien hizo ambas cosas se cuenta una sola vez.",
        "\u00ab Mpampiasa tonga \u00bb dia mitambatra ny mpindrana sy ny mpandray "
        "anjara amin'ny hetsika : izay nanao ny roa dia isaina indray mandeha ihany."),
    "L'âge des usagers": ("The ages of members", "La edad de los usuarios",
                          "Ny taonan'ny mpampiasa"),
    "Les catégories d'usager": ("Member categories", "Las categorías de usuario",
                                "Ny sokajin'ny mpampiasa"),
    "Qui arrive, qui reste, qui part": ("Who joins, who stays, who leaves",
                                        "Quién llega, quién se queda, quién se va",
                                        "Iza no tonga, iza no mijanona, iza no lasa"),
    "Cartes à renouveler dans les %(n)s jours": (
        "Cards to renew within %(n)s days",
        "Tarjetas por renovar en %(n)s días",
        "Karatra havaozina anatin'ny %(n)s andro"),
    "Aucune carte n'arrive à échéance ce mois-ci.": (
        "No card falls due this month.",
        "Ninguna tarjeta vence este mes.",
        "Tsy misy karatra lany daty amin'ity volana ity."),
    "D'où viennent les usagers": ("Where members come from",
                                  "De dónde vienen los usuarios",
                                  "Avy aiza ny mpampiasa"),
    "Code postal": ("Postcode", "Código postal", "Kaody paositra"),
    "Localité": ("Town", "Localidad", "Tanàna"),
    "Aucune localité renseignée.": ("No town recorded.",
                                    "Ninguna localidad registrada.",
                                    "Tsy misy tanàna voarakitra."),
    "%(n)s usagers n'ont pas de localité renseignée.": (
        "%(n)s members have no town recorded.",
        "%(n)s usuarios no tienen localidad registrada.",
        "Mpampiasa %(n)s no tsy manana tanàna voarakitra."),
    "Les langues parlées par les usagers": ("Languages spoken by members",
                                            "Las lenguas habladas por los usuarios",
                                            "Ny fiteny ampiasain'ny mpampiasa"),
    "%(n)s usagers n'ont aucune langue renseignée.": (
        "%(n)s members have no language recorded.",
        "%(n)s usuarios no tienen ninguna lengua registrada.",
        "Mpampiasa %(n)s no tsy manana fiteny voarakitra."),
    "Les usagers qui ont le plus emprunté": ("The members who borrowed most",
                                             "Los usuarios que más prestaron",
                                             "Ny mpampiasa nindrana be indrindra"),
    "Aucun prêt sur cette période.": ("No loans in this period.",
                                      "Ningún préstamo en este período.",
                                      "Tsy nisy fampindramana tamin'io vanim-potoana io."),

    # ── Écran argent ──
    "Facturé": ("Invoiced", "Facturado", "Nofakturina"),
    "sur la période": ("over the period", "en el período",
                       "nandritra ny vanim-potoana"),
    "Encaissé": ("Collected", "Cobrado", "Voaray"),
    "paiements reçus sur la période": ("payments received during the period",
                                       "pagos recibidos en el período",
                                       "fandoavam-bola voaray nandritra ny vanim-potoana"),
    "Reste dû": ("Still owed", "Pendiente de pago", "Mbola tsy voaloa"),
    "toutes factures ouvertes confondues": ("across all open invoices",
                                            "en todas las facturas abiertas",
                                            "amin'ny faktiora misokatra rehetra"),
    "Entrées de caisse": ("Cash in", "Entradas de caja", "Vola miditra"),
    "espèces reçues": ("cash received", "efectivo recibido", "vola voaray"),
    "Sorties de caisse": ("Cash out", "Salidas de caja", "Vola mivoaka"),
    "dépenses saisies": ("expenses entered", "gastos registrados",
                         "fandaniana voarakitra"),
    "Solde de la caisse": ("Cash balance", "Saldo de caja", "Tahirim-bola"),
    "entrées moins sorties sur la période": ("cash in minus cash out over the period",
                                             "entradas menos salidas en el período",
                                             "miditra ampihenana mivoaka nandritra ny vanim-potoana"),
    "Les factures à encaisser": ("Invoices to collect", "Las facturas por cobrar",
                                 "Ny faktiora horaisina"),
    "N° de facture": ("Invoice no.", "N.º de factura", "Lah. faktiora"),
    "Jours de retard": ("Days late", "Días de retraso", "Andro tara"),
    "Aucune facture en attente de paiement.": ("No invoice awaiting payment.",
                                               "Ninguna factura pendiente de pago.",
                                               "Tsy misy faktiora miandry fandoavam-bola."),
    "Toutes les factures ouvertes, y compris celles émises avant la période.": (
        "All open invoices, including those issued before the period.",
        "Todas las facturas abiertas, incluidas las emitidas antes del período.",
        "Ny faktiora misokatra rehetra, anisan'izany ireo navoaka talohan'ny vanim-potoana."),
    "D'où vient l'argent": ("Where the money comes from", "De dónde viene el dinero",
                            "Avy aiza ny vola"),
    "Les recettes par nature": ("Income by kind", "Los ingresos por naturaleza",
                                "Ny fidiram-bola araka ny karazany"),
    "Aucune facture émise sur cette période.": ("No invoice issued in this period.",
                                                "Ninguna factura emitida en este período.",
                                                "Tsy nisy faktiora navoaka tamin'io vanim-potoana io."),
    "Les encaissements mois par mois": ("Collections month by month",
                                        "Los cobros mes a mes",
                                        "Ny vola voaray isam-bolana"),
    "Comment les gens paient": ("How people pay", "Cómo paga la gente",
                                "Ahoana no andoavan'ny olona"),
    "Mode de paiement": ("Payment method", "Modo de pago", "Fomba fandoavana"),
    "Paiements": ("Payments", "Pagos", "Fandoavam-bola"),
    "Aucun paiement sur cette période.": ("No payments in this period.",
                                          "Ningún pago en este período.",
                                          "Tsy nisy fandoavam-bola tamin'io vanim-potoana io."),
    "La caisse jour par jour": ("The till, day by day", "La caja día a día",
                                "Ny kesy isan'andro"),
    "Autres paiements": ("Other payments", "Otros pagos", "Fandoavana hafa"),
    "Solde espèces du jour": ("Cash balance for the day", "Saldo en efectivo del día",
                              "Tahirim-bola androany"),
    "Aucun mouvement d'argent sur cette période.": (
        "No money moved in this period.",
        "Ningún movimiento de dinero en este período.",
        "Tsy nisy fihetsiketsehim-bola tamin'io vanim-potoana io."),
    "Le détail de la caisse": ("The till in detail", "El detalle de la caja",
                               "Ny antsipirian'ny kesy"),
    "Aucun mouvement de caisse sur cette période.": (
        "No till movements in this period.",
        "Ningún movimiento de caja en este período.",
        "Tsy nisy fihetsehan'ny kesy tamin'io vanim-potoana io."),

    # ── Vue d'ensemble ──
    "Livres sortis": ("Books out", "Libros prestados", "Boky nivoaka"),
    "chez des usagers en ce moment": ("with members right now",
                                      "en manos de usuarios ahora mismo",
                                      "any amin'ny mpampiasa ankehitriny"),
    "Livres disponibles": ("Books available", "Libros disponibles",
                           "Boky misy"),
    "sur les rayons aujourd'hui": ("on the shelves today",
                                   "en los estantes hoy",
                                   "eo amin'ny talantalana androany"),
    "Livres en retard": ("Overdue books", "Libros en retraso", "Boky tara"),
    "dont %(n)s familles": ("of which %(n)s families", "de las cuales %(n)s familias",
                            "ka %(n)s no fianakaviana"),
    "Livres au catalogue": ("Books in the catalogue", "Libros en el catálogo",
                            "Boky ao amin'ny katalaogy"),
    "%(n)s titres différents": ("%(n)s distinct titles", "%(n)s títulos distintos",
                                "lohateny %(n)s samihafa"),
    "Nouveaux livres": ("New books", "Libros nuevos", "Boky vaovao"),
    "Nouveaux usagers": ("New members", "Usuarios nuevos", "Mpampiasa vaovao"),
    "Présences aux animations": ("Activity attendances",
                                 "Asistencias a las actividades",
                                 "Fanatrehana ny hetsika"),
    "Heures de travail": ("Hours worked", "Horas de trabajo", "Ora niasana"),
    "Argent encaissé": ("Money collected", "Dinero cobrado", "Vola voaray"),
    "%(label)s : %(v)s": ("%(label)s: %(v)s", "%(label)s: %(v)s", "%(label)s : %(v)s"),
    "Les chiffres importants de la bibliothèque, sur une page.": (
        "The library's key figures, on one page.",
        "Las cifras importantes de la biblioteca, en una página.",
        "Ny isa lehibe momba ny tranomboky, amin'ny pejy iray."),
    "Les six premiers chiffres décrivent aujourd'hui ; les six suivants, la période "
    "choisie.": (
        "The first six figures describe today; the next six, the chosen period.",
        "Las seis primeras cifras describen hoy; las seis siguientes, el período elegido.",
        "Ny isa enina voalohany dia mamaritra ny androany ; ny enina manaraka, ny "
        "vanim-potoana nofidina."),
    "Les livres sortis à la fin de chaque mois": (
        "Books out at the end of each month",
        "Los libros prestados al final de cada mes",
        "Ny boky nivoaka tamin'ny faran'ny volana tsirairay"),
    "Nombre de livres qui n'étaient pas rentrés le dernier jour du mois.": (
        "Number of books not yet back on the last day of the month.",
        "Número de libros no devueltos el último día del mes.",
        "Isan'ny boky mbola tsy tafaverina tamin'ny andro farany amin'ny volana."),
    "Le fonds par rayon": ("The collection by section", "El fondo por sección",
                           "Ny tahiry araka ny sokajy"),
    "Livres disponibles aujourd'hui": ("Books available today",
                                       "Libros disponibles hoy",
                                       "Boky misy androany"),
    "Livres sortis aujourd'hui": ("Books out today", "Libros prestados hoy",
                                  "Boky nivoaka androany"),
    "Livres en retard aujourd'hui": ("Books overdue today",
                                     "Libros en retraso hoy",
                                     "Boky tara androany"),
    "Livres entrés": ("Books received", "Libros ingresados", "Boky niditra"),
    "Le bilan en un tableau": ("The summary in one table",
                               "El balance en una tabla",
                               "Ny fintina amin'ny tabilao iray"),
    "Ce qu'on compte": ("What we count", "Lo que contamos", "Izay isaintsika"),
    "Les huit premières lignes décrivent la situation d'aujourd'hui et ne dépendent "
    "pas de la période choisie.": (
        "The first eight rows describe today's situation and do not depend on the "
        "chosen period.",
        "Las ocho primeras filas describen la situación de hoy y no dependen del "
        "período elegido.",
        "Ny andalana valo voalohany dia mamaritra ny toe-javatra androany ary tsy "
        "miankina amin'ny vanim-potoana nofidina."),

    # ── Écran équipe ──
    "saisies sur la période": ("entered over the period", "registradas en el período",
                               "voarakitra nandritra ny vanim-potoana"),
    "Personnes": ("People", "Personas", "Olona"),
    "ont travaillé sur la période": ("worked during the period",
                                     "trabajaron durante el período",
                                     "niasa nandritra ny vanim-potoana"),
    "comptées séparément des activités": ("counted separately from activities",
                                          "contadas aparte de las actividades",
                                          "isaina misaraka amin'ny asa"),
    "lignes de temps enregistrées": ("time entries recorded",
                                     "líneas de tiempo registradas",
                                     "andalan'ora voarakitra"),
    "Le temps donné à la bibliothèque, par nature de travail et par personne.": (
        "Time given to the library, by kind of work and by person.",
        "El tiempo dedicado a la biblioteca, por tipo de trabajo y por persona.",
        "Ny fotoana nomena ny tranomboky, araka ny karazan'asa sy araka ny olona."),
    "Les heures par nature de travail": ("Hours by kind of work",
                                         "Las horas por tipo de trabajo",
                                         "Ny ora araka ny karazan'asa"),
    "heures": ("hours", "horas", "ora"),
    "Les heures mois par mois": ("Hours month by month", "Las horas mes a mes",
                                 "Ny ora isam-bolana"),
    "Le temps par nature de travail": ("Time by kind of work",
                                       "El tiempo por tipo de trabajo",
                                       "Ny fotoana araka ny karazan'asa"),
    "Nature du travail": ("Kind of work", "Tipo de trabajo", "Karazan'asa"),
    "Aucun temps de travail saisi sur cette période.": (
        "No working time entered for this period.",
        "Ningún tiempo de trabajo registrado en este período.",
        "Tsy nisy fotoam-piasana voarakitra tamin'io vanim-potoana io."),
    "Le temps par personne": ("Time by person", "El tiempo por persona",
                              "Ny fotoana araka ny olona"),
    "Personne": ("Person", "Persona", "Olona"),
    "Le détail mois par mois": ("The detail month by month",
                                "El detalle mes a mes",
                                "Ny antsipiriany isam-bolana"),

    # ── Listes de travail ──
    "Livres non rendus dont l'échéance est passée de plus de %(n)s jours.": (
        "Books not returned, more than %(n)s days past due.",
        "Libros no devueltos con más de %(n)s días de retraso.",
        "Boky tsy naverina, mihoatra ny %(n)s andro taorian'ny fe-potoana."),
    "Tous les livres non rendus dont l'échéance est passée.": (
        "All books not returned whose due date has passed.",
        "Todos los libros no devueltos cuyo plazo ha vencido.",
        "Ny boky rehetra tsy naverina ka lany ny fe-potoana."),
    "à relancer aujourd'hui": ("to chase up today", "por reclamar hoy",
                               "tokony arahina androany"),
    "Le plus ancien": ("The oldest", "El más antiguo", "Ny tranainy indrindra"),
    "de retard": ("late", "de retraso", "tara"),
    "À rappeler": ("To call back", "Por llamar", "Hantsoina"),
    "N° du livre": ("Book no.", "N.º del libro", "Lah. boky"),
    "À rendre le": ("Due on", "A devolver el", "Averina ny"),
    "Aucun retard. Tout est rentré.": ("No overdue books. Everything is back.",
                                       "Sin retrasos. Todo ha vuelto.",
                                       "Tsy misy fahatarana. Tafaverina daholo."),
    "Non": ("No", "No", "Tsia"),
    "Oui": ("Yes", "Sí", "Eny"),
    "Livres mis de côté qui attendent leur usager.": (
        "Books set aside waiting for their member.",
        "Libros apartados que esperan a su usuario.",
        "Boky natokana miandry ny mpampiasa azy."),
    "Livres mis de côté": ("Books set aside", "Libros apartados",
                           "Boky natokana"),
    "à garder au comptoir": ("to keep at the desk", "para guardar en el mostrador",
                             "hotehirizina eo amin'ny birao"),
    "Usagers à prévenir": ("Members to notify", "Usuarios por avisar",
                           "Mpampiasa hampandrenesina"),
    "pas encore appelés": ("not yet called", "aún no llamados",
                           "mbola tsy nantsoina"),
    "À prévenir et à remettre": ("To notify and hand over",
                                 "Por avisar y entregar",
                                 "Hampandrenesina sy hatolotra"),
    "Prévenu ?": ("Notified?", "¿Avisado?", "Nampandrenesina?"),
    "Aucun livre en attente de retrait.": ("No book awaiting collection.",
                                           "Ningún libro pendiente de retirada.",
                                           "Tsy misy boky miandry halaina."),
    "jamais": ("never", "nunca", "tsy mbola"),
    "Usagers et livres sans aucun prêt depuis %(n)s jours.": (
        "Members and books with no loan for %(n)s days.",
        "Usuarios y libros sin ningún préstamo desde hace %(n)s días.",
        "Mpampiasa sy boky tsy nisy fampindramana nandritra ny %(n)s andro."),
    "Usagers sans prêt": ("Members with no loan", "Usuarios sin préstamo",
                          "Mpampiasa tsy nindrana"),
    "depuis %(n)s jours": ("for %(n)s days", "desde hace %(n)s días",
                           "nandritra ny %(n)s andro"),
    "Livres jamais sortis": ("Books never out", "Libros nunca prestados",
                             "Boky tsy mbola nivoaka"),
    "Dernier prêt": ("Last loan", "Último préstamo", "Fampindramana farany"),
    "Tous les usagers ont emprunté récemment.": (
        "Every member has borrowed recently.",
        "Todos los usuarios han prestado recientemente.",
        "Nindrana vao haingana ny mpampiasa rehetra."),
    "Livres qui ne sortent pas": ("Books that do not go out",
                                  "Libros que no salen",
                                  "Boky tsy mivoaka"),
    "Acquis le": ("Acquired on", "Adquirido el", "Azo ny"),
    "Tous les livres ont été empruntés récemment.": (
        "Every book has been borrowed recently.",
        "Todos los libros han sido prestados recientemente.",
        "Nindramina vao haingana ny boky rehetra."),

    # ── Socle : graphes, Excel, PDF, périodes ──
    "Autres": ("Others", "Otros", "Hafa"),
    "Feuille": ("Sheet", "Hoja", "Takila"),
    "Résumé": ("Summary", "Resumen", "Fintina"),
    "Période": ("Period", "Período", "Vanim-potoana"),
    "au": ("to", "al", "ka hatramin'ny"),
    "Chiffre": ("Figure", "Cifra", "Isa"),
    "Valeur": ("Value", "Valor", "Sanda"),
    "Précision": ("Detail", "Precisión", "Fanazavana"),
    "%(n)s jours": ("%(n)s days", "%(n)s días", "%(n)s andro"),
    "1 jour": ("1 day", "1 día", "1 andro"),
    "âge inconnu": ("age unknown", "edad desconocida", "tsy fantatra taona"),
    "Page %(n)s": ("Page %(n)s", "Página %(n)s", "Pejy %(n)s"),
    "Rien à afficher.": ("Nothing to show.", "Nada que mostrar.",
                         "Tsy misy aseho."),
    "12 derniers mois": ("Last 12 months", "Últimos 12 meses",
                         "Volana 12 farany"),
    "du %(start)s au %(end)s": ("from %(start)s to %(end)s",
                                "del %(start)s al %(end)s",
                                "ny %(start)s ka hatramin'ny %(end)s"),
    "Dates incomplètes : voici les 12 derniers mois.": (
        "Incomplete dates: here are the last 12 months.",
        "Fechas incompletas: aquí están los últimos 12 meses.",
        "Daty tsy feno : ireto ny volana 12 farany."),
    "La date de début doit précéder la date de fin : voici les 12 derniers mois.": (
        "The start date must come before the end date: here are the last 12 months.",
        "La fecha de inicio debe preceder a la de fin: aquí están los últimos 12 meses.",
        "Ny daty fanombohana dia tsy maintsy mialoha ny daty famaranana : ireto ny "
        "volana 12 farany."),
    "Ce rapport n'existe pas.": ("There is no such report.",
                                 "Este informe no existe.",
                                 "Tsy misy io tatitra io."),

    # ── Gabarits ──
    "Retard d'au moins": ("Overdue by at least", "Retraso de al menos",
                          "Tara farafahakeliny"),
    "%(value)s jours": ("%(value)s days", "%(value)s días", "%(value)s andro"),
    "Sans aucun prêt depuis": ("With no loan for", "Sin ningún préstamo desde hace",
                               "Tsy nisy fampindramana nandritra ny"),
    "Montrer seulement le rayon": ("Show only the section",
                                   "Mostrar solo la sección",
                                   "Asehoy ny sokajy ihany"),
    "Tous les rayons": ("All sections", "Todas las secciones",
                        "Ny sokajy rehetra"),
    "Catégorie d'usager": ("Member category", "Categoría de usuario",
                           "Sokajin'ny mpampiasa"),
    "Toutes les catégories": ("All categories", "Todas las categorías",
                              "Ny sokajy rehetra"),
    "Quelle période ?": ("Which period?", "¿Qué período?",
                         "Vanim-potoana inona?"),
    "Choisir d'autres dates": ("Choose other dates", "Elegir otras fechas",
                               "Misafidy daty hafa"),
    "Entre le": ("Between", "Entre el", "Eo anelanelan'ny"),
    "et le": ("and", "y el", "sy ny"),
    "Valider ces dates": ("Use these dates", "Validar estas fechas",
                          "Ekeo ireo daty ireo"),
    "Les deux jours indiqués sont compris dans le calcul.": (
        "Both days shown are included in the calculation.",
        "Ambos días indicados están incluidos en el cálculo.",
        "Tafiditra ao anatin'ny kajy ny andro roa voatondro."),
    "Les listes du jour, et les chiffres de la bibliothèque.": (
        "Today's lists, and the library's figures.",
        "Las listas del día, y las cifras de la biblioteca.",
        "Ny lisitry ny andro, sy ny isan'ny tranomboky."),
    "À faire aujourd'hui": ("To do today", "Por hacer hoy", "Atao androany"),
    "Les chiffres de la bibliothèque": ("The library's figures",
                                        "Las cifras de la biblioteca",
                                        "Ny isan'ny tranomboky"),
    "Chaque écran s'imprime en PDF et s'enregistre en Excel.": (
        "Every screen prints to PDF and saves to Excel.",
        "Cada pantalla se imprime en PDF y se guarda en Excel.",
        "Ny efijery tsirairay dia atonta PDF ary tehirizina Excel."),
    "Sortir les données brutes": ("Export the raw data", "Extraer los datos brutos",
                                  "Hamoaka ny angona tsotra"),
    "Fichiers CSV à reprendre dans un tableur. Ce ne sont pas des rapports : ils ne "
    "sont ni mis en page ni commentés.": (
        "CSV files to open in a spreadsheet. These are not reports: they are neither "
        "laid out nor explained.",
        "Archivos CSV para abrir en una hoja de cálculo. No son informes: no están ni "
        "maquetados ni comentados.",
        "Rakitra CSV hovakiana amin'ny tabilao. Tsy tatitra ireo : tsy voalamina ary "
        "tsy misy fanazavana."),
    "Prêts de l'année (CSV)": ("This year's loans (CSV)",
                               "Préstamos del año (CSV)",
                               "Fampindramana amin'ny taona (CSV)"),
    "Un fichier par période : ajoutez ?p=month ou des dates à l'adresse.": (
        "One file per period: add ?p=month or dates to the address.",
        "Un archivo por período: añada ?p=month o fechas a la dirección.",
        "Rakitra iray isaky ny vanim-potoana : ampio ?p=month na daty ao amin'ny adiresy."),
    "Imprimer (PDF)": ("Print (PDF)", "Imprimir (PDF)", "Atontay (PDF)"),
    "Fichier Excel": ("Excel file", "Archivo Excel", "Rakitra Excel"),
    "Sommaire": ("Contents", "Sumario", "Mpiatrika"),
    "Aller à :": ("Go to:", "Ir a:", "Mankany:"),
    "Aucun chiffre à montrer pour cette période.": (
        "No figures to show for this period.",
        "Ninguna cifra que mostrar para este período.",
        "Tsy misy isa aseho amin'io vanim-potoana io."),
    "Rien à afficher pour cette période.": ("Nothing to show for this period.",
                                            "Nada que mostrar para este período.",
                                            "Tsy misy aseho amin'io vanim-potoana io."),
    # ── Corrections temp2 : sous-rapports, données brutes rapatriées ──
    "Les présences par animation": ("Attendance by activity",
                                    "Las asistencias por actividad",
                                    "Ny fanatrehana araka ny hetsika"),
    "Le catalogue complet": ("The whole catalogue", "El catálogo completo",
                             "Ny katalaogy manontolo"),
    "Auteurs": ("Authors", "Autores", "Mpanoratra"),
    "Situation": ("Situation", "Situación", "Toe-javatra"),
    "Aucun exemplaire au catalogue.": ("No copies in the catalogue.",
                                       "Ningún ejemplar en el catálogo.",
                                       "Tsy misy kopia ao amin'ny katalaogy."),
    "Un exemplaire par ligne. Pour reprendre le catalogue dans un tableur avec toutes "
    "les colonnes (ISBN, éditeur, année, tags…), utilisez l'export CSV proposé sous ce "
    "tableau.": (
        "One copy per row. To open the catalogue in a spreadsheet with every column "
        "(ISBN, publisher, year, tags…), use the CSV export offered below this table.",
        "Un ejemplar por fila. Para abrir el catálogo en una hoja de cálculo con todas "
        "las columnas (ISBN, editorial, año, etiquetas…), use la exportación CSV "
        "propuesta debajo de esta tabla.",
        "Kopia iray isaky ny andalana. Raha hampiasa ny katalaogy amin'ny tabilao "
        "misy ny tsanganana rehetra (ISBN, mpanonta, taona, marika…), ampiasao ny "
        "fanondranana CSV eo ambanin'ity tabilao ity."),
    "Réservation": ("Hold", "Reserva", "Famandrihana"),
    "Prêts et réservations en cours": ("Current loans and holds",
                                       "Préstamos y reservas en curso",
                                       "Fampindramana sy famandrihana am-perinasa"),
    "Aucun prêt ni réservation en cours.": ("No current loan or hold.",
                                            "Ningún préstamo ni reserva en curso.",
                                            "Tsy misy fampindramana na famandrihana."),
    "Situation d'aujourd'hui : ce tableau ne dépend pas de la période choisie.": (
        "Today's situation: this table does not depend on the chosen period.",
        "Situación de hoy: esta tabla no depende del período elegido.",
        "Toe-javatra androany : tsy miankina amin'ny vanim-potoana nofidina ity tabilao ity."),
    "pas rendu": ("not returned", "no devuelto", "tsy naverina"),
    "Le détail des prêts de la période": ("Every loan of the period",
                                          "El detalle de los préstamos del período",
                                          "Ny antsipirian'ny fampindramana"),
    "Rendu le": ("Returned on", "Devuelto el", "Naverina ny"),
    "Ce qui s'est passé pendant la période": ("What happened during the period",
                                              "Lo que pasó durante el período",
                                              "Izay nitranga nandritra ny vanim-potoana"),
    "Présences": ("Attendances", "Asistencias", "Fanatrehana"),
    "Les huit premières lignes décrivent la situation d'aujourd'hui et ne dépendent "
    "pas de la période choisie. Le graphe ne montre que les cinq chiffres de la "
    "période, les seuls comparables entre eux.": (
        "The first eight rows describe today's situation and do not depend on the "
        "chosen period. The chart shows only the five figures of the period, the only "
        "ones comparable with each other.",
        "Las ocho primeras filas describen la situación de hoy y no dependen del "
        "período elegido. El gráfico solo muestra las cinco cifras del período, las "
        "únicas comparables entre sí.",
        "Ny andalana valo voalohany dia mamaritra ny toe-javatra androany ary tsy "
        "miankina amin'ny vanim-potoana nofidina. Ny sary dia tsy maneho afa-tsy ny "
        "isa dimy amin'ny vanim-potoana, izay ireo ihany no azo ampitahaina."),
    "Entre deux dates": ("Between two dates", "Entre dos fechas",
                         "Eo anelanelan'ny daty roa"),
    "Sortir toutes les colonnes (CSV)": ("Export every column (CSV)",
                                         "Exportar todas las columnas (CSV)",
                                         "Hamoaka ny tsanganana rehetra (CSV)"),
    "Fichiers destinés à un tableur, avec toutes les colonnes de la base — bien plus "
    "que ce que les tableaux ci-dessus affichent. Ils ne sont ni mis en page ni "
    "commentés.": (
        "Files meant for a spreadsheet, with every column in the database — far more "
        "than the tables above show. They are neither laid out nor explained.",
        "Archivos destinados a una hoja de cálculo, con todas las columnas de la base "
        "— mucho más de lo que muestran las tablas anteriores. No están ni maquetados "
        "ni comentados.",
        "Rakitra ho an'ny tabilao, misy ny tsanganana rehetra ao amin'ny banky angona "
        "— mihoatra lavitra noho izay asehon'ny tabilao etsy ambony. Tsy voalamina "
        "ary tsy misy fanazavana."),
    "Une ligne par exemplaire : ISBN, éditeur, année, tags, résumé, provenance…": (
        "One row per copy: ISBN, publisher, year, tags, summary, source…",
        "Una fila por ejemplar: ISBN, editorial, año, etiquetas, resumen, procedencia…",
        "Andalana iray isaky ny kopia : ISBN, mpanonta, taona, marika, famintinana, fiaviana…"),
    "La situation d'aujourd'hui, prêts et réservations dans un même fichier.": (
        "Today's situation, loans and holds in a single file.",
        "La situación de hoy, préstamos y reservas en un mismo archivo.",
        "Ny toe-javatra androany, fampindramana sy famandrihana ao anaty rakitra iray."),
    "Les prêts de la période (CSV)": ("The period's loans (CSV)",
                                      "Los préstamos del período (CSV)",
                                      "Ny fampindramana amin'ny vanim-potoana (CSV)"),
    "Tous les prêts de la période affichée en haut de l'écran.": (
        "Every loan of the period shown at the top of the screen.",
        "Todos los préstamos del período mostrado arriba en la pantalla.",
        "Ny fampindramana rehetra amin'ny vanim-potoana aseho eo ambony."),
    "Chaque écran s'imprime en PDF et s'enregistre en Excel, en entier ou tableau par "
    "tableau.": (
        "Every screen prints to PDF and saves to Excel, whole or table by table.",
        "Cada pantalla se imprime en PDF y se guarda en Excel, entera o tabla por tabla.",
        "Ny efijery tsirairay dia atonta PDF ary tehirizina Excel, manontolo na isaky "
        "ny tabilao."),
    "Imprimer ce tableau seul": ("Print this table only", "Imprimir solo esta tabla",
                                 "Atontay ity tabilao ity irery"),
    "PDF": ("PDF", "PDF", "PDF"),
    "Enregistrer ce tableau seul": ("Save this table only", "Guardar solo esta tabla",
                                    "Tehirizo ity tabilao ity irery"),
    "Excel": ("Excel", "Excel", "Excel"),
    # ── Second retour de Val : renommages et bilan complet ──
    "Usagers perdus": ("Members lost", "Usuarios perdidos", "Mpampiasa very"),
    "carte périmée sur la période et non renouvelée": (
        "card expired during the period and not renewed",
        "tarjeta vencida en el período y no renovada",
        "karatra lany daty nandritra ny vanim-potoana ary tsy nohavaozina"),
    "Le bilan en un graphe": ("The summary in one chart", "El balance en un gráfico",
                              "Ny fintina amin'ny sary iray"),
    "Les huit premières lignes décrivent la situation d'aujourd'hui et ne dépendent "
    "pas de la période choisie ; les suivantes portent sur la période. L'argent "
    "encaissé ne figure pas dans le graphe : un montant ne se compare pas à un "
    "nombre de livres.": (
        "The first eight rows describe today's situation and do not depend on the "
        "chosen period; the rest cover the period. Money collected is left out of "
        "the chart: an amount cannot be compared with a number of books.",
        "Las ocho primeras filas describen la situación de hoy y no dependen del "
        "período elegido; las siguientes cubren el período. El dinero cobrado no "
        "figura en el gráfico: un importe no se compara con un número de libros.",
        "Ny andalana valo voalohany dia mamaritra ny toe-javatra androany ary tsy "
        "miankina amin'ny vanim-potoana nofidina ; ny manaraka dia mikasika ny "
        "vanim-potoana. Tsy ao anatin'ny sary ny vola voaray : tsy azo ampitahaina "
        "amin'ny isan'ny boky ny vola."),
    # ── Deux dernières features : double histogramme, bilan comparé ──
    "Les livres et les prêts par rayon": (
        "Books and loans by section",
        "Los libros y los préstamos por sección",
        "Ny boky sy ny fampindramana araka ny sokajy"),
    "Les huit premières lignes décrivent la situation d'aujourd'hui : elles ne "
    "dépendent pas de la période choisie et n'ont donc rien à comparer. Les suivantes "
    "portent sur la période.": (
        "The first eight rows describe today's situation: they do not depend on the "
        "chosen period and so have nothing to compare with. The rest cover the period.",
        "Las ocho primeras filas describen la situación de hoy: no dependen del "
        "período elegido y por tanto no tienen nada que comparar. Las siguientes "
        "cubren el período.",
        "Ny andalana valo voalohany dia mamaritra ny toe-javatra androany : tsy "
        "miankina amin'ny vanim-potoana nofidina izy ka tsy misy azo ampitahaina. "
        "Ny manaraka dia mikasika ny vanim-potoana."),
}



TRANSLATIONS = {
    "en": {fr: values[0] for fr, values in TABLE.items()},
    "es": {fr: values[1] for fr, values in TABLE.items()},
    "mg": {fr: values[2] for fr, values in TABLE.items()},
}

PLURALS: dict = {"en": {}, "es": {}, "mg": {}}


def _unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _read_value(lines: list[str], start: int, keyword: str) -> tuple[str, int]:
    first = lines[start][len(keyword):].strip()
    parts = [_unescape(first.strip('"'))]
    i = start + 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(_unescape(lines[i].strip().strip('"')))
        i += 1
    return "".join(parts), i


def _clean_comments(block: list[str]) -> list[str]:
    out = []
    for line in block:
        if line.startswith("#|"):
            continue
        if line.startswith("#,"):
            flags = [f.strip() for f in line[2:].split(",") if f.strip() != "fuzzy"]
            if not flags:
                continue
            line = "#, " + ", ".join(flags)
        out.append(line)
    return out


def apply_lang(lang: str) -> tuple[int, int]:
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0, 0
    singles = TRANSLATIONS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []
    applied = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#") or not line.strip():
            pending.append(line)
            i += 1
            continue
        if line.startswith("msgid "):
            msgid, j = _read_value(lines, i, "msgid ")
            block_msgid = lines[i:j]
            if j < len(lines) and lines[j].startswith("msgstr "):
                _msgstr, k = _read_value(lines, j, "msgstr ")
                translation = singles.get(msgid)
                if translation:
                    out.extend(_clean_comments(pending))
                    out.extend(block_msgid)
                    out.append(f'msgstr "{_escape(translation)}"')
                    applied += 1
                else:
                    out.extend(pending)
                    out.extend(lines[i:k])
                pending = []
                i = k
                continue
        out.extend(pending)
        pending = []
        out.append(line)
        i += 1
    out.extend(pending)

    po_path.write_bytes(("\n".join(out) + "\n").encode("utf-8"))
    return applied, len(singles)


def main() -> None:
    for lang in ("en", "es", "mg"):
        applied, total = apply_lang(lang)
        print(f"[{lang}] {applied}/{total} traductions appliquées")


if __name__ == "__main__":
    main()
