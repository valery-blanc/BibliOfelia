#!/usr/bin/env python3
"""Traductions Sprint 30 — FR → EN/ES/MG.

Couvre FEAT-078 (export Excel de tout le catalogue), FEAT-079 (mise à jour
d'exemplaires existants depuis un fichier Excel), FEAT-080 (identification
complète du livre et de l'usager aux écrans de prêt et de retour) et FEAT-081
(une ancienne carte d'usager reconnue partout, et signalée comme telle).

Vocabulaire repris de l'existant, pour que les deux nouvelles fenêtres parlent
comme le reste de l'écran « Catalogage Excel » :

- *exemplaire* → **copy** / **ejemplar** / **kopia**
- *code Ofelia* → **Ofelia code** / **código Ofelia** / **kaody Ofelia**
- *code externe* → **external code** / **código externo** / **kaody ivelany**
- *emplacement* → **location** / **ubicación** / **toerana**
- *retour* → **return** / **devolución** / **famerenana** (FEAT-080)

« Externe » existait déjà comme en-tête de colonne, traduit *External code* /
*Código externo* / *Kaody ivelany* : la pastille de code réutilise le même
msgid plutôt que d'en créer un synonyme.

Les noms de colonnes (OFELIA_CODE, TITLE, CONDITION…) ne sont **pas** traduits :
ce sont des en-têtes de fichier, les mêmes dans les quatre langues.

Le mécanisme (`apply_lang`, gestion des blocs `msgid_plural`) est repris de
`scripts/translations_sprint28.py`.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint30.py
"""
from __future__ import annotations

import re
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

# ── Chaînes longues, factorisées pour garder les dictionnaires lisibles ────

_NO_KEY_COLUMN = (
    "Colonne d'identification manquante : le fichier doit porter une colonne "
    "OFELIA_CODE (ou INTERNAL_ID) et/ou EXTERNAL_CODE, sinon les exemplaires à "
    "mettre à jour ne peuvent pas être retrouvés."
)
_EXPORT_INTRO = (
    "Le fichier porte exactement les colonnes que BibliOfelia sait relire, plus "
    "les codes qui identifient l'exemplaire (OFELIA_CODE, INTERNAL_ID). C'est le "
    "point de départ d'une correction en masse : exportez, corrigez dans Excel, "
    "renvoyez le fichier par « Mettre à jour les exemplaires »."
)
_EXPORT_HINT = (
    "Une notice en plusieurs exemplaires sort sur plusieurs lignes : "
    "l'emplacement, l'état, la provenance et le code externe appartiennent à "
    "l'exemplaire, pas à la fiche."
)
_UPDATE_INTRO = (
    "Téléversez un fichier .xlsx pour corriger des exemplaires <strong>déjà "
    "présents</strong> dans le catalogue. Aucune notice ni aucun exemplaire "
    "n'est créé : une ligne dont l'exemplaire est introuvable est signalée, pas "
    "ajoutée."
)
_UPDATE_KEY_COL = "code Ofelia de l'exemplaire (EAN13 « 290… » ou code interne « OFL-… »)"
_UPDATE_KEY_RULE = (
    "Au moins l'une des deux colonnes doit être renseignée sur chaque ligne. Si "
    "les deux le sont, <strong>c'est le code Ofelia qui identifie "
    "l'exemplaire</strong> et le code externe de la ligne lui est appliqué — "
    "c'est ainsi qu'on attribue des codes externes en masse."
)
_UPDATE_OTHER_COLS = (
    "Toutes les autres colonnes de l'import sont acceptées et facultatives : "
    "TITLE, AUTHOR, CATEGORY, CATEGORY_ABBR, TYPE, EDITOR, YEAR, LANGUAGE, TAGS, "
    "CONDITION, PROVENANCE, LOCATION et ISBN. Une cellule remplie remplace la "
    "valeur existante ; <strong>une cellule vide laisse la valeur en place</strong> "
    "(le fichier ne sert donc pas à effacer un champ)."
)
_UPDATE_HINT = (
    "Le plus simple est de partir du fichier produit par « Exporter le "
    "catalogue » : il porte déjà les bonnes colonnes et les bons codes."
)
_UPDATE_ERRORS = (
    "L'exemplaire de ces lignes n'a pas été retrouvé, ou la ligne ne porte aucun "
    "code d'identification. La mise à jour ne crée jamais d'exemplaire : ces "
    "lignes n'ont rien modifié. Le détail est listé plus bas."
)
_W_OFELIA_UNKNOWN = (
    "Aucun exemplaire ne porte ce code Ofelia : ligne ignorée. Vérifiez le code, "
    "ou repartez d'un export récent du catalogue."
)
_W_EXTERNAL_UNKNOWN = (
    "Aucun exemplaire ne porte ce code externe : ligne ignorée. Un code externe "
    "s'attribue en mise à jour à partir du code Ofelia, ou à la main sur la fiche "
    "de l'exemplaire."
)
_W_NO_KEY = (
    "Ligne sans code Ofelia ni code externe : impossible de savoir quel "
    "exemplaire mettre à jour."
)
_W_ROW_ERROR = (
    "Cette ligne a provoqué une erreur technique et a été laissée de côté ; les "
    "autres lignes du fichier ont bien été traitées."
)
_W_ISBN_CONFLICT = (
    "Cet ISBN appartient déjà à une autre notice : il n'a pas été repris, le "
    "reste de la ligne est appliqué."
)
_W_LOCATION_UNKNOWN = (
    "Emplacement inconnu : créez-le dans Avancé → Méta-données → Emplacements, "
    "ou corrigez le code. Le reste de la ligne est appliqué."
)
_PAGE_SUB = "Vérifier, importer, exporter ou mettre à jour un fichier Excel d'inventaire."

