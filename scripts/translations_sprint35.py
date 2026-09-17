#!/usr/bin/env python3
"""Traductions Sprint 35 — FR → EN/ES/MG.

FEAT-094 : vocabulaire « classification » / « code de classification »
à la place de « catégorie » / « abréviation » pour catalog.Category.

Les catégories d'usagers ne passent pas par ce script.

À rejouer APRÈS `makemessages` :
    python scripts/translations_sprint35.py
"""
from __future__ import annotations

import re
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

# fr: (en, es, mg)
TABLE: dict[str, tuple[str, str, str]] = {
    "classification": ("classification", "clasificación", "fanasokajiana"),
    "classifications": ("classifications", "clasificaciones", "fanasokajiana"),
    "Classification": ("Classification", "Clasificación", "Fanasokajiana"),
    "Classifications": ("Classifications", "Clasificaciones", "Fanasokajiana"),
    "code de classification": (
        "classification code", "código de clasificación", "kaody fanasokajiana"),
    "Code de classification": (
        "Classification code", "Código de clasificación", "Kaody fanasokajiana"),
    "Le code de classification": (
        "The classification code", "El código de clasificación",
        "Ny kaody fanasokajiana"),
    "classification parente": (
        "parent classification", "clasificación superior", "fanasokajiana ambony"),
    "Classification parente": (
        "Parent classification", "Clasificación superior", "Fanasokajiana ambony"),
    "Sous-classification de… (optionnel).": (
        "Sub-classification of… (optional).",
        "Subclasificación de… (opcional).",
        "Zana-panasokajian'ny… (safidy)."),
    "Nouvelle classification": (
        "New classification", "Nueva clasificación", "Fanasokajiana vaovao"),
    "Modifier la classification": (
        "Edit classification", "Editar la clasificación", "Hanova ny fanasokajiana"),
    "Supprimer la classification": (
        "Delete classification", "Eliminar la clasificación", "Hamafa ny fanasokajiana"),
    "Classification créée.": (
        "Classification created.", "Clasificación creada.",
        "Voaforona ny fanasokajiana."),
    "Classification mise à jour.": (
        "Classification updated.", "Clasificación actualizada.",
        "Nohavaozina ny fanasokajiana."),
    "Classification supprimée.": (
        "Classification deleted.", "Clasificación eliminada.",
        "Nofafana ny fanasokajiana."),
    "Aucune classification définie.": (
        "No classification defined yet.",
        "No hay ninguna clasificación definida.",
        "Tsy misy fanasokajiana voafaritra."),
    "Toutes les classifications": (
        "All classifications", "Todas las clasificaciones",
        "Ny fanasokajiana rehetra"),
    "Sans classification": (
        "No classification", "Sin clasificación", "Tsy misy fanasokajiana"),
    "Statistiques par classification": (
        "Statistics by classification", "Estadísticas por clasificación",
        "Antontan'isa araka ny fanasokajiana"),
    "Classification par défaut": (
        "Default classification", "Clasificación por defecto",
        "Fanasokajiana mahazatra"),
    "Une classification": (
        "A classification", "Una clasificación", "Fanasokajiana iray"),
    "%(n)s notice(s) → classification %(v)s": (
        "%(n)s record(s) → classification %(v)s",
        "%(n)s ficha(s) → clasificación %(v)s",
        "Rakitra %(n)s → fanasokajiana %(v)s"),
    "%(n)s notice(s) sans classification": (
        "%(n)s record(s) with no classification",
        "%(n)s ficha(s) sin clasificación",
        "Rakitra %(n)s tsy misy fanasokajiana"),
    "optionnel : nom d'une classification existante (alias CATEGORY)": (
        "optional: name of an existing classification (alias CATEGORY)",
        "opcional: nombre de una clasificación existente (alias CATEGORY)",
        "safidy: anaran'ny fanasokajiana efa misy (alias CATEGORY)"),
    "optionnel : code de classification de la ligne CLASSIFICATION (alias CATEGORY_ABBR)": (
        "optional: classification code of the CLASSIFICATION row (alias CATEGORY_ABBR)",
        "opcional: código de clasificación de la fila CLASSIFICATION (alias CATEGORY_ABBR)",
        "safidy: kaody fanasokajiana an'ny andalana CLASSIFICATION (alias CATEGORY_ABBR)"),
    "Confirmez-vous la suppression de la classification <strong>%(code)s</strong> ?": (
        "Do you confirm the deletion of classification <strong>%(code)s</strong>?",
        "¿Confirma la eliminación de la clasificación <strong>%(code)s</strong>?",
        "Hamafa ny fanasokajiana <strong>%(code)s</strong> tokoa ve ianao ?"),
    "Le code de classification « %(abbr)s » disparaît : les étiquettes de tranche déjà collées restent, mais ne pourront plus être réimprimées.": (
        "The classification code “%(abbr)s” disappears: spine labels already stuck on books stay, but they can no longer be reprinted.",
        "El código de clasificación « %(abbr)s » desaparece: las etiquetas de lomo ya pegadas se quedan, pero ya no se podrán reimprimir.",
        "Laso ny kaody fanasokajiana « %(abbr)s » : mijanona ny etikety sisiny efa napetaka, fa tsy azo atonta indray intsony."),
    "C'est ce qui part sur l'étiquette de tranche, pour ranger le livre au bon rayon sans le sortir de l'étagère. Exemple : « JE DOC » pour « Jeunesse Documentaire ».": (
        "This is what goes on the spine label, so you can file the book on the right shelf without pulling it out. Example: “JE DOC” for “Youth Non-fiction”.",
        "Esto es lo que va en la etiqueta de lomo, para colocar el libro en el estante correcto sin sacarlo. Ejemplo: « JE DOC » para « Juventud Documental ».",
        "Izany no alefa eo amin'ny etikety sisiny, hametrahana ny boky amin'ny talantalana marina nefa tsy esorina. Ohatra : « JE DOC » ho an'ny « Tanora Dokumentera »."),
    "Il vaut pour toutes les notices de la classification. Les étiquettes s'impriment depuis Impressions → Étiquettes.": (
        "It applies to every record in the classification. Labels are printed from Printing → Labels.",
        "Vale para todas las fichas de la clasificación. Las etiquetas se imprimen desde Impresión → Etiquetas.",
        "Manan-kery ho an'ny rakitra rehetra amin'io fanasokajiana io. Atonta avy amin'ny Fanontana → Etikety ny etikety."),
    "Imprime le code de classification (« JE DOC ») à coller sur la tranche, pour ranger et retrouver un livre sans le sortir du rayon.": (
        "Prints the classification code (“JE DOC”) to stick on the spine, so you can file and find a book without taking it off the shelf.",
        "Imprime el código de clasificación (« JE DOC ») para pegarlo en el lomo, y colocar o encontrar un libro sin sacarlo del estante.",
        "Manonta ny kaody fanasokajiana (« JE DOC ») hapetaka amin'ny sisiny, hametrahana sy hahitana boky nefa tsy esorina amin'ny talantalana."),
    "Vérifier ou importer un fichier Excel d'inventaire (ISBN, titre, auteur, emplacement, classification).": (
        "Check or import an Excel inventory file (ISBN, title, author, location, classification).",
        "Comprobar o importar un archivo Excel de inventario (ISBN, título, autor, ubicación, clasificación).",
        "Hamarino na ampidiro rakitra Excel fanisana (ISBN, lohateny, mpanoratra, toerana, fanasokajiana)."),
    "Classement des notices et code de classification imprimé sur la tranche des livres (« JE DOC »).": (
        "Filing of records and classification code printed on book spines (“JE DOC”).",
        "Clasificación de las fichas y código de clasificación impreso en el lomo de los libros (« JE DOC »).",
        "Fanasokajiana ny rakitra sy kaody fanasokajiana atonta amin'ny sisin'ny boky (« JE DOC »)."),
    "Gestion fine : classifications, tags, emplacements, catégories d'usagers (réservé au support technique).": (
        "Fine-grained management: classifications, tags, locations, member categories (technical support only).",
        "Gestión fina: clasificaciones, etiquetas, ubicaciones, categorías de usuario (reservado al soporte técnico).",
        "Fitantanana antsipiriany: fanasokajiana, marika, toerana, sokajin'ny mpampiasa (natokana ho an'ny fanohanana teknika)."),
    "Les classifications, tags et emplacements se gèrent depuis l'administration Django pour l'instant.": (
        "Classifications, tags and locations are still managed from the Django admin for now.",
        "Las clasificaciones, etiquetas y ubicaciones se gestionan por ahora desde la administración Django.",
        "Ny fanasokajiana, marika ary toerana dia mbola tantanina avy amin'ny fitantanana Django amin'izao."),
    "Aucun exemplaire sélectionné n'a de code de classification : renseignez le code de classification avant d'imprimer.": (
        "None of the selected copies has a classification code: fill in the classification code before printing.",
        "Ningún ejemplar seleccionado tiene código de clasificación: indique el código de clasificación antes de imprimir.",
        "Tsy misy kopia voafidy manana kaody fanasokajiana : fenoy ny kaody fanasokajiana alohan'ny hanontana."),
    "Identifiant unique. Pour les classifications Ofelia, identique au code de classification (JE DOC).": (
        "Unique identifier. For Ofelia classifications, the same as the classification code (JE DOC).",
        "Identificador único. En las clasificaciones Ofelia, idéntico al código de clasificación (JE DOC).",
        "Famantarana tokana. Ho an'ny fanasokajiana Ofelia, mitovy amin'ny kaody fanasokajiana (JE DOC)."),
    "Imprimé sur l'étiquette de tranche. Ex. « JE DOC » pour « Jeunesse Documentaire ».": (
        "Printed on the spine label. E.g. “JE DOC” for “Youth Non-fiction”.",
        "Impreso en la etiqueta de lomo. Ej. « JE DOC » para « Juventud Documental ».",
        "Atonta amin'ny etikety sisiny. Ohatra « JE DOC » ho an'ny « Tanora Dokumentera »."),
    "Utilisée si ni la classification du document ni la catégorie de membre n'en définit une. Défaut : 21 jours (3 semaines).": (
        "Used if neither the document classification nor the member category defines one. Default: 21 days (3 weeks).",
        "Se usa si ni la clasificación del documento ni la categoría de miembro definen una. Por defecto: 21 días (3 semanas).",
        "Ampiasaina raha tsy ny fanasokajian'ny boky na ny sokajin'ny mpampiasa no mamaritra iray. Mahazatra : 21 andro (3 herinandro)."),
    "Toutes les autres colonnes de l'import sont acceptées et facultatives : TITLE, AUTHOR, CLASSIFICATION, CLASSIFICATION_CODE, TYPE, EDITOR, YEAR, LANGUAGE, TAGS, CONDITION, PROVENANCE, LOCATION et ISBN. Une cellule remplie remplace la valeur existante ; <strong>une cellule vide laisse la valeur en place</strong> (le fichier ne sert donc pas à effacer un champ). Les anciens noms CATEGORY et CATEGORY_ABBR restent lus.": (
        "Every other import column is accepted and optional: TITLE, AUTHOR, CLASSIFICATION, CLASSIFICATION_CODE, TYPE, EDITOR, YEAR, LANGUAGE, TAGS, CONDITION, PROVENANCE, LOCATION and ISBN. A filled cell replaces the existing value; <strong>an empty cell leaves the value in place</strong> (so the file is not used to clear a field). The old names CATEGORY and CATEGORY_ABBR are still read.",
        "El resto de columnas de la importación se aceptan y son opcionales: TITLE, AUTHOR, CLASSIFICATION, CLASSIFICATION_CODE, TYPE, EDITOR, YEAR, LANGUAGE, TAGS, CONDITION, PROVENANCE, LOCATION e ISBN. Una celda rellena sustituye el valor existente; <strong>una celda vacía deja el valor en su sitio</strong> (el archivo no sirve para borrar un campo). Los nombres antiguos CATEGORY y CATEGORY_ABBR se siguen leyendo.",
        "Ny tsanganana hafa rehetra amin'ny fampidirana dia ekena ary tsy voatery: TITLE, AUTHOR, CLASSIFICATION, CLASSIFICATION_CODE, TYPE, EDITOR, YEAR, LANGUAGE, TAGS, CONDITION, PROVENANCE, LOCATION ary ISBN. Sela feno dia manolo ny sanda efa misy; <strong>sela foana dia avela ny sanda</strong> (tsy natao hamafana saha ny rakitra). Mbola vakiana ny anarana taloha CATEGORY sy CATEGORY_ABBR."),
}

