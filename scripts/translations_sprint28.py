#!/usr/bin/env python3
"""Traductions Sprint 28 — FR → EN/ES/MG.

Couvre FEAT-063 (code Ofelia externe), FEAT-064 (provenance + recherche par
exemplaire), FEAT-065 (langues parlées), FEAT-066 (enfants rattachés),
FEAT-067 (catégorie abrégée + écran Catégories) et FEAT-068 (étiquettes de
tranche).

Nouveauté de ce sprint : le dictionnaire `PLURALS` traite aussi les blocs
`msgid_plural`, que les scripts des sprints précédents laissaient de côté —
d'où quelques entrées antérieures (emplacements, récolement, import Excel)
reprises ici pour solder le retard. `scripts/i18n_check.py` les audite
désormais lui aussi.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint28.py
"""
from __future__ import annotations

import re
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

# Aides longues, factorisées pour garder les dictionnaires lisibles.
_ABBR_HELP = (
    "Cote imprimée sur l'étiquette de tranche. Ex. « RO FI ADO » pour "
    "« Romans fiction pour adolescents »."
)
_PROV_LABEL_HELP = "Nom lisible affiché dans les listes. Ex. « Prêt Bibliothèque de Genève »."
_PROV_NOTES_HELP = "Contact, date de restitution prévue, conditions du dépôt…"
_PROV_DEFAULT_HELP = (
    "Appliquée à tous les exemplaires du lot. Ex. des livres prêtés par une "
    "autre bibliothèque, à retrouver le jour du retour."
)
_EXT_CODE_HELP = "Code déjà porté par le livre, jusqu'à 20 caractères. Ex. BCF13298781X."
_EXT_CODE_INVALID = (
    "Le code externe doit être alphanumérique et faire %(n)s caractères au plus."
)
_EXT_CODE_TAKEN = "Ce code externe est déjà porté par l'exemplaire %(code)s (%(title)s)."
_EXT_CODE_SINGLE = (
    "Un code externe ne peut être attribué qu'à un seul exemplaire : créez-les "
    "sans code, puis saisissez le code sur l'exemplaire concerné."
)
_NO_ABBR = (
    "Aucun exemplaire sélectionné n'a de catégorie abrégée : renseignez "
    "l'abréviation de la catégorie avant d'imprimer."
)
_ABBR_GONE = (
    "L'abréviation « %(abbr)s » disparaît : les étiquettes de tranche déjà "
    "collées restent, mais ne pourront plus être réimprimées."
)
_ABBR_WHAT = (
    "C'est la cote qui part sur l'étiquette de tranche, pour ranger le livre au "
    "bon rayon sans le sortir de l'étagère. Exemple : « RO FI ADO » pour "
    "« Romans fiction pour adolescents »."
)
_ABBR_SCOPE = (
    "Elle vaut pour toutes les notices de la catégorie. Les étiquettes "
    "s'impriment depuis Impressions → Étiquettes."
)
_XLS_DUP = (
    "Code externe déjà porté par un autre exemplaire : code ignoré, le reste de "
    "la ligne est importé."
)
_XLS_INVALID = (
    "Code externe refusé : il doit être alphanumérique et faire 20 caractères au "
    "plus. Le reste de la ligne est importé."
)
_DEL_FINAL = "Cette suppression est définitive. Les notices, elles, restent au catalogue."
_DEL_HISTORY = "L'historique de prêts et de consultations de ces exemplaires est effacé."
_DEL_TOMBSTONE = (
    "Leurs codes Ofelia sont mis de côté définitivement : ils ne seront jamais "
    "réattribués à un autre livre, même si l'étiquette a déjà été imprimée."
)
_PROV_BLOCKED = (
    "Effacer la provenance ferait perdre la trace de l'origine de ces "
    "exemplaires. Traitez-les d'abord : rattachez-les à une autre provenance, "
    "ou supprimez-les si le fonds est rendu."
)
_PROV_FREE = "Aucun exemplaire ne la porte : la suppression n'a aucun effet sur le catalogue."
_PROV_SUB = "D'où viennent les exemplaires : achat, don, prêt d'une autre bibliothèque…"
_PROV_EMPTY = "Aucune provenance définie. Cliquez sur « Nouvelle provenance » pour commencer."
_PROV_WHY_1 = (
    "La provenance suit l'exemplaire, pas le titre : un même livre peut avoir un "
    "exemplaire acheté par la bibliothèque et un autre prêté par une "
    "bibliothèque partenaire."
)
_PROV_WHY_2 = (
    "Le jour où il faut rendre un fonds, ouvrez le catalogue, cochez « Chercher "
    "les exemplaires », filtrez sur la provenance : vous obtenez la liste exacte "
    "des livres à sortir."
)
_ADV_CATEGORIES = (
    "Classement des notices et abréviation imprimée sur la tranche des livres "
    "(« RO FI ADO »)."
)
_ADV_PROVENANCES = (
    "D'où viennent les exemplaires (achat, don, prêt d'une autre bibliothèque). "
    "Permet de retrouver et de rendre un fonds entier."
)
_CAT_SUB = "Classement des notices et cote imprimée sur la tranche des livres"
_CHILDREN_HELP = (
    "Les enfants qui accompagnent cet usager. Ils n'ont pas de carte : ces "
    "informations servent à leur proposer les bons livres."
)
_NO_IMPACT = "Aucun impact : usager sans prêt, réservation ni enfant rattaché."
_LANG_OTHER_HELP = "Langues absentes de la liste, séparées par des virgules."


# ── 2e vague (retours Val du 2026-08-20) : BUG-027, FEAT-069 à FEAT-072 ──
_PROV_EMPTY_HELP = (
    "Aucune provenance n'existe encore : créez-en une depuis Avancé → Provenances."
)
_LANG_CODE_HELP = (
    "Abréviation internationale principale, sans variante régionale : fr, en, "
    "pt, de… (« fr » couvre le français de France, du Canada et de Suisse)."
)
_LANG_NAME_HELP = "Nom de la langue dans la langue de saisie courante."
_NOTHING_TO_CHANGE = "Rien à modifier : aucun menu n'a été changé."
_BIRTH_YEAR_HELP = "Pour un enfant : l'âge est calculé."
_XLS_EXT_COL = "optionnel : code d'une autre bibliothèque déjà posé sur le livre"
_XLS_PROV_COL = "optionnel : code ou nom d'une provenance existante"
_XLS_ABBR_COL = "optionnel : abréviation (cote) de la catégorie indiquée en CATEGORY"
_LANG_DEL_CONFIRM = "Confirmez-vous le retrait de <strong>%(name)s</strong> de la liste ?"
_LANG_DEL_NO_RECORD = "Aucune notice n'est supprimée ni modifiée."
_LANG_DEL_EFFECT = (
    "La langue ne sera plus proposée à la saisie, ni pour un livre ni pour un usager."
)
_LANG_SUB = "Langues des livres et langues parlées par les usagers"
_LANG_ONE_LIST = "Une seule liste, deux usages"
_LANG_ONE_LIST_1 = (
    "Cette liste alimente à la fois la langue d'un livre et les langues parlées "
    "d'un usager. Ajoutez-y une langue dès qu'un livre ou un lecteur l'exige."
)
_LANG_ONE_LIST_2 = (
    "Utilisez les abréviations internationales principales, sans variante "
    "régionale : « fr » couvre le français de France, du Canada et de Suisse, "
    "« pt » le portugais et le brésilien."
)
_LANG_ONE_LIST_3 = (
    "Les menus déroulants sont triés par ordre alphabétique dans la langue de "
    "l'interface : l'ordre change donc d'une langue à l'autre."
)
_ADV_LANGUAGES = (
    "Langues proposées pour les livres et pour les langues parlées des usagers. "
    "Complétez la liste si un fonds l'exige."
)
_FAMILY_DELETED = "fiche(s) de famille seront supprimées avec l'usager :"
_NO_IMPACT_FAMILY = "Aucun impact : usager sans prêt, réservation ni personne rattachée."
_FAMILY_HELP = (
    "Les personnes qui partagent cette carte. Elles n'ont pas de carte à leur "
    "nom : ces informations servent à leur proposer les bons livres."
)
_LANG_KEEPS_CODE = (
    "notice garde le code « %(code)s », qui s'affichera tel quel au lieu du nom "
    "traduit."
)
_LANG_KEEPS_CODE_PLURAL = (
    "notices gardent le code « %(code)s », qui s'affichera tel quel au lieu du "
    "nom traduit."
)