# FEAT-080 — écrans de prêt et de retour.
_RETURN_OK_MEMBER = "Retour effectué : %(title)s, rendu par %(member)s."
_RETURN_OK = "Retour effectué : %(title)s."
_NO_LOAN_ROW = "Aucun prêt actif — rien à solder"
_REINTEGRATED_ROW = "Retour effectué — livre perdu réintégré au fonds"

# FEAT-081 — ancienne carte d'usager.
_REPLACED_CARD = (
    "Carte remplacée : %(old)s. %(name)s utilise désormais la carte n° %(new)s."
)
_REPRINT_CARD = (
    "La carte n° %(old)s est désormais l'ancienne : imprimez la nouvelle carte "
    "et remettez-la à l'usager. En attendant, l'ancienne reste reconnue au scan "
    "et le signale."
)

# Bloc pluriel : la carte d'export annonce le nombre d'exemplaires du catalogue.
_EXPORT_COUNT_1 = (
    "Télécharge la totalité du catalogue dans un fichier .xlsx : "
    "<strong>%(n)s exemplaire</strong>, une ligne par exemplaire."
)
_EXPORT_COUNT_N = (
    "Télécharge la totalité du catalogue dans un fichier .xlsx : "
    "<strong>%(n)s exemplaires</strong>, une ligne par exemplaire."
)


TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        _NO_KEY_COLUMN: (
            "Missing identifying column: the file must have an OFELIA_CODE (or "
            "INTERNAL_ID) and/or EXTERNAL_CODE column, otherwise the copies to "
            "update cannot be found."
        ),
        "Mise à jour": "Update",
        "Mise à jour lancée. Suivez l'avancement ici.": (
            "Update started. Track progress here."
        ),
        _EXPORT_INTRO: (
            "The file carries exactly the columns BibliOfelia can read back, plus "
            "the codes that identify the copy (OFELIA_CODE, INTERNAL_ID). It is "
            "the starting point for a bulk correction: export, fix in Excel, then "
            "send the file back through “Update copies”."
        ),
        "Exporter le catalogue": "Export the catalogue",
        _EXPORT_HINT: (
            "A record with several copies comes out on several rows: location, "
            "condition, provenance and external code belong to the copy, not to "
            "the record."
        ),
        _UPDATE_INTRO: (
            "Upload an .xlsx file to correct copies <strong>already in</strong> "
            "the catalogue. No record and no copy is ever created: a row whose "
            "copy cannot be found is reported, not added."
        ),
        _UPDATE_KEY_COL: (
            "Ofelia code of the copy (EAN13 “290…” or internal code “OFL-…”)"
        ),
        "code externe de l'exemplaire": "external code of the copy",
        _UPDATE_KEY_RULE: (
            "At least one of the two columns must be filled in on every row. If "
            "both are, <strong>the Ofelia code is what identifies the "
            "copy</strong> and the row's external code is applied to it — that is "
            "how external codes are assigned in bulk."
        ),
        _UPDATE_OTHER_COLS: (
            "Every other import column is accepted and optional: TITLE, AUTHOR, "
            "CATEGORY, CATEGORY_ABBR, TYPE, EDITOR, YEAR, LANGUAGE, TAGS, "
            "CONDITION, PROVENANCE, LOCATION and ISBN. A filled cell replaces the "
            "existing value; <strong>an empty cell leaves the value alone</strong> "
            "(so the file cannot be used to clear a field)."
        ),
        "Mettre à jour les exemplaires": "Update the copies",
        _UPDATE_HINT: (
            "The easiest way is to start from the file produced by “Export the "
            "catalogue”: it already has the right columns and the right codes."
        ),
        _UPDATE_ERRORS: (
            "The copy for these rows was not found, or the row carries no "
            "identifying code. The update never creates a copy: these rows changed "
            "nothing. Details are listed below."
        ),
        "Exemplaires modifiés": "Copies changed",
        "Lignes sans changement": "Rows with no change",
        _W_OFELIA_UNKNOWN: (
            "No copy carries this Ofelia code: row skipped. Check the code, or "
            "start again from a recent catalogue export."
        ),
        _W_EXTERNAL_UNKNOWN: (
            "No copy carries this external code: row skipped. An external code is "
            "assigned by updating from the Ofelia code, or by hand on the copy's "
            "page."
        ),
        _W_NO_KEY: (
            "Row with neither an Ofelia code nor an external code: there is no way "
            "to tell which copy to update."
        ),
        _W_ROW_ERROR: (
            "This row raised a technical error and was left aside; the other rows "
            "of the file were processed normally."
        ),
        _W_ISBN_CONFLICT: (
            "This ISBN already belongs to another record: it was not applied, the "
            "rest of the row was."
        ),
        _W_LOCATION_UNKNOWN: (
            "Unknown location: create it under Advanced → Metadata → Locations, or "
            "fix the code. The rest of the row was applied."
        ),
        _PAGE_SUB: "Check, import, export or update an Excel inventory file.",
        "Mettre à jour des exemplaires": "Update copies",
        _RETURN_OK_MEMBER: "Return recorded: %(title)s, brought back by %(member)s.",
        _RETURN_OK: "Return recorded: %(title)s.",
        _NO_LOAN_ROW: "No active loan — nothing to settle",
        _REINTEGRATED_ROW: "Return recorded — lost book put back into the collection",
        "Retour effectué": "Return recorded",
        "Rendu par": "Returned by",
        "Ofelia": "Ofelia",
        "Externe": "External code",
        _REPLACED_CARD: (
            "Replaced card: %(old)s. %(name)s now uses card no. %(new)s."
        ),
        _REPRINT_CARD: (
            "Card no. %(old)s is now the old one: print the new card and hand it "
            "to the member. Until then, the old one is still recognised when "
            "scanned, and flagged as replaced."
        ),
    },
    "es": {
        _NO_KEY_COLUMN: (
            "Falta la columna de identificación: el archivo debe tener una columna "
            "OFELIA_CODE (o INTERNAL_ID) y/o EXTERNAL_CODE, de lo contrario no se "
            "pueden encontrar los ejemplares que hay que actualizar."
        ),
        "Mise à jour": "Actualización",
        "Mise à jour lancée. Suivez l'avancement ici.": (
            "Actualización iniciada. Siga el avance aquí."
        ),
        _EXPORT_INTRO: (
            "El archivo lleva exactamente las columnas que BibliOfelia sabe releer, "
            "más los códigos que identifican el ejemplar (OFELIA_CODE, "
            "INTERNAL_ID). Es el punto de partida de una corrección masiva: "
            "exporte, corrija en Excel y devuelva el archivo con «Actualizar los "
            "ejemplares»."
        ),
        "Exporter le catalogue": "Exportar el catálogo",
        _EXPORT_HINT: (
            "Un registro con varios ejemplares sale en varias líneas: la ubicación, "
            "el estado, la procedencia y el código externo pertenecen al ejemplar, "
            "no a la ficha."
        ),
        _UPDATE_INTRO: (
            "Suba un archivo .xlsx para corregir ejemplares <strong>ya "
            "presentes</strong> en el catálogo. No se crea ningún registro ni "
            "ningún ejemplar: una línea cuyo ejemplar no se encuentra se señala, no "
            "se añade."
        ),
        _UPDATE_KEY_COL: (
            "código Ofelia del ejemplar (EAN13 «290…» o código interno «OFL-…»)"
        ),
        "code externe de l'exemplaire": "código externo del ejemplar",
        _UPDATE_KEY_RULE: (
            "Al menos una de las dos columnas debe estar rellenada en cada línea. "
            "Si lo están las dos, <strong>es el código Ofelia el que identifica el "
            "ejemplar</strong> y el código externo de la línea se le aplica: así se "
            "asignan códigos externos de forma masiva."
        ),
        _UPDATE_OTHER_COLS: (
            "Se aceptan todas las demás columnas de la importación, y son "
            "opcionales: TITLE, AUTHOR, CATEGORY, CATEGORY_ABBR, TYPE, EDITOR, "
            "YEAR, LANGUAGE, TAGS, CONDITION, PROVENANCE, LOCATION e ISBN. Una "
            "celda rellenada sustituye el valor existente; <strong>una celda vacía "
            "deja el valor tal cual</strong> (el archivo no sirve, pues, para "
            "borrar un campo)."
        ),
        "Mettre à jour les exemplaires": "Actualizar los ejemplares",
        _UPDATE_HINT: (
            "Lo más sencillo es partir del archivo que produce «Exportar el "
            "catálogo»: ya lleva las columnas y los códigos correctos."
        ),
        _UPDATE_ERRORS: (
            "No se encontró el ejemplar de estas líneas, o la línea no lleva ningún "
            "código de identificación. La actualización nunca crea un ejemplar: "
            "estas líneas no modificaron nada. El detalle se lista más abajo."
        ),
        "Exemplaires modifiés": "Ejemplares modificados",
        "Lignes sans changement": "Líneas sin cambio",
        _W_OFELIA_UNKNOWN: (
            "Ningún ejemplar lleva este código Ofelia: línea ignorada. Compruebe el "
            "código o vuelva a partir de una exportación reciente del catálogo."
        ),
        _W_EXTERNAL_UNKNOWN: (
            "Ningún ejemplar lleva este código externo: línea ignorada. Un código "
            "externo se asigna al actualizar a partir del código Ofelia, o a mano "
            "en la ficha del ejemplar."
        ),
        _W_NO_KEY: (
            "Línea sin código Ofelia ni código externo: es imposible saber qué "
            "ejemplar hay que actualizar."
        ),
        _W_ROW_ERROR: (
            "Esta línea provocó un error técnico y se dejó de lado; las demás "
            "líneas del archivo sí se procesaron."
        ),
        _W_ISBN_CONFLICT: (
            "Este ISBN ya pertenece a otro registro: no se aplicó, el resto de la "
            "línea sí."
        ),
        _W_LOCATION_UNKNOWN: (
            "Ubicación desconocida: créela en Avanzado → Metadatos → Ubicaciones, o "
            "corrija el código. El resto de la línea se aplicó."
        ),
        _PAGE_SUB: (
            "Verificar, importar, exportar o actualizar un archivo Excel de "
            "inventario."
        ),
        "Mettre à jour des exemplaires": "Actualizar ejemplares",
        _RETURN_OK_MEMBER: "Devolución registrada: %(title)s, entregado por %(member)s.",
        _RETURN_OK: "Devolución registrada: %(title)s.",
        _NO_LOAN_ROW: "Ningún préstamo activo — nada que saldar",
        _REINTEGRATED_ROW: "Devolución registrada — libro perdido reintegrado al fondo",
        "Retour effectué": "Devolución registrada",
        "Rendu par": "Devuelto por",
        "Ofelia": "Ofelia",
        "Externe": "Código externo",
        _REPLACED_CARD: (
            "Tarjeta sustituida: %(old)s. %(name)s usa ahora la tarjeta n.º %(new)s."
        ),
        _REPRINT_CARD: (
            "La tarjeta n.º %(old)s es ahora la antigua: imprima la nueva tarjeta "
            "y entréguesela al usuario. Mientras tanto, la antigua sigue "
            "reconociéndose al escanear, y se avisa de ello."
        ),
    },
    "mg": {
        _NO_KEY_COLUMN: (
            "Tsy misy ny fariana famantarana : tsy maintsy manana fariana "
            "OFELIA_CODE (na INTERNAL_ID) sy/na EXTERNAL_CODE ilay rakitra, raha "
            "tsy izany dia tsy hita ireo kopia hohavaozina."
        ),
        "Mise à jour": "Fanavaozana",
        "Mise à jour lancée. Suivez l'avancement ici.": (
            "Nanomboka ny fanavaozana. Araho eto ny fandrosoana."
        ),
        _EXPORT_INTRO: (
            "Mitondra tsy misy ombiombiny ireo fariana hain'ny BibliOfelia vakina "
            "indray ilay rakitra, miampy ny kaody manondro ny kopia (OFELIA_CODE, "
            "INTERNAL_ID). Izy no fiaingana amin'ny fanitsiana be dia be : "
            "avoahy, ahitsio ao amin'ny Excel, dia averino amin'ny « Hanavao ireo "
            "kopia »."
        ),
        "Exporter le catalogue": "Havoaka ny katalaogy",
        _EXPORT_HINT: (
            "Ny raki-tsoratra manana kopia maromaro dia mivoaka andalana maromaro : "
            "ny toerana, ny toe-javatra, ny fiaviana ary ny kaody ivelany dia an'ny "
            "kopia, fa tsy an'ny raki-tsoratra."
        ),
        _UPDATE_INTRO: (
            "Ampidiro ny rakitra .xlsx hanitsiana kopia <strong>efa ao</strong> "
            "amin'ny katalaogy. Tsy misy raki-tsoratra na kopia noforonina : ny "
            "andalana tsy ahitana ny kopiany dia tsindriana, fa tsy ampiana."
        ),
        _UPDATE_KEY_COL: (
            "kaody Ofelia an'ny kopia (EAN13 « 290… » na kaody anatiny « OFL-… »)"
        ),
        "code externe de l'exemplaire": "kaody ivelany an'ny kopia",
        _UPDATE_KEY_RULE: (
            "Tsy maintsy fenoina isaky ny andalana ny iray farafahakeliny amin'ireo "
            "fariana roa. Raha feno izy roa, <strong>ny kaody Ofelia no manondro "
            "ny kopia</strong> ary ampiharina aminy ny kaody ivelany eo amin'ny "
            "andalana — izany no fomba fanomezana kaody ivelany betsaka."
        ),
        _UPDATE_OTHER_COLS: (
            "Ekena ary tsy voatery ireo fariana hafa rehetra amin'ny fampidirana : "
            "TITLE, AUTHOR, CATEGORY, CATEGORY_ABBR, TYPE, EDITOR, YEAR, LANGUAGE, "
            "TAGS, CONDITION, PROVENANCE, LOCATION ary ISBN. Ny efitra feno dia "
            "manolo ny sanda misy ; <strong>ny efitra foana dia mamela ny sanda "
            "eo</strong> (tsy azo ampiasaina hamafana fariana àry ilay rakitra)."
        ),
        "Mettre à jour les exemplaires": "Hanavao ireo kopia",
        _UPDATE_HINT: (
            "Ny tsotra indrindra dia ny miainga amin'ny rakitra avy amin'ny "
            "« Havoaka ny katalaogy » : efa mitondra ny fariana sy ny kaody marina "
            "izy."
        ),
        _UPDATE_ERRORS: (
            "Tsy hita ny kopian'ireo andalana ireo, na tsy mitondra kaody "
            "famantarana ilay andalana. Tsy mamorona kopia mihitsy ny fanavaozana : "
            "tsy nanova na inona na inona ireo andalana ireo. Ao ambany ny "
            "antsipiriany."
        ),
        "Exemplaires modifiés": "Kopia novaina",
        "Lignes sans changement": "Andalana tsy niova",
        _W_OFELIA_UNKNOWN: (
            "Tsy misy kopia mitondra io kaody Ofelia io : nalaina an-tsirambina ny "
            "andalana. Hamarino ny kaody, na miaingà amin'ny famoahana katalaogy "
            "vaovao."
        ),
        _W_EXTERNAL_UNKNOWN: (
            "Tsy misy kopia mitondra io kaody ivelany io : nalaina an-tsirambina ny "
            "andalana. Ny kaody ivelany dia omena amin'ny fanavaozana miainga "
            "amin'ny kaody Ofelia, na an-tanana eo amin'ny pejin'ny kopia."
        ),
        _W_NO_KEY: (
            "Andalana tsy misy kaody Ofelia na kaody ivelany : tsy fantatra izay "
            "kopia tokony hohavaozina."
        ),
        _W_ROW_ERROR: (
            "Nahatonga hadisoana ara-teknika ity andalana ity ka navela ; voakarakara "
            "tsara kosa ny andalana hafa ao amin'ny rakitra."
        ),
        _W_ISBN_CONFLICT: (
            "Efa an'ny raki-tsoratra hafa io ISBN io : tsy nampiharina izy, fa "
            "nampiharina kosa ny ambin'ny andalana."
        ),
        _W_LOCATION_UNKNOWN: (
            "Toerana tsy fantatra : foronina ao amin'ny Mandroso → Angona → Toerana, "
            "na ahitsio ny kaody. Nampiharina ny ambin'ny andalana."
        ),
        _PAGE_SUB: (
            "Hamarino, ampidiro, avoahy na havaozy ny rakitra Excel momba ny "
            "fanisam-bokatra."
        ),
        "Mettre à jour des exemplaires": "Hanavao kopia",
        _RETURN_OK_MEMBER: "Vita ny famerenana : %(title)s, naverin'i %(member)s.",
        _RETURN_OK: "Vita ny famerenana : %(title)s.",
        _NO_LOAN_ROW: "Tsy misy fampindramana mavitrika — tsy misy hovahana",
        _REINTEGRATED_ROW: "Vita ny famerenana — naverina tao amin'ny tahiry ny boky very",
        "Retour effectué": "Vita ny famerenana",
        "Rendu par": "Naverin'i",
        "Ofelia": "Ofelia",
        "Externe": "Kaody ivelany",
        _REPLACED_CARD: (
            "Karatra nosoloina : %(old)s. Ny karatra n° %(new)s no ampiasain'i "
            "%(name)s izao."
        ),
        _REPRINT_CARD: (
            "Lasa taloha ny karatra n° %(old)s : atontay ny karatra vaovao dia "
            "omeo ilay mpampiasa. Mandra-pahatongan'izay, mbola fantatra rehefa "
            "kitihina ilay taloha, ary voalaza izany."
        ),
    },
}