TRANSLATIONS = {
    "en": {fr: values[0] for fr, values in TABLE.items()},
    "es": {fr: values[1] for fr, values in TABLE.items()},
    "mg": {fr: values[2] for fr, values in TABLE.items()},
}

PLURALS: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        "notice se retrouvera sans classification (aucune notice n'est supprimée).": (
            "record will end up with no classification (no record is deleted).",
            "records will end up with no classification (no record is deleted).",
        ),
        "sous-classification perdra son parent (deviendra racine).": (
            "sub-classification will lose its parent (it becomes a top-level one).",
            "sub-classifications will lose their parent (they become top-level ones).",
        ),
    },
    "es": {
        "notice se retrouvera sans classification (aucune notice n'est supprimée).": (
            "ficha quedará sin clasificación (ninguna ficha se elimina).",
            "fichas quedarán sin clasificación (ninguna ficha se elimina).",
        ),
        "sous-classification perdra son parent (deviendra racine).": (
            "subclasificación perderá su padre (pasará a ser de primer nivel).",
            "subclasificaciones perderán su padre (pasarán a ser de primer nivel).",
        ),
    },
    "mg": {
        "notice se retrouvera sans classification (aucune notice n'est supprimée).": (
            "rakitra no tsy hanana fanasokajiana (tsy misy rakitra voafafa).",
            "rakitra no tsy hanana fanasokajiana (tsy misy rakitra voafafa).",
        ),
        "sous-classification perdra son parent (deviendra racine).": (
            "zana-panasokajiana no very ray (lasa fototra).",
            "zana-panasokajiana no very ray (lasa fototra).",
        ),
    },
}


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
    plurals = PLURALS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []
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

        if j < len(lines) and lines[j].startswith("msgid_plural "):
            _plural_id, k = _read_value(lines, j, "msgid_plural ")
            header = header + lines[j:k]
            while k < len(lines) and re.match(r"^msgstr\[\d\] ", lines[k]):
                _v, k = _read_value(lines, k, lines[k][: lines[k].index(" ") + 1])
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
    payload = ("\n".join(out) + "\n").encode("utf-8")
    with open(po_path, "wb") as handle:
        handle.write(payload)
    return n_single, n_plural


def main() -> None:
    for lang in ("en", "es", "mg"):
        single, plural = apply_lang(lang)
        print(f"[{lang}] {single} chaîne(s) + {plural} pluriel(s)")


if __name__ == "__main__":
    main()