TRANSLATIONS = {
    # ── Anglais ───────────────────────────────────────────────────────────
    "en": {
        # ── 4e vague : audit i18n elargi (choices, Meta) ──
        'Superadmin': 'Superadmin',
        'Bibliothécaire': 'Librarian',
        'Contributeur OfeliaScan': 'OfeliaScan contributor',
        'Support / lecture seule': 'Support / read-only',
        'paramètre': 'setting',
        'paramètres': 'settings',
        # ── 3e vague : verbose_name des modeles + FEAT-073 ──
        'rôle': 'role',
        'langue par défaut': 'default language',
        'toujours afficher les options avancées': 'always show advanced options',
        'code': 'code',
        'nom': 'name',
        'nom complet': 'full name',
        'catégorie parente': 'parent category',
        'description': 'description',
        'emplacement parent': 'parent location',
        'notes': 'notes',
        'titre': 'title',
        'sous-titre': 'subtitle',
        'éditeur': 'publisher',
        'année de publication': 'year of publication',
        'ISBN-13': 'ISBN-13',
        'ISBN-10': 'ISBN-10',
        'résumé': 'summary',
        'couverture': 'cover',
        'série': 'series',
        'tome': 'volume',
        'type de document': 'document type',
        'périmètre': 'scope',
        'date': 'date',
        'nombre': 'count',
        'n° de carte': 'card number',
        'date de naissance': 'date of birth',
        'téléphone': 'phone',
        'adresse': 'address',
        "date d'inscription": 'registration date',
        "date d'expiration": 'expiry date',
        'statut': 'status',
        'langue de correspondance': 'language for correspondence',
        'ancienne carte': 'previous card',
        'photo': 'photo',
        'résultats de la recherche': 'results of the search',
        '(toutes les pages)': '(all pages)',
        'Rechercher des notices': 'Search records',
        'Rechercher des exemplaires': 'Search copies',
        # ââ 2e vague ââ
        _PROV_EMPTY_HELP: "No source exists yet: create one from Advanced → Sources.",
        _LANG_CODE_HELP: "Main international abbreviation, without regional variant: fr, en, pt, de… (“fr” covers French from France, Canada and Switzerland).",
        _LANG_NAME_HELP: "Name of the language, in the language you are typing in.",
        "— non précisée —": "— not specified —",
        "langue": "language",
        "langues": "languages",
        "Langues": "Languages",
        "Nouvelle langue": "New language",
        "Modifier la langue": "Edit language",
        "Retirer la langue": "Remove language",
        "Langue ajoutée.": "Language added.",
        "Langue mise à jour.": "Language updated.",
        "Langue retirée de la liste.": "Language removed from the list.",
        "Retirer de la liste": "Remove from the list",
        _LANG_DEL_CONFIRM: "Do you confirm removing <strong>%(name)s</strong> from the list?",
        _LANG_DEL_NO_RECORD: "No record is deleted or modified.",
        _LANG_DEL_EFFECT: "The language will no longer be offered when cataloguing a book or enrolling a member.",
        "Aucune langue définie.": "No language defined yet.",
        _LANG_SUB: "Languages of the books, and languages spoken by the members",
        _LANG_ONE_LIST: "One list, two uses",
        _LANG_ONE_LIST_1: "This list feeds both a book’s language and a member’s spoken languages. Add a language to it as soon as a book or a reader needs one.",
        _LANG_ONE_LIST_2: "Use the main international abbreviations, without regional variants: “fr” covers French from France, Canada and Switzerland, “pt” covers Portuguese and Brazilian.",
        _LANG_ONE_LIST_3: "Drop-down lists are sorted alphabetically in the interface language, so the order changes from one language to another.",
        _ADV_LANGUAGES: "Languages offered for books and for members’ spoken languages. Extend the list if a collection needs it.",
        "Ne pas modifier": "Leave unchanged",
        "— (vider)": "— (clear)",
        "Affecter": "Apply",
        _NOTHING_TO_CHANGE: "Nothing to change: no drop-down was touched.",
        "%(n)s notice(s) → catégorie %(v)s": "%(n)s record(s) → category %(v)s",
        "%(n)s notice(s) sans catégorie": "%(n)s record(s) with no category",
        "%(n)s exemplaire(s) → emplacement %(v)s": "%(n)s copy/copies → location %(v)s",
        "%(n)s exemplaire(s) sans emplacement": "%(n)s copy/copies with no location",
        "%(n)s exemplaire(s) → provenance %(v)s": "%(n)s copy/copies → source %(v)s",
        "%(n)s exemplaire(s) sans provenance": "%(n)s copy/copies with no source",
        _XLS_EXT_COL: "optional: another library’s code already on the book",
        _XLS_PROV_COL: "optional: code or name of an existing source",
        _XLS_ABBR_COL: "optional: abbreviation (shelf mark) of the category given in CATEGORY",
        "Famille": "Family",
        "Adulte ou enfant": "Adult or child",
        "Enfant": "Child",
        "Adulte": "Adult",
        "Année de naissance": "Year of birth",
        "année de naissance": "year of birth",
        "adulte": "adult",
        _BIRTH_YEAR_HELP: "For a child: the age is worked out from it.",
        "membre de la famille": "family member",
        "membres de la famille": "family members",
        "Ajouter une personne": "Add a person",
        _FAMILY_DELETED: "family record(s) will be deleted along with the member:",
        _NO_IMPACT_FAMILY: "No impact: this member has no loan, no reservation and nobody attached.",
        _FAMILY_HELP: "The people who share this card. They have no card of their own: this is only here to help suggest the right books to them.",
        # FEAT-063 — code Ofelia externe
        "Code Ofelia externe": "External Ofelia code",
        "code Ofelia externe": "external Ofelia code",
        "Code externe": "External code",
        _EXT_CODE_HELP: "Code already on the book, up to 20 characters. E.g. BCF13298781X.",
        _EXT_CODE_INVALID: "The external code must be alphanumeric and at most %(n)s characters long.",
        _EXT_CODE_TAKEN: "This external code already belongs to copy %(code)s (%(title)s).",
        _EXT_CODE_SINGLE: "An external code can only be given to a single copy: create them without a code, then enter the code on the relevant copy.",
        _XLS_DUP: "External code already used by another copy: the code is ignored, the rest of the row is imported.",
        _XLS_INVALID: "External code rejected: it must be alphanumeric and at most 20 characters. The rest of the row is imported.",
        # FEAT-064 — provenance
        "Provenance": "Source",
        "provenance": "source",
        "provenances": "sources",
        "Provenances": "Sources",
        "Nouvelle provenance": "New source",
        "Modifier la provenance": "Edit source",
        "Supprimer la provenance": "Delete source",
        "Provenance créée.": "Source created.",
        "Provenance mise à jour.": "Source updated.",
        "Provenance supprimée.": "Source deleted.",
        "Provenance par défaut": "Default source",
        "Provenance actuelle": "Current source",
        "Toutes provenances": "All sources",
        "Affecter une provenance": "Assign a source",
        "— (vider la provenance)": "— (clear the source)",
        "Nom complet": "Full name",
        "Court, sans espace : OFELIA, BM-GE, DON-DUPONT…": "Short, no spaces: OFELIA, BM-GE, DON-DUPONT…",
        _PROV_LABEL_HELP: "Readable name shown in lists. E.g. “On loan from Geneva Library”.",
        _PROV_NOTES_HELP: "Contact, expected return date, terms of the deposit…",
        _PROV_DEFAULT_HELP: "Applied to every copy in the batch. E.g. books lent by another library, to be found again on the day they go back.",
        "Impossible : %(n)s exemplaire(s) portent encore cette provenance.": "Not possible: %(n)s copy/copies still have this source.",
        "%(n)s exemplaire(s) rattaché(s) à la provenance %(p)s.": "%(n)s copy/copies attached to source %(p)s.",
        "%(n)s exemplaire(s) sans provenance (provenance vidée).": "%(n)s copy/copies with no source (source cleared).",
        "%(n)s exemplaire(s) supprimé(s).": "%(n)s copy/copies deleted.",
        _PROV_BLOCKED: "Deleting the source would lose track of where these copies came from. Deal with them first: attach them to another source, or delete them if the collection is going back.",
        _PROV_FREE: "No copy uses it: deleting it has no effect on the catalogue.",
        _PROV_SUB: "Where the copies come from: purchase, donation, loan from another library…",
        _PROV_EMPTY: "No source defined yet. Click “New source” to start.",
        _PROV_WHY_1: "The source follows the copy, not the title: the same book can have one copy bought by the library and another lent by a partner library.",
        _PROV_WHY_2: "When a collection has to go back, open the catalogue, tick “Search copies” and filter on the source: you get the exact list of books to pull off the shelves.",
        "À quoi ça sert": "What it is for",
        "Voir ces exemplaires": "View these copies",
        "Confirmez-vous la suppression de la provenance <strong>%(code)s</strong> ?": "Do you confirm the deletion of source <strong>%(code)s</strong>?",
        _ADV_PROVENANCES: "Where the copies come from (purchase, donation, loan from another library). Lets you find and return a whole collection.",
        # FEAT-064 — recherche par exemplaire
        "Chercher les exemplaires": "Search copies",
        "exemplaire(s) sélectionné(s)": "copy/copies selected",
        "Supprimer les exemplaires sélectionnés": "Delete the selected copies",
        "Supprimer des exemplaires": "Delete copies",
        "Exemplaires concernés": "Copies affected",
        _DEL_FINAL: "This deletion is final. The records themselves stay in the catalogue.",
        _DEL_HISTORY: "The loan and in-house reading history of these copies is erased.",
        _DEL_TOMBSTONE: "Their Ofelia codes are permanently set aside: they will never be given to another book, even if the label has already been printed.",
        # FEAT-067 — catégories
        "Catégories": "Categories",
        "Abréviation": "Abbreviation",
        "abréviation": "abbreviation",
        "Catégorie parente": "Parent category",
        "Durée de prêt (jours)": "Loan period (days)",
        "Court, sans espace : ENF-ALB, ADU-ROM…": "Short, no spaces: ENF-ALB, ADU-ROM…",
        _ABBR_HELP: "Shelf mark printed on the spine label. E.g. “RO FI ADO” for “Teen fiction novels”.",
        "Sous-catégorie de… (optionnel).": "Sub-category of… (optional).",
        "Vide = durée par défaut de la bibliothèque.": "Empty = the library's default period.",
        "Catégorie créée.": "Category created.",
        "Catégorie mise à jour.": "Category updated.",
        "Catégorie supprimée.": "Category deleted.",
        "Modifier la catégorie": "Edit category",
        "Supprimer la catégorie": "Delete category",
        "Nouvelle": "New",
        "Aucune catégorie définie.": "No category defined yet.",
        "L'abréviation": "The abbreviation",
        _ABBR_WHAT: "This is the shelf mark that goes on the spine label, so a book can be shelved in the right place without pulling it off the shelf. Example: “RO FI ADO” for “Teen fiction novels”.",
        _ABBR_SCOPE: "It applies to every record in the category. Labels are printed from Printing → Labels.",
        _ABBR_GONE: "The abbreviation “%(abbr)s” disappears: spine labels already stuck on books stay, but they can no longer be reprinted.",
        "Confirmez-vous la suppression de la catégorie <strong>%(code)s</strong> ?": "Do you confirm the deletion of category <strong>%(code)s</strong>?",
        _CAT_SUB: "Classification of records and the shelf mark printed on book spines",
        "Cote imprimée sur la tranche": "Shelf mark printed on the spine",
        _ADV_CATEGORIES: "Classification of records and the abbreviation printed on book spines (“RO FI ADO”).",
        # FEAT-068 — étiquettes de tranche
        "Étiquettes de tranche": "Spine labels",
        _NO_ABBR: "None of the selected copies has an abbreviated category: fill in the category abbreviation before printing.",
        # FEAT-065 — langues parlées
        "Langues parlées": "Spoken languages",
        "langues parlées": "spoken languages",
        "Autres langues": "Other languages",
        "autres langues": "other languages",
        _LANG_OTHER_HELP: "Languages not in the list, separated by commas.",
        "Français": "French",
        "Anglais": "English",
        "Portugais": "Portuguese",
        "Espagnol": "Spanish",
        "Italien": "Italian",
        "Allemand": "German",
        "Arabe": "Arabic",
        "Albanais": "Albanian",
        "Turc": "Turkish",
        "Russe": "Russian",
        "Serbo-croate": "Serbo-Croatian",
        "Tamoul": "Tamil",
        "Chinois": "Chinese",
        "Polonais": "Polish",
        "Persan": "Persian",
        "Farsi": "Farsi",
        "Grec": "Greek",
        "Somali": "Somali",
        "Roumain": "Romanian",
        "Ukrainien": "Ukrainian",
        "Japonais": "Japanese",
        "Malgache": "Malagasy",
        # FEAT-066 — enfants
        "Enfants": "Children",
        "enfant": "child",
        "enfants": "children",
        "Ajouter un enfant": "Add a child",
        "Sexe": "Sex",
        "sexe": "sex",
        "Âge": "Age",
        "âge": "age",
        "prénom": "first name",
        "Fille": "Girl",
        "Garçon": "Boy",
        "%(n)s ans": "%(n)s years old",
        _CHILDREN_HELP: "The children who come along with this member. They have no card: this is only here to help suggest the right books to them.",
        "fiche(s) enfant seront supprimées avec l'usager :": "child record(s) will be deleted along with the member:",
        _NO_IMPACT: "No impact: this member has no loan, no reservation and no child attached.",
    },
    # ── Espagnol ──────────────────────────────────────────────────────────
    "es": {
        # ── 4e vague : audit i18n elargi (choices, Meta) ──
        'Superadmin': 'Superadministrador',
        'Bibliothécaire': 'Bibliotecario',
        'Contributeur OfeliaScan': 'Colaborador OfeliaScan',
        'Support / lecture seule': 'Soporte / solo lectura',
        'paramètre': 'ajuste',
        'paramètres': 'ajustes',
        # ── 3e vague : verbose_name des modeles + FEAT-073 ──
        'rôle': 'rol',
        'langue par défaut': 'idioma por defecto',
        'toujours afficher les options avancées': 'mostrar siempre las opciones avanzadas',
        'code': 'código',
        'nom': 'nombre',
        'nom complet': 'nombre completo',
        'catégorie parente': 'categoría superior',
        'description': 'descripción',
        'emplacement parent': 'ubicación superior',
        'notes': 'notas',
        'titre': 'título',
        'sous-titre': 'subtítulo',
        'éditeur': 'editorial',
        'année de publication': 'año de publicación',
        'ISBN-13': 'ISBN-13',
        'ISBN-10': 'ISBN-10',
        'résumé': 'resumen',
        'couverture': 'portada',
        'série': 'serie',
        'tome': 'tomo',
        'type de document': 'tipo de documento',
        'périmètre': 'alcance',
        'date': 'fecha',
        'nombre': 'cantidad',
        'n° de carte': 'n.º de carné',
        'date de naissance': 'fecha de nacimiento',
        'téléphone': 'teléfono',
        'adresse': 'dirección',
        "date d'inscription": 'fecha de inscripción',
        "date d'expiration": 'fecha de caducidad',
        'statut': 'estado',
        'langue de correspondance': 'idioma de correspondencia',
        'ancienne carte': 'carné anterior',
        'photo': 'foto',
        'résultats de la recherche': 'resultados de la búsqueda',
        '(toutes les pages)': '(todas las páginas)',
        'Rechercher des notices': 'Buscar registros',
        'Rechercher des exemplaires': 'Buscar ejemplares',
        # ââ 2e vague ââ
        _PROV_EMPTY_HELP: "Todavía no existe ninguna procedencia: cree una desde Avanzado → Procedencias.",
        _LANG_CODE_HELP: "Abreviatura internacional principal, sin variante regional: fr, en, pt, de… (“fr” cubre el francés de Francia, Canadá y Suiza).",
        _LANG_NAME_HELP: "Nombre del idioma, en el idioma en que está escribiendo.",
        "— non précisée —": "— sin especificar —",
        "langue": "idioma",
        "langues": "idiomas",
        "Langues": "Idiomas",
        "Nouvelle langue": "Nuevo idioma",
        "Modifier la langue": "Editar el idioma",
        "Retirer la langue": "Quitar el idioma",
        "Langue ajoutée.": "Idioma añadido.",
        "Langue mise à jour.": "Idioma actualizado.",
        "Langue retirée de la liste.": "Idioma retirado de la lista.",
        "Retirer de la liste": "Quitar de la lista",
        _LANG_DEL_CONFIRM: "¿Confirma que quiere quitar <strong>%(name)s</strong> de la lista?",
        _LANG_DEL_NO_RECORD: "No se elimina ni se modifica ningún registro.",
        _LANG_DEL_EFFECT: "El idioma ya no se ofrecerá al catalogar un libro ni al inscribir a un usuario.",
        "Aucune langue définie.": "No hay ningún idioma definido.",
        _LANG_SUB: "Idiomas de los libros e idiomas hablados por los usuarios",
        _LANG_ONE_LIST: "Una sola lista, dos usos",
        _LANG_ONE_LIST_1: "Esta lista alimenta a la vez el idioma de un libro y los idiomas hablados de un usuario. Añada un idioma en cuanto un libro o un lector lo necesite.",
        _LANG_ONE_LIST_2: "Use las abreviaturas internacionales principales, sin variantes regionales: “fr” cubre el francés de Francia, Canadá y Suiza, “pt” cubre el portugués y el brasileño.",
        _LANG_ONE_LIST_3: "Los menús desplegables se ordenan alfabéticamente en el idioma de la interfaz, así que el orden cambia de un idioma a otro.",
        _ADV_LANGUAGES: "Idiomas ofrecidos para los libros y para los idiomas hablados de los usuarios. Amplíe la lista si un fondo lo exige.",
        "Ne pas modifier": "No modificar",
        "— (vider)": "— (vaciar)",
        "Affecter": "Aplicar",
        _NOTHING_TO_CHANGE: "Nada que modificar: no se ha tocado ningún menú.",
        "%(n)s notice(s) → catégorie %(v)s": "%(n)s registro(s) → categoría %(v)s",
        "%(n)s notice(s) sans catégorie": "%(n)s registro(s) sin categoría",
        "%(n)s exemplaire(s) → emplacement %(v)s": "%(n)s ejemplar(es) → ubicación %(v)s",
        "%(n)s exemplaire(s) sans emplacement": "%(n)s ejemplar(es) sin ubicación",
        "%(n)s exemplaire(s) → provenance %(v)s": "%(n)s ejemplar(es) → procedencia %(v)s",
        "%(n)s exemplaire(s) sans provenance": "%(n)s ejemplar(es) sin procedencia",
        _XLS_EXT_COL: "opcional: código de otra biblioteca ya puesto en el libro",
        _XLS_PROV_COL: "opcional: código o nombre de una procedencia existente",
        _XLS_ABBR_COL: "opcional: abreviatura (signatura) de la categoría indicada en CATEGORY",
        "Famille": "Familia",
        "Adulte ou enfant": "Adulto o niño",
        "Enfant": "Niño",
        "Adulte": "Adulto",
        "Année de naissance": "Año de nacimiento",
        "année de naissance": "año de nacimiento",
        "adulte": "adulto",
        _BIRTH_YEAR_HELP: "Para un niño: la edad se calcula a partir de él.",
        "membre de la famille": "miembro de la familia",
        "membres de la famille": "miembros de la familia",
        "Ajouter une personne": "Añadir una persona",
        _FAMILY_DELETED: "ficha(s) de familia se eliminarán junto con el usuario:",
        _NO_IMPACT_FAMILY: "Sin impacto: usuario sin préstamos, sin reservas y sin nadie a su cargo.",
        _FAMILY_HELP: "Las personas que comparten este carné. No tienen carné propio: esta información solo sirve para proponerles los libros adecuados.",
        "Code Ofelia externe": "Código Ofelia externo",
        "code Ofelia externe": "código Ofelia externo",
        "Code externe": "Código externo",
        _EXT_CODE_HELP: "Código que el libro ya lleva, hasta 20 caracteres. Ej. BCF13298781X.",
        _EXT_CODE_INVALID: "El código externo debe ser alfanumérico y tener como máximo %(n)s caracteres.",
        _EXT_CODE_TAKEN: "Este código externo ya pertenece al ejemplar %(code)s (%(title)s).",
        _EXT_CODE_SINGLE: "Un código externo solo puede asignarse a un ejemplar: créelos sin código y luego escriba el código en el ejemplar correspondiente.",
        _XLS_DUP: "Código externo ya usado por otro ejemplar: se ignora el código, el resto de la fila se importa.",
        _XLS_INVALID: "Código externo rechazado: debe ser alfanumérico y tener como máximo 20 caracteres. El resto de la fila se importa.",
        "Provenance": "Procedencia",
        "provenance": "procedencia",
        "provenances": "procedencias",
        "Provenances": "Procedencias",
        "Nouvelle provenance": "Nueva procedencia",
        "Modifier la provenance": "Editar la procedencia",
        "Supprimer la provenance": "Eliminar la procedencia",
        "Provenance créée.": "Procedencia creada.",
        "Provenance mise à jour.": "Procedencia actualizada.",
        "Provenance supprimée.": "Procedencia eliminada.",
        "Provenance par défaut": "Procedencia por defecto",
        "Provenance actuelle": "Procedencia actual",
        "Toutes provenances": "Todas las procedencias",
        "Affecter une provenance": "Asignar una procedencia",
        "— (vider la provenance)": "— (vaciar la procedencia)",
        "Nom complet": "Nombre completo",
        "Court, sans espace : OFELIA, BM-GE, DON-DUPONT…": "Corto, sin espacios: OFELIA, BM-GE, DON-DUPONT…",
        _PROV_LABEL_HELP: "Nombre legible que aparece en las listas. Ej. “Préstamo Biblioteca de Ginebra”.",
        _PROV_NOTES_HELP: "Contacto, fecha de devolución prevista, condiciones del depósito…",
        _PROV_DEFAULT_HELP: "Se aplica a todos los ejemplares del lote. Ej. libros prestados por otra biblioteca, que habrá que localizar el día de la devolución.",
        "Impossible : %(n)s exemplaire(s) portent encore cette provenance.": "Imposible: %(n)s ejemplar(es) todavía tienen esta procedencia.",
        "%(n)s exemplaire(s) rattaché(s) à la provenance %(p)s.": "%(n)s ejemplar(es) asignado(s) a la procedencia %(p)s.",
        "%(n)s exemplaire(s) sans provenance (provenance vidée).": "%(n)s ejemplar(es) sin procedencia (procedencia vaciada).",
        "%(n)s exemplaire(s) supprimé(s).": "%(n)s ejemplar(es) eliminado(s).",
        _PROV_BLOCKED: "Borrar la procedencia haría perder el rastro del origen de estos ejemplares. Trátelos primero: asígnelos a otra procedencia o elimínelos si el fondo se devuelve.",
        _PROV_FREE: "Ningún ejemplar la usa: eliminarla no afecta al catálogo.",
        _PROV_SUB: "De dónde vienen los ejemplares: compra, donación, préstamo de otra biblioteca…",
        _PROV_EMPTY: "No hay ninguna procedencia definida. Haga clic en “Nueva procedencia” para empezar.",
        _PROV_WHY_1: "La procedencia acompaña al ejemplar, no al título: un mismo libro puede tener un ejemplar comprado por la biblioteca y otro prestado por una biblioteca asociada.",
        _PROV_WHY_2: "El día que hay que devolver un fondo, abra el catálogo, marque “Buscar los ejemplares” y filtre por procedencia: obtendrá la lista exacta de los libros que hay que sacar.",
        "À quoi ça sert": "Para qué sirve",
        "Voir ces exemplaires": "Ver estos ejemplares",
        "Confirmez-vous la suppression de la provenance <strong>%(code)s</strong> ?": "¿Confirma la eliminación de la procedencia <strong>%(code)s</strong>?",
        _ADV_PROVENANCES: "De dónde vienen los ejemplares (compra, donación, préstamo de otra biblioteca). Permite localizar y devolver un fondo entero.",
        "Chercher les exemplaires": "Buscar los ejemplares",
        "exemplaire(s) sélectionné(s)": "ejemplar(es) seleccionado(s)",
        "Supprimer les exemplaires sélectionnés": "Eliminar los ejemplares seleccionados",
        "Supprimer des exemplaires": "Eliminar ejemplares",
        "Exemplaires concernés": "Ejemplares afectados",
        _DEL_FINAL: "Esta eliminación es definitiva. Los registros siguen en el catálogo.",
        _DEL_HISTORY: "Se borra el historial de préstamos y consultas de estos ejemplares.",
        _DEL_TOMBSTONE: "Sus códigos Ofelia quedan apartados definitivamente: nunca se reasignarán a otro libro, aunque la etiqueta ya esté impresa.",
        "Catégories": "Categorías",
        "Abréviation": "Abreviatura",
        "abréviation": "abreviatura",
        "Catégorie parente": "Categoría superior",
        "Durée de prêt (jours)": "Duración del préstamo (días)",
        "Court, sans espace : ENF-ALB, ADU-ROM…": "Corto, sin espacios: ENF-ALB, ADU-ROM…",
        _ABBR_HELP: "Signatura impresa en la etiqueta de lomo. Ej. “RO FI ADO” para “Novelas de ficción para adolescentes”.",
        "Sous-catégorie de… (optionnel).": "Subcategoría de… (opcional).",
        "Vide = durée par défaut de la bibliothèque.": "Vacío = duración por defecto de la biblioteca.",
        "Catégorie créée.": "Categoría creada.",
        "Catégorie mise à jour.": "Categoría actualizada.",
        "Catégorie supprimée.": "Categoría eliminada.",
        "Modifier la catégorie": "Editar la categoría",
        "Supprimer la catégorie": "Eliminar la categoría",
        "Nouvelle": "Nueva",
        "Aucune catégorie définie.": "No hay ninguna categoría definida.",
        "L'abréviation": "La abreviatura",
        _ABBR_WHAT: "Es la signatura que va en la etiqueta de lomo, para colocar el libro en el estante correcto sin sacarlo. Ejemplo: “RO FI ADO” para “Novelas de ficción para adolescentes”.",
        _ABBR_SCOPE: "Vale para todos los registros de la categoría. Las etiquetas se imprimen desde Impresiones → Etiquetas.",
        _ABBR_GONE: "La abreviatura “%(abbr)s” desaparece: las etiquetas de lomo ya pegadas se quedan, pero no se podrán volver a imprimir.",
        "Confirmez-vous la suppression de la catégorie <strong>%(code)s</strong> ?": "¿Confirma la eliminación de la categoría <strong>%(code)s</strong>?",
        _CAT_SUB: "Clasificación de los registros y signatura impresa en el lomo de los libros",
        "Cote imprimée sur la tranche": "Signatura impresa en el lomo",
        _ADV_CATEGORIES: "Clasificación de los registros y abreviatura impresa en el lomo de los libros (“RO FI ADO”).",
        "Étiquettes de tranche": "Etiquetas de lomo",
        _NO_ABBR: "Ninguno de los ejemplares seleccionados tiene categoría abreviada: rellene la abreviatura de la categoría antes de imprimir.",
        "Langues parlées": "Idiomas hablados",
        "langues parlées": "idiomas hablados",
        "Autres langues": "Otros idiomas",
        "autres langues": "otros idiomas",
        _LANG_OTHER_HELP: "Idiomas que no están en la lista, separados por comas.",
        "Français": "Francés",
        "Anglais": "Inglés",
        "Portugais": "Portugués",
        "Espagnol": "Español",
        "Italien": "Italiano",
        "Allemand": "Alemán",
        "Arabe": "Árabe",
        "Albanais": "Albanés",
        "Turc": "Turco",
        "Russe": "Ruso",
        "Serbo-croate": "Serbocroata",
        "Tamoul": "Tamil",
        "Chinois": "Chino",
        "Polonais": "Polaco",
        "Persan": "Persa",
        "Farsi": "Farsi",
        "Grec": "Griego",
        "Somali": "Somalí",
        "Roumain": "Rumano",
        "Ukrainien": "Ucraniano",
        "Japonais": "Japonés",
        "Malgache": "Malgache",
        "Enfants": "Hijos",
        "enfant": "hijo",
        "enfants": "hijos",
        "Ajouter un enfant": "Añadir un hijo",
        "Sexe": "Sexo",
        "sexe": "sexo",
        "Âge": "Edad",
        "âge": "edad",
        "prénom": "nombre",
        "Fille": "Niña",
        "Garçon": "Niño",
        "%(n)s ans": "%(n)s años",
        _CHILDREN_HELP: "Los niños que acompañan a este usuario. No tienen carné: esta información sirve para proponerles los libros adecuados.",
        "fiche(s) enfant seront supprimées avec l'usager :": "ficha(s) de hijo se eliminarán junto con el usuario:",
        _NO_IMPACT: "Sin impacto: usuario sin préstamos, sin reservas y sin hijos registrados.",
    },
    # ── Malgache ──────────────────────────────────────────────────────────
    "mg": {
        # ── 4e vague : audit i18n elargi (choices, Meta) ──
        'Superadmin': 'Superadmin',
        'Bibliothécaire': 'Mpiandry tranomboky',
        'Contributeur OfeliaScan': 'Mpandray anjara OfeliaScan',
        'Support / lecture seule': 'Fanohanana / famakiana ihany',
        'paramètre': 'safidy',
        'paramètres': 'safidy',
        # ── 3e vague : verbose_name des modeles + FEAT-073 ──
        'rôle': 'andraikitra',
        'langue par défaut': 'fiteny mahazatra',
        'toujours afficher les options avancées': 'asehoy foana ny safidy mandroso',
        'code': 'kaody',
        'nom': 'anarana',
        'nom complet': 'anarana feno',
        'catégorie parente': 'sokajy ambony',
        'description': 'famaritana',
        'emplacement parent': 'toerana ambony',
        'notes': 'fanamarihana',
        'titre': 'lohateny',
        'sous-titre': 'lohateny faharoa',
        'éditeur': 'mpanonta',
        'année de publication': 'taona namoahana',
        'ISBN-13': 'ISBN-13',
        'ISBN-10': 'ISBN-10',
        'résumé': 'famintinana',
        'couverture': 'fonony',
        'série': 'andiany',
        'tome': 'boky faha-',
        'type de document': 'karazan-tahirin-kevitra',
        'périmètre': 'faritra',
        'date': 'daty',
        'nombre': 'isa',
        'n° de carte': "laharan'ny karatra",
        'date de naissance': 'daty nahaterahana',
        'téléphone': 'finday',
        'adresse': 'adiresy',
        "date d'inscription": 'daty nisoratana',
        "date d'expiration": 'daty fahataperany',
        'statut': 'sata',
        'langue de correspondance': 'fiteny ifandraisana',
        'ancienne carte': 'karatra taloha',
        'photo': 'sary',
        'résultats de la recherche': "valin'ny fikarohana",
        '(toutes les pages)': '(pejy rehetra)',
        'Rechercher des notices': 'Karohy ny rakitra',
        'Rechercher des exemplaires': 'Karohy ny kopia',
        # ââ 2e vague ââ
        _PROV_EMPTY_HELP: "Mbola tsy misy fiaviana : mamorona iray avy ao amin'ny Mandroso → Fiaviana.",
        _LANG_CODE_HELP: "Fanafohezana iraisam-pirenena fototra, tsy misy karazany isam-paritra : fr, en, pt, de… (ny « fr » dia mahafaoka ny frantsay any Frantsa, Kanada ary Soisa).",
        _LANG_NAME_HELP: "Anaran'ny fiteny, amin'ny fiteny anoratanao.",
        "— non précisée —": "— tsy voafaritra —",
        "langue": "fiteny",
        "langues": "fiteny",
        "Langues": "Fiteny",
        "Nouvelle langue": "Fiteny vaovao",
        "Modifier la langue": "Hanova ny fiteny",
        "Retirer la langue": "Hanaisotra ny fiteny",
        "Langue ajoutée.": "Voampiditra ny fiteny.",
        "Langue mise à jour.": "Voaova ny fiteny.",
        "Langue retirée de la liste.": "Nesorina tao anaty lisitra ny fiteny.",
        "Retirer de la liste": "Esory amin'ny lisitra",
        _LANG_DEL_CONFIRM: "Hanaisotra ny <strong>%(name)s</strong> amin'ny lisitra tokoa ve ianao ?",
        _LANG_DEL_NO_RECORD: "Tsy misy rakitra fafana na ovana.",
        _LANG_DEL_EFFECT: "Tsy hatolotra intsony io fiteny io rehefa manasokajy boky na manoratra mpampiasa.",
        "Aucune langue définie.": "Tsy misy fiteny voafaritra.",
        _LANG_SUB: "Fitenin'ny boky sy fiteny tenenin'ny mpampiasa",
        _LANG_ONE_LIST: "Lisitra tokana, fampiasana roa",
        _LANG_ONE_LIST_1: "Io lisitra io no mamelona ny fitenin'ny boky sy ny fiteny tenenin'ny mpampiasa. Ampio fiteny izy raha ilain'ny boky na ny mpamaky iray.",
        _LANG_ONE_LIST_2: "Ampiasao ny fanafohezana iraisam-pirenena fototra, tsy misy karazany isam-paritra : ny « fr » dia mahafaoka ny frantsay any Frantsa, Kanada ary Soisa, ny « pt » kosa ny portogey sy ny breziliana.",
        _LANG_ONE_LIST_3: "Voalamina araka ny abidia amin'ny fitenin'ny efijery ny lisitra midina, ka miova arakaraka ny fiteny ny filaharana.",
        _ADV_LANGUAGES: "Fiteny atolotra ho an'ny boky sy ho an'ny fiteny tenenin'ny mpampiasa. Ampio ny lisitra raha ilain'ny fanangonana.",
        "Ne pas modifier": "Aza ovana",
        "— (vider)": "— (fafao)",
        "Affecter": "Ampiharo",
        _NOTHING_TO_CHANGE: "Tsy misy ovana : tsy nisy lisitra novaina.",
        "%(n)s notice(s) → catégorie %(v)s": "Rakitra %(n)s → sokajy %(v)s",
        "%(n)s notice(s) sans catégorie": "Rakitra %(n)s tsy misy sokajy",
        "%(n)s exemplaire(s) → emplacement %(v)s": "Kopia %(n)s → toerana %(v)s",
        "%(n)s exemplaire(s) sans emplacement": "Kopia %(n)s tsy misy toerana",
        "%(n)s exemplaire(s) → provenance %(v)s": "Kopia %(n)s → fiaviana %(v)s",
        "%(n)s exemplaire(s) sans provenance": "Kopia %(n)s tsy misy fiaviana",
        _XLS_EXT_COL: "safidy : kaodin'ny tranomboky hafa efa eo amin'ny boky",
        _XLS_PROV_COL: "safidy : kaody na anaran'ny fiaviana efa misy",
        _XLS_ABBR_COL: "safidy : fanafohezana (kaody) an'ny sokajy voatondro ao amin'ny CATEGORY",
        "Famille": "Fianakaviana",
        "Adulte ou enfant": "Olon-dehibe na ankizy",
        "Enfant": "Ankizy",
        "Adulte": "Olon-dehibe",
        "Année de naissance": "Taona nahaterahana",
        "année de naissance": "taona nahaterahana",
        "adulte": "olon-dehibe",
        _BIRTH_YEAR_HELP: "Ho an'ny ankizy : avy aminy no anisana ny taona.",
        "membre de la famille": "mpianakavy",
        "membres de la famille": "mpianakavy",
        "Ajouter une personne": "Hanampy olona",
        _FAMILY_DELETED: "rakitry ny fianakaviana hofafana miaraka amin'ny mpampiasa :",
        _NO_IMPACT_FAMILY: "Tsy misy fiantraikany : mpampiasa tsy manana fampindramana, famandrihana na olona miankina.",
        _FAMILY_HELP: "Ny olona mizara ity karatra ity. Tsy manana karatra manokana izy ireo : ireo fanazavana ireo dia hanolorana boky mifanaraka aminy ihany.",
        "Code Ofelia externe": "Kaody Ofelia ivelany",
        "code Ofelia externe": "kaody Ofelia ivelany",
        "Code externe": "Kaody ivelany",
        _EXT_CODE_HELP: "Kaody efa hita eo amin'ny boky, 20 marika farafahabetsany. Oh. BCF13298781X.",
        _EXT_CODE_INVALID: "Ny kaody ivelany dia tsy maintsy litera na isa ary tsy mihoatra ny %(n)s marika.",
        _EXT_CODE_TAKEN: "Efa an'ny kopia %(code)s (%(title)s) io kaody ivelany io.",
        _EXT_CODE_SINGLE: "Kopia iray ihany no azo omena kaody ivelany : amboary aloha ny kopia tsy misy kaody, avy eo soraty ny kaody amin'ny kopia voakasika.",
        _XLS_DUP: "Efa an'ny kopia hafa io kaody ivelany io : tsy raisina ny kaody, fa ampidirina ihany ny ambin'ny andalana.",
        _XLS_INVALID: "Tsy ekena ny kaody ivelany : tsy maintsy litera na isa ary tsy mihoatra ny 20 marika. Ampidirina ihany ny ambin'ny andalana.",
        "Provenance": "Fiaviana",
        "provenance": "fiaviana",
        "provenances": "fiaviana",
        "Provenances": "Fiaviana",
        "Nouvelle provenance": "Fiaviana vaovao",
        "Modifier la provenance": "Hanova ny fiaviana",
        "Supprimer la provenance": "Hamafa ny fiaviana",
        "Provenance créée.": "Voaforona ny fiaviana.",
        "Provenance mise à jour.": "Voaova ny fiaviana.",
        "Provenance supprimée.": "Voafafa ny fiaviana.",
        "Provenance par défaut": "Fiaviana mahazatra",
        "Provenance actuelle": "Fiaviana ankehitriny",
        "Toutes provenances": "Fiaviana rehetra",
        "Affecter une provenance": "Hanome fiaviana",
        "— (vider la provenance)": "— (fafao ny fiaviana)",
        "Nom complet": "Anarana feno",
        "Court, sans espace : OFELIA, BM-GE, DON-DUPONT…": "Fohy, tsy misy elanelana : OFELIA, BM-GE, DON-DUPONT…",
        _PROV_LABEL_HELP: "Anarana mora vakiana aseho anaty lisitra. Oh. « Nampindramin'ny Tranomboky Genève ».",
        _PROV_NOTES_HELP: "Fifandraisana, daty famerenana, fepetran'ny fametrahana…",
        _PROV_DEFAULT_HELP: "Ampiharina amin'ny kopia rehetra amin'ilay andiany. Oh. boky nampindramin'ny tranomboky hafa, ho hita indray amin'ny andro famerenana.",
        "Impossible : %(n)s exemplaire(s) portent encore cette provenance.": "Tsy vita : mbola misy kopia %(n)s manana io fiaviana io.",
        "%(n)s exemplaire(s) rattaché(s) à la provenance %(p)s.": "Kopia %(n)s nampiarahana amin'ny fiaviana %(p)s.",
        "%(n)s exemplaire(s) sans provenance (provenance vidée).": "Kopia %(n)s tsy misy fiaviana (nofafana ny fiaviana).",
        "%(n)s exemplaire(s) supprimé(s).": "Kopia %(n)s voafafa.",
        _PROV_BLOCKED: "Raha fafana ny fiaviana dia very ny fantatra momba ny niavian'ireo kopia ireo. Karakarao aloha izy ireo : ampiarahо amin'ny fiaviana hafa, na fafao raha averina ny fanangonana.",
        _PROV_FREE: "Tsy misy kopia mampiasa azy : tsy misy fiantraikany amin'ny katalaogy ny famafana azy.",
        _PROV_SUB: "Ny niavian'ny kopia : vidiana, natolotra, nampindramin'ny tranomboky hafa…",
        _PROV_EMPTY: "Mbola tsy misy fiaviana voafaritra. Tsindrio « Fiaviana vaovao » hanombohana.",
        _PROV_WHY_1: "Ny fiaviana dia manaraka ny kopia, fa tsy ny lohateny : boky iray ihany dia mety hanana kopia novidin'ny tranomboky sy kopia hafa nampindramin'ny tranomboky mpiara-miasa.",
        _PROV_WHY_2: "Amin'ny andro tsy maintsy hamerenana fanangonana, sokafy ny katalaogy, mariho « Karohy ny kopia », sivano araka ny fiaviana : hahazo ny lisitra marina ny boky halaina ianao.",
        "À quoi ça sert": "Inona no ilàna azy",
        "Voir ces exemplaires": "Hijery ireo kopia ireo",
        "Confirmez-vous la suppression de la provenance <strong>%(code)s</strong> ?": "Hamafa ny fiaviana <strong>%(code)s</strong> tokoa ve ianao ?",
        _ADV_PROVENANCES: "Ny niavian'ny kopia (vidiana, natolotra, nampindramin'ny tranomboky hafa). Ahafahana mahita sy mamerina fanangonana manontolo.",
        "Chercher les exemplaires": "Karohy ny kopia",
        "exemplaire(s) sélectionné(s)": "kopia voafidy",
        "Supprimer les exemplaires sélectionnés": "Hamafa ny kopia voafidy",
        "Supprimer des exemplaires": "Hamafa kopia",
        "Exemplaires concernés": "Kopia voakasika",
        _DEL_FINAL: "Tsy azo averina io famafana io. Ny rakitra kosa dia mijanona ao amin'ny katalaogy.",
        _DEL_HISTORY: "Voafafa ny tantaran'ny fampindramana sy ny famakiana an-toerana amin'ireo kopia ireo.",
        _DEL_TOMBSTONE: "Atokana tanteraka ny kaody Ofelia-n'izy ireo : tsy homena boky hafa mihitsy, na dia efa vita pirinty aza ny etikety.",
        "Catégories": "Sokajy",
        "Abréviation": "Fanafohezana",
        "abréviation": "fanafohezana",
        "Catégorie parente": "Sokajy ambony",
        "Durée de prêt (jours)": "Faharetan'ny fampindramana (andro)",
        "Court, sans espace : ENF-ALB, ADU-ROM…": "Fohy, tsy misy elanelana : ENF-ALB, ADU-ROM…",
        _ABBR_HELP: "Kaody atao pirinty amin'ny etiketin'ny lamosin-boky. Oh. « RO FI ADO » ho an'ny « Tantara foronina ho an'ny tanora ».",
        "Sous-catégorie de… (optionnel).": "Zana-tsokajin'ny… (safidy).",
        "Vide = durée par défaut de la bibliothèque.": "Foana = faharetana mahazatra amin'ny tranomboky.",
        "Catégorie créée.": "Voaforona ny sokajy.",
        "Catégorie mise à jour.": "Voaova ny sokajy.",
        "Catégorie supprimée.": "Voafafa ny sokajy.",
        "Modifier la catégorie": "Hanova ny sokajy",
        "Supprimer la catégorie": "Hamafa ny sokajy",
        "Nouvelle": "Vaovao",
        "Aucune catégorie définie.": "Tsy misy sokajy voafaritra.",
        "L'abréviation": "Ny fanafohezana",
        _ABBR_WHAT: "Izy no kaody mankany amin'ny etiketin'ny lamosin-boky, mba hametrahana ny boky eo amin'ny toerana mety nefa tsy mila manaisotra azy amin'ny talantalana. Ohatra : « RO FI ADO » ho an'ny « Tantara foronina ho an'ny tanora ».",
        _ABBR_SCOPE: "Mihatra amin'ny rakitra rehetra ao amin'ilay sokajy izy. Ny etikety dia atao pirinty avy ao amin'ny Fanontana → Etikety.",
        _ABBR_GONE: "Manjavona ny fanafohezana « %(abbr)s » : mijanona ny etiketin-damosina efa napetaka, fa tsy ho azo atao pirinty indray.",
        "Confirmez-vous la suppression de la catégorie <strong>%(code)s</strong> ?": "Hamafa ny sokajy <strong>%(code)s</strong> tokoa ve ianao ?",
        _CAT_SUB: "Fanasokajiana ny rakitra sy ny kaody atao pirinty amin'ny lamosin-boky",
        "Cote imprimée sur la tranche": "Kaody atao pirinty amin'ny lamosina",
        _ADV_CATEGORIES: "Fanasokajiana ny rakitra sy ny fanafohezana atao pirinty amin'ny lamosin-boky (« RO FI ADO »).",
        "Étiquettes de tranche": "Etiketin'ny lamosina",
        _NO_ABBR: "Tsy misy amin'ireo kopia voafidy manana sokajy nafohezina : fenoy aloha ny fanafohezan'ny sokajy alohan'ny hanontana.",
        "Langues parlées": "Fiteny tenenina",
        "langues parlées": "fiteny tenenina",
        "Autres langues": "Fiteny hafa",
        "autres langues": "fiteny hafa",
        _LANG_OTHER_HELP: "Fiteny tsy ao anaty lisitra, sarahina amin'ny faingo.",
        "Français": "Frantsay",
        "Anglais": "Anglisy",
        "Portugais": "Portogey",
        "Espagnol": "Espaniola",
        "Italien": "Italiana",
        "Allemand": "Alemana",
        "Arabe": "Arabo",
        "Albanais": "Albaney",
        "Turc": "Tiorka",
        "Russe": "Rosiana",
        "Serbo-croate": "Serbo-kroaty",
        "Tamoul": "Tamoly",
        "Chinois": "Sinoa",
        "Polonais": "Poloney",
        "Persan": "Persana",
        "Farsi": "Farsy",
        "Grec": "Grika",
        "Somali": "Somaly",
        "Roumain": "Romaniana",
        "Ukrainien": "Okrainiana",
        "Japonais": "Japoney",
        "Malgache": "Malagasy",
        "Enfants": "Zanaka",
        "enfant": "zanaka",
        "enfants": "zanaka",
        "Ajouter un enfant": "Hanampy zanaka",
        "Sexe": "Lahy na vavy",
        "sexe": "lahy na vavy",
        "Âge": "Taona",
        "âge": "taona",
        "prénom": "anarana",
        "Fille": "Zazavavy",
        "Garçon": "Zazalahy",
        "%(n)s ans": "%(n)s taona",
        _CHILDREN_HELP: "Ny ankizy miaraka amin'ity mpampiasa ity. Tsy manana karatra izy ireo : ireo fanazavana ireo dia hanolorana boky mifanaraka aminy.",
        "fiche(s) enfant seront supprimées avec l'usager :": "rakitra zanaka hofafana miaraka amin'ny mpampiasa :",
        _NO_IMPACT: "Tsy misy fiantraikany : mpampiasa tsy manana fampindramana, famandrihana na zanaka voasoratra.",
    },
}