PLURALS: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        _EXPORT_COUNT_1: (
            "Downloads the whole catalogue as an .xlsx file: "
            "<strong>%(n)s copy</strong>, one row per copy.",
            "Downloads the whole catalogue as an .xlsx file: "
            "<strong>%(n)s copies</strong>, one row per copy.",
        ),
        "%(n)s ligne non appliquée": (
            "%(n)s row not applied",
            "%(n)s rows not applied",
        ),
        "%(n)s an": (
            "%(n)s year old",
            "%(n)s years old",
        ),
    },
    "es": {
        _EXPORT_COUNT_1: (
            "Descarga la totalidad del catálogo en un archivo .xlsx: "
            "<strong>%(n)s ejemplar</strong>, una línea por ejemplar.",
            "Descarga la totalidad del catálogo en un archivo .xlsx: "
            "<strong>%(n)s ejemplares</strong>, una línea por ejemplar.",
        ),
        "%(n)s ligne non appliquée": (
            "%(n)s línea no aplicada",
            "%(n)s líneas no aplicadas",
        ),
        "%(n)s an": (
            "%(n)s año",
            "%(n)s años",
        ),
    },
    "mg": {
        _EXPORT_COUNT_1: (
            "Maka ny katalaogy manontolo amin'ny rakitra .xlsx : "
            "<strong>kopia %(n)s</strong>, andalana iray isaky ny kopia.",
            "Maka ny katalaogy manontolo amin'ny rakitra .xlsx : "
            "<strong>kopia %(n)s</strong>, andalana iray isaky ny kopia.",
        ),
        "%(n)s ligne non appliquée": (
            "Andalana %(n)s tsy nampiharina",
            "Andalana %(n)s tsy nampiharina",
        ),
        "%(n)s an": (
            "%(n)s taona",
            "%(n)s taona",
        ),
    },
}


def _unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\\\", "\\")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


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
    """Applique les traductions du sprint à un `.po`. Renvoie (simples, pluriels)."""
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
        single, plural = apply_lang(lang)
        print(f"[{lang}] {single} chaîne(s) + {plural} pluriel(s)")


if __name__ == "__main__":
    main()