# ── Formes plurielles ─────────────────────────────────────────────────────
# Clé = msgid singulier ; valeur = (traduction singulier, traduction pluriel).
# Les 4 locales déclarent `nplurals=2`.
PLURALS = {
    "en": {
        'Sélectionner le résultat visible': (
            'Select the visible result',
            'Select the %(counter)s visible results',
        ),
        'Sélectionner le résultat de la recherche': (
            'Select the search result',
            'Select all %(counter)s search results',
        ),
        '… et %(counter)s autre exemplaire non affiché ici. Il sera supprimé lui aussi.': (
            '… and %(counter)s other copy not shown here. It will be deleted too.',
            '… and %(counter)s other copies not shown here. They will be deleted too.',
        ),
        '… et %(counter)s autre notice non affichée ici. Elle sera supprimée elle aussi.': (
            '… and %(counter)s other record not shown here. It will be deleted too.',
            '… and %(counter)s other records not shown here. They will be deleted too.',
        ),
        "notice se retrouvera sans catégorie (aucune notice n'est supprimée).": (
            "record will end up with no category (no record is deleted).",
            "records will end up with no category (no record is deleted).",
        ),
        "sous-catégorie perdra son parent (deviendra racine).": (
            "sub-category will lose its parent (it becomes a top-level one).",
            "sub-categories will lose their parent (they become top-level ones).",
        ),
        "%(n)s ligne non importée": (
            "%(n)s row not imported",
            "%(n)s rows not imported",
        ),
        "%(counter)s exemplaire sélectionné": (
            "%(counter)s copy selected",
            "%(counter)s copies selected",
        ),
        "exemplaire est actuellement prêté : son prêt sera clos en « perdu ».": (
            "copy is currently on loan: its loan will be closed as “lost”.",
            "copies are currently on loan: their loans will be closed as “lost”.",
        ),
        "exemplaire est mis de côté : la réservation servie sera annulée.": (
            "copy is set aside: the reservation it serves will be cancelled.",
            "copies are set aside: the reservations they serve will be cancelled.",
        ),
        "exemplaire rattaché perdra son emplacement (affiché « — » dans la fiche).": (
            "attached copy will lose its shelf location (shown as “—” on the record).",
            "attached copies will lose their shelf location (shown as “—” on the record).",
        ),
        "sous-emplacement perdra son parent (deviendra racine).": (
            "sub-location will lose its parent (it becomes a top-level one).",
            "sub-locations will lose their parent (they become top-level ones).",
        ),
        "Suppression impossible : %(counter)s exemplaire porte encore cette provenance.": (
            "Deletion not possible: %(counter)s copy still has this source.",
            "Deletion not possible: %(counter)s copies still have this source.",
        ),
        "%(counter)s notice sélectionnée": (
            "%(counter)s record selected",
            "%(counter)s records selected",
        ),
        "%(n)s exemplaire concerné": (
            "%(n)s copy affected",
            "%(n)s copies affected",
        ),
        "%(counter)s exemplaire": ("%(counter)s copy", "%(counter)s copies"),
        "%(n)s jour": ("%(n)s day", "%(n)s days"),
        "exemplaire a été déplacé automatiquement vers <strong>%(code)s</strong> pendant cette session (sa location précédente a été corrigée).": (
            "copy was moved automatically to <strong>%(code)s</strong> during this session (its previous location was corrected).",
            "copies were moved automatically to <strong>%(code)s</strong> during this session (their previous location was corrected).",
        ),
        "%(n)s jour de retard": ("%(n)s day overdue", "%(n)s days overdue"),
        _LANG_KEEPS_CODE: (
            "record keeps the code “%(code)s”, which will show as-is instead of the translated name.",
            "records keep the code “%(code)s”, which will show as-is instead of the translated name.",
        ),
    },
    "es": {
        'Sélectionner le résultat visible': (
            'Seleccionar el resultado visible',
            'Seleccionar los %(counter)s resultados visibles',
        ),
        'Sélectionner le résultat de la recherche': (
            'Seleccionar el resultado de la búsqueda',
            'Seleccionar los %(counter)s resultados de la búsqueda',
        ),
        '… et %(counter)s autre exemplaire non affiché ici. Il sera supprimé lui aussi.': (
            '… y %(counter)s ejemplar más que no se muestra aquí. También se eliminará.',
            '… y %(counter)s ejemplares más que no se muestran aquí. También se eliminarán.',
        ),
        '… et %(counter)s autre notice non affichée ici. Elle sera supprimée elle aussi.': (
            '… y %(counter)s registro más que no se muestra aquí. También se eliminará.',
            '… y %(counter)s registros más que no se muestran aquí. También se eliminarán.',
        ),
        "notice se retrouvera sans catégorie (aucune notice n'est supprimée).": (
            "registro se quedará sin categoría (no se elimina ningún registro).",
            "registros se quedarán sin categoría (no se elimina ningún registro).",
        ),
        "sous-catégorie perdra son parent (deviendra racine).": (
            "subcategoría perderá su categoría superior (pasará a ser principal).",
            "subcategorías perderán su categoría superior (pasarán a ser principales).",
        ),
        "%(n)s ligne non importée": (
            "%(n)s fila no importada",
            "%(n)s filas no importadas",
        ),
        "%(counter)s exemplaire sélectionné": (
            "%(counter)s ejemplar seleccionado",
            "%(counter)s ejemplares seleccionados",
        ),
        "exemplaire est actuellement prêté : son prêt sera clos en « perdu ».": (
            "ejemplar está prestado ahora mismo: su préstamo se cerrará como “perdido”.",
            "ejemplares están prestados ahora mismo: sus préstamos se cerrarán como “perdidos”.",
        ),
        "exemplaire est mis de côté : la réservation servie sera annulée.": (
            "ejemplar está apartado: se cancelará la reserva que atiende.",
            "ejemplares están apartados: se cancelarán las reservas que atienden.",
        ),
        "exemplaire rattaché perdra son emplacement (affiché « — » dans la fiche).": (
            "ejemplar asociado perderá su ubicación (aparecerá “—” en la ficha).",
            "ejemplares asociados perderán su ubicación (aparecerá “—” en la ficha).",
        ),
        "sous-emplacement perdra son parent (deviendra racine).": (
            "sububicación perderá su ubicación superior (pasará a ser principal).",
            "sububicaciones perderán su ubicación superior (pasarán a ser principales).",
        ),
        "Suppression impossible : %(counter)s exemplaire porte encore cette provenance.": (
            "Eliminación imposible: %(counter)s ejemplar todavía tiene esta procedencia.",
            "Eliminación imposible: %(counter)s ejemplares todavía tienen esta procedencia.",
        ),
        "%(counter)s notice sélectionnée": (
            "%(counter)s registro seleccionado",
            "%(counter)s registros seleccionados",
        ),
        "%(n)s exemplaire concerné": (
            "%(n)s ejemplar afectado",
            "%(n)s ejemplares afectados",
        ),
        "%(counter)s exemplaire": ("%(counter)s ejemplar", "%(counter)s ejemplares"),
        "%(n)s jour": ("%(n)s día", "%(n)s días"),
        "exemplaire a été déplacé automatiquement vers <strong>%(code)s</strong> pendant cette session (sa location précédente a été corrigée).": (
            "ejemplar se movió automáticamente a <strong>%(code)s</strong> durante esta sesión (se corrigió su ubicación anterior).",
            "ejemplares se movieron automáticamente a <strong>%(code)s</strong> durante esta sesión (se corrigió su ubicación anterior).",
        ),
        "%(n)s jour de retard": ("%(n)s día de retraso", "%(n)s días de retraso"),
        _LANG_KEEPS_CODE: (
            "registro conserva el código “%(code)s”, que se mostrará tal cual en lugar del nombre traducido.",
            "registros conservan el código “%(code)s”, que se mostrará tal cual en lugar del nombre traducido.",
        ),
    },
    "mg": {
        'Sélectionner le résultat visible': (
            'Fidio ny valiny hita',
            'Fidio ny valiny %(counter)s hita',
        ),
        'Sélectionner le résultat de la recherche': (
            "Fidio ny valin'ny fikarohana",
            "Fidio ny valin'ny fikarohana %(counter)s",
        ),
        '… et %(counter)s autre exemplaire non affiché ici. Il sera supprimé lui aussi.': (
            '… ary kopia %(counter)s hafa tsy aseho eto. Hofafana koa izy.',
            '… ary kopia %(counter)s hafa tsy aseho eto. Hofafana koa izy ireo.',
        ),
        '… et %(counter)s autre notice non affichée ici. Elle sera supprimée elle aussi.': (
            '… ary rakitra %(counter)s hafa tsy aseho eto. Hofafana koa izy.',
            '… ary rakitra %(counter)s hafa tsy aseho eto. Hofafana koa izy ireo.',
        ),
        "notice se retrouvera sans catégorie (aucune notice n'est supprimée).": (
            "rakitra no ho tsy misy sokajy (tsy misy rakitra fafana).",
            "rakitra no ho tsy misy sokajy (tsy misy rakitra fafana).",
        ),
        "sous-catégorie perdra son parent (deviendra racine).": (
            "zana-tsokajy no ho very ny sokajy ambony (ho lasa fototra).",
            "zana-tsokajy no ho very ny sokajy ambony (ho lasa fototra).",
        ),
        "%(n)s ligne non importée": (
            "Andalana %(n)s tsy voampiditra",
            "Andalana %(n)s tsy voampiditra",
        ),
        "%(counter)s exemplaire sélectionné": (
            "Kopia %(counter)s voafidy",
            "Kopia %(counter)s voafidy",
        ),
        "exemplaire est actuellement prêté : son prêt sera clos en « perdu ».": (
            "kopia no ampindramina amin'izao : hofaranana ho « very » ny fampindramana azy.",
            "kopia no ampindramina amin'izao : hofaranana ho « very » ny fampindramana azy ireo.",
        ),
        "exemplaire est mis de côté : la réservation servie sera annulée.": (
            "kopia no natokana : hofoanana ny famandrihana tompoiny.",
            "kopia no natokana : hofoanana ny famandrihana tompoin'izy ireo.",
        ),
        "exemplaire rattaché perdra son emplacement (affiché « — » dans la fiche).": (
            "kopia mifandray no ho very ny toerany (aseho « — » ao amin'ny rakitra).",
            "kopia mifandray no ho very ny toerany (aseho « — » ao amin'ny rakitra).",
        ),
        "sous-emplacement perdra son parent (deviendra racine).": (
            "zana-toerana no ho very ny toerana ambony (ho lasa fototra).",
            "zana-toerana no ho very ny toerana ambony (ho lasa fototra).",
        ),
        "Suppression impossible : %(counter)s exemplaire porte encore cette provenance.": (
            "Tsy azo fafana : mbola misy kopia %(counter)s manana io fiaviana io.",
            "Tsy azo fafana : mbola misy kopia %(counter)s manana io fiaviana io.",
        ),
        "%(counter)s notice sélectionnée": (
            "Rakitra %(counter)s voafidy",
            "Rakitra %(counter)s voafidy",
        ),
        "%(n)s exemplaire concerné": ("Kopia %(n)s voakasika", "Kopia %(n)s voakasika"),
        "%(counter)s exemplaire": ("Kopia %(counter)s", "Kopia %(counter)s"),
        "%(n)s jour": ("Andro %(n)s", "Andro %(n)s"),
        "exemplaire a été déplacé automatiquement vers <strong>%(code)s</strong> pendant cette session (sa location précédente a été corrigée).": (
            "kopia no nafindra ho any amin'ny <strong>%(code)s</strong> nandritra ity fotoana ity (voahitsy ny toerany teo aloha).",
            "kopia no nafindra ho any amin'ny <strong>%(code)s</strong> nandritra ity fotoana ity (voahitsy ny toerany teo aloha).",
        ),
        "%(n)s jour de retard": ("Andro %(n)s tara", "Andro %(n)s tara"),
        _LANG_KEEPS_CODE: (
            "rakitra no mitazona ny kaody « %(code)s », ka io no haseho fa tsy ny anarana nadika.",
            "rakitra no mitazona ny kaody « %(code)s », ka io no haseho fa tsy ny anarana nadika.",
        ),
    },
}


# ── Applicateur .po ───────────────────────────────────────────────────────


def _unescape(value: str) -> str:
    return (
        value.replace('\\"', '"')
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\\\", "\\")
    )


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def _read_value(lines: list[str], start: int, keyword: str) -> tuple[str, int]:
    """Lit `keyword "..."` + ses lignes de continuation. Renvoie (valeur, index suivant)."""
    first = lines[start][len(keyword):].strip()
    parts = [_unescape(first.strip('"'))]
    i = start + 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(_unescape(lines[i].strip().strip('"')))
        i += 1
    return "".join(parts), i


def _clean_comments(block: list[str]) -> list[str]:
    """Retire le drapeau `fuzzy` et les anciens msgid `#|` d'un bloc traduit."""
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
    """Applique les traductions à un `.po`. Renvoie (singuliers, pluriels)."""
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0, 0
    singles = TRANSLATIONS.get(lang, {})
    plurals = PLURALS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []  # commentaires en attente du msgid courant
    n_single = n_plural = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            pending.append(line)
            i += 1
            continue
        if not line.startswith("msgid "):
            out.extend(pending)
            pending = []
            out.append(line)
            i += 1
            continue

        msgid, j = _read_value(lines, i, "msgid ")
        header = lines[i:j]

        # Bloc pluriel
        if j < len(lines) and lines[j].startswith("msgid_plural "):
            _plural_id, k = _read_value(lines, j, "msgid_plural ")
            header += lines[j:k]
            forms = []
            while k < len(lines) and re.match(r"^msgstr\[\d\] ", lines[k]):
                _v, k = _read_value(lines, k, lines[k][: lines[k].index(" ") + 1])
                forms.append(_v)
            if msgid in plurals:
                sing, plur = plurals[msgid]
                out.extend(_clean_comments(pending))
                out.extend(header)
                out.append(f'msgstr[0] "{_escape(sing)}"')
                out.append(f'msgstr[1] "{_escape(plur)}"')
                n_plural += 1
            else:
                out.extend(pending)
                out.extend(lines[i:k])
            pending = []
            i = k
            continue

        # Bloc simple
        if j < len(lines) and lines[j].startswith("msgstr "):
            _v, k = _read_value(lines, j, "msgstr ")
            if msgid in singles and singles[msgid]:
                out.extend(_clean_comments(pending))
                out.extend(header)
                out.append(f'msgstr "{_escape(singles[msgid])}"')
                n_single += 1
            else:
                out.extend(pending)
                out.extend(lines[i:k])
            pending = []
            i = k
            continue

        out.extend(pending)
        pending = []
        out.extend(header)
        i = j

    out.extend(pending)
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return n_single, n_plural


def main() -> None:
    for lang in ("en", "es", "mg"):
        singles, plurals = apply_lang(lang)
        print(f"[{lang}] {singles} chaîne(s) + {plurals} forme(s) plurielle(s)")


if __name__ == "__main__":
    main()
