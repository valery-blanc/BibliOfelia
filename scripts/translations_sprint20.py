#!/usr/bin/env python3
"""Traductions Sprint 20 / FEAT-050 (catalogage Excel) — FR → EN/ES/MG.

Applique les traductions directement aux fichiers .po (stdlib, sans Docker).
Overwrite + de-fuzzy (cf. translations_sprint19.py).
Rejoue : python scripts/translations_sprint20.py
"""
from __future__ import annotations

from pathlib import Path

_VERIFY_INTRO = (
    "Téléversez un fichier .xlsx avec les colonnes ID, TITLE, AUTHOR, ISBN. "
    "BibliOfelia interroge OpenLibrary, Google Books, la BNF et la BNE — "
    "d'abord par ISBN, puis par titre + auteur — et vous renvoie le même "
    "fichier annoté, avec un score de confiance pour les appariements incertains."
)
_IMPORT_INTRO = (
    "Téléversez un fichier .xlsx avec au moins une colonne ISBN. Chaque ISBN "
    "devient une notice et un exemplaire dans le catalogue (les ISBN déjà "
    "connus ajoutent simplement un exemplaire à la notice existante)."
)
_IMPORT_NOTE = (
    "L'import crée un lot de catalogage visible dans « Catalogage par scan ». "
    "Les métadonnées (titre, auteur…) peuvent ensuite être complétées via "
    "l'enrichissement."
)
_LOC_OPT = "optionnel : code d'emplacement (sinon l'exemplaire est créé sans emplacement)"

# BUG-019 : bandeaux quota Google Books (429). msgid = chaîne concaténée.
_RL_EXCEL = (
    "%(n)s ligne(s) ont pu rester incomplètes car le quota d'une source en ligne "
    "(Google Books) a été atteint (colonne SOURCE_BY_ISBN = RATE_LIMITED). "
    "Relancez la vérification demain — le quota se réinitialise chaque jour."
)
_RL_ENRICH = (
    "%(n)s notice(s) n'ont pas pu être complétées car le quota d'une source en "
    "ligne (Google Books) a été atteint. Relancez cet enrichissement demain — le "
    "quota se réinitialise chaque jour — pour compléter le reste."
)

TRANSLATIONS = {
    "en": {
        # FEAT-051 : filtre emplacement dans le catalogue
        "Tous emplacements": "All locations",
        # BUG-019 : quota Google Books (429)
        "Quota Google Books atteint": "Google Books quota reached",
        "Quota atteint": "Quota reached",
        "quota atteint — à relancer": "quota reached — re-run later",
        _RL_EXCEL: (
            "%(n)s row(s) may have stayed incomplete because an online source's "
            "quota (Google Books) was reached (column SOURCE_BY_ISBN = "
            "RATE_LIMITED). Re-run the verification tomorrow — the quota resets "
            "every day."
        ),
        _RL_ENRICH: (
            "%(n)s record(s) could not be completed because an online source's "
            "quota (Google Books) was reached. Re-run this enrichment tomorrow — "
            "the quota resets every day — to complete the rest."
        ),
        "catalogage Excel": "Excel cataloging",
        "catalogages Excel": "Excel catalogings",
        "Vérification": "Verification",
        "Aucun fichier sélectionné.": "No file selected.",
        "Vérification lancée. Suivez l'avancement ici.": "Verification started. Track progress here.",
        "Import lancé. Suivez l'avancement ici.": "Import started. Track progress here.",
        "Catalogage Excel": "Excel cataloging",
        "Vérifier ou importer un fichier Excel d'inventaire (ISBN, titre, auteur, emplacement, catégorie).":
            "Check or import an Excel inventory file (ISBN, title, author, location, category).",
        "Vérifier ou importer un fichier Excel d'inventaire.":
            "Check or import an Excel inventory file.",
        "Vérifier un fichier": "Check a file",
        "Importer dans BibliOfelia": "Import into BibliOfelia",
        "Travaux récents": "Recent jobs",
        "Type": "Type",
        "Aucun travail lancé pour l'instant.": "No job started yet.",
        _VERIFY_INTRO: (
            "Upload a .xlsx file with the columns ID, TITLE, AUTHOR, ISBN. "
            "BibliOfelia queries OpenLibrary, Google Books, the BNF and the BNE — "
            "first by ISBN, then by title + author — and returns the same file "
            "annotated, with a confidence score for uncertain matches."
        ),
        "Lancer la vérification": "Start verification",
        "Compter environ 10 minutes pour 1000 lignes. Le traitement se fait en tâche de fond.":
            "Expect about 10 minutes per 1000 rows. Processing runs in the background.",
        _IMPORT_INTRO: (
            "Upload a .xlsx file with at least one ISBN column. Each ISBN becomes "
            "a record and a copy in the catalog (already known ISBNs simply add a "
            "copy to the existing record)."
        ),
        "obligatoire": "required",
        _LOC_OPT: "optional: location code (otherwise the copy is created without a location)",
        "optionnel : nom de catégorie existante": "optional: name of an existing category",
        "Importer dans le catalogue": "Import into the catalog",
        _IMPORT_NOTE: (
            "The import creates a cataloging batch visible under “Cataloging by "
            "scan”. The metadata (title, author…) can then be completed via "
            "enrichment."
        ),
        "Catalogage Excel #%(id)s": "Excel cataloging #%(id)s",
        "Traitement en cours… cette page se rafraîchit automatiquement.":
            "Processing… this page refreshes automatically.",
        "Trouvées par ISBN": "Found by ISBN",
        "Trouvées par titre+auteur": "Found by title+author",
        "Non trouvées": "Not found",
        "Notices complétées": "Records completed",
        "Notices créées": "Records created",
        "Télécharger le fichier annoté": "Download the annotated file",
        "Voir le lot importé": "View the imported batch",
        "Avertissements": "Warnings",
        "Ligne": "Row",
        "Détail": "Detail",
    },
    "es": {
        # FEAT-051 : filtre emplacement dans le catalogue
        "Tous emplacements": "Todas las ubicaciones",
        # BUG-019 : quota Google Books (429)
        "Quota Google Books atteint": "Cuota de Google Books alcanzada",
        "Quota atteint": "Cuota alcanzada",
        "quota atteint — à relancer": "cuota alcanzada — reintentar más tarde",
        _RL_EXCEL: (
            "%(n)s fila(s) pueden haber quedado incompletas porque se alcanzó la "
            "cuota de una fuente en línea (Google Books) (columna SOURCE_BY_ISBN = "
            "RATE_LIMITED). Vuelva a lanzar la verificación mañana — la cuota se "
            "reinicia cada día."
        ),
        _RL_ENRICH: (
            "%(n)s ficha(s) no pudieron completarse porque se alcanzó la cuota de "
            "una fuente en línea (Google Books). Vuelva a lanzar este "
            "enriquecimiento mañana — la cuota se reinicia cada día — para "
            "completar el resto."
        ),
        "catalogage Excel": "catalogación Excel",
        "catalogages Excel": "catalogaciones Excel",
        "Vérification": "Verificación",
        "Aucun fichier sélectionné.": "Ningún archivo seleccionado.",
        "Vérification lancée. Suivez l'avancement ici.": "Verificación iniciada. Siga el avance aquí.",
        "Import lancé. Suivez l'avancement ici.": "Importación iniciada. Siga el avance aquí.",
        "Catalogage Excel": "Catalogación Excel",
        "Vérifier ou importer un fichier Excel d'inventaire (ISBN, titre, auteur, emplacement, catégorie).":
            "Verificar o importar un archivo Excel de inventario (ISBN, título, autor, ubicación, categoría).",
        "Vérifier ou importer un fichier Excel d'inventaire.":
            "Verificar o importar un archivo Excel de inventario.",
        "Vérifier un fichier": "Verificar un archivo",
        "Importer dans BibliOfelia": "Importar en BibliOfelia",
        "Travaux récents": "Trabajos recientes",
        "Type": "Tipo",
        "Aucun travail lancé pour l'instant.": "Ningún trabajo iniciado por ahora.",
        _VERIFY_INTRO: (
            "Suba un archivo .xlsx con las columnas ID, TITLE, AUTHOR, ISBN. "
            "BibliOfelia consulta OpenLibrary, Google Books, la BNF y la BNE — "
            "primero por ISBN, luego por título + autor — y le devuelve el mismo "
            "archivo anotado, con una puntuación de confianza para las coincidencias inciertas."
        ),
        "Lancer la vérification": "Iniciar la verificación",
        "Compter environ 10 minutes pour 1000 lignes. Le traitement se fait en tâche de fond.":
            "Cuente unos 10 minutos por cada 1000 filas. El procesamiento se realiza en segundo plano.",
        _IMPORT_INTRO: (
            "Suba un archivo .xlsx con al menos una columna ISBN. Cada ISBN se "
            "convierte en una ficha y un ejemplar en el catálogo (los ISBN ya "
            "conocidos simplemente añaden un ejemplar a la ficha existente)."
        ),
        "obligatoire": "obligatorio",
        _LOC_OPT: "opcional: código de ubicación (de lo contrario el ejemplar se crea sin ubicación)",
        "optionnel : nom de catégorie existante": "opcional: nombre de una categoría existente",
        "Importer dans le catalogue": "Importar en el catálogo",
        _IMPORT_NOTE: (
            "La importación crea un lote de catalogación visible en «Catalogación "
            "por escaneo». Los metadatos (título, autor…) pueden completarse "
            "después mediante el enriquecimiento."
        ),
        "Catalogage Excel #%(id)s": "Catalogación Excel n.º %(id)s",
        "Traitement en cours… cette page se rafraîchit automatiquement.":
            "Procesando… esta página se actualiza automáticamente.",
        "Trouvées par ISBN": "Encontradas por ISBN",
        "Trouvées par titre+auteur": "Encontradas por título+autor",
        "Non trouvées": "No encontradas",
        "Notices complétées": "Fichas completadas",
        "Notices créées": "Fichas creadas",
        "Télécharger le fichier annoté": "Descargar el archivo anotado",
        "Voir le lot importé": "Ver el lote importado",
        "Avertissements": "Advertencias",
        "Ligne": "Fila",
        "Détail": "Detalle",
    },
    "mg": {
        # FEAT-051 : filtre emplacement dans le catalogue
        "Tous emplacements": "Toerana rehetra",
        # BUG-019 : quota Google Books (429)
        "Quota Google Books atteint": "Tratra ny fetran'ny Google Books",
        "Quota atteint": "Tratra ny fetra",
        "quota atteint — à relancer": "tratra ny fetra — averina atao",
        _RL_EXCEL: (
            "%(n)s andalana mety tsy feno satria tratra ny fetran'ny loharano "
            "an-tserasera (Google Books) (tsanganana SOURCE_BY_ISBN = "
            "RATE_LIMITED). Avereno atao rahampitso ny fanamarinana — miverina "
            "isan'andro ny fetra."
        ),
        _RL_ENRICH: (
            "%(n)s notice no tsy afaka nofenoina satria tratra ny fetran'ny "
            "loharano an-tserasera (Google Books). Avereno atao rahampitso ity "
            "fampitomboana ity — miverina isan'andro ny fetra — mba hamenoana ny "
            "ambiny."
        ),
        "catalogage Excel": "katalaogy Excel",
        "catalogages Excel": "katalaogy Excel",
        "Vérification": "Fanamarinana",
        "Aucun fichier sélectionné.": "Tsy misy rakitra voafidy.",
        "Vérification lancée. Suivez l'avancement ici.":
            "Nanomboka ny fanamarinana. Araho eto ny fandrosoana.",
        "Import lancé. Suivez l'avancement ici.":
            "Nanomboka ny fanafarana. Araho eto ny fandrosoana.",
        "Catalogage Excel": "Katalaogy Excel",
        "Vérifier ou importer un fichier Excel d'inventaire (ISBN, titre, auteur, emplacement, catégorie).":
            "Hamarino na afaro rakitra Excel an'ny fanisana (ISBN, lohateny, mpanoratra, toerana, sokajy).",
        "Vérifier ou importer un fichier Excel d'inventaire.":
            "Hamarino na afaro rakitra Excel an'ny fanisana.",
        "Vérifier un fichier": "Hamarina rakitra",
        "Importer dans BibliOfelia": "Afaro ao amin'ny BibliOfelia",
        "Travaux récents": "Asa vao haingana",
        "Type": "Karazana",
        "Aucun travail lancé pour l'instant.": "Tsy misy asa natomboka aloha.",
        _VERIFY_INTRO: (
            "Alefaso rakitra .xlsx misy ny tsanganana ID, TITLE, AUTHOR, ISBN. "
            "Manontany ny OpenLibrary, Google Books, BNF ary BNE ny BibliOfelia — "
            "amin'ny ISBN aloha, dia amin'ny lohateny + mpanoratra — ka mamerina "
            "ilay rakitra misy fanamarihana, miaraka amin'ny isa fahatokisana ho "
            "an'ny fifanarahana tsy azo antoka."
        ),
        "Lancer la vérification": "Atombohy ny fanamarinana",
        "Compter environ 10 minutes pour 1000 lignes. Le traitement se fait en tâche de fond.":
            "Manodidina ny 10 minitra isaky ny andalana 1000. Atao ao ambadika ny fanodinana.",
        _IMPORT_INTRO: (
            "Alefaso rakitra .xlsx misy farafahakeliny tsanganana ISBN iray. "
            "Lasa notice sy kopia ao amin'ny katalaogy ny ISBN tsirairay (ny ISBN "
            "efa fantatra dia manampy kopia fotsiny amin'ny notice efa misy)."
        ),
        "obligatoire": "tsy maintsy",
        _LOC_OPT: "tsy voatery: kaody toerana (raha tsy izany dia noforonina tsy misy toerana ny kopia)",
        "optionnel : nom de catégorie existante": "tsy voatery: anaran'ny sokajy efa misy",
        "Importer dans le catalogue": "Afaro ao amin'ny katalaogy",
        _IMPORT_NOTE: (
            "Ny fanafarana dia mamorona andian-katalaogy hita ao amin'ny "
            "« Katalaogy amin'ny scan ». Azo fenoina aorian'izay amin'ny alalan'ny "
            "fampitomboana ny metadata (lohateny, mpanoratra…)."
        ),
        "Catalogage Excel #%(id)s": "Katalaogy Excel #%(id)s",
        "Traitement en cours… cette page se rafraîchit automatiquement.":
            "Eo am-panodinana… mihavao ho azy ity pejy ity.",
        "Trouvées par ISBN": "Hita tamin'ny ISBN",
        "Trouvées par titre+auteur": "Hita tamin'ny lohateny+mpanoratra",
        "Non trouvées": "Tsy hita",
        "Notices complétées": "Notice nofenoina",
        "Notices créées": "Notice noforonina",
        "Télécharger le fichier annoté": "Alaivo ny rakitra misy fanamarihana",
        "Voir le lot importé": "Hijery ny andiana nafarana",
        "Avertissements": "Fampitandremana",
        "Ligne": "Andalana",
        "Détail": "Antsipiriany",
    },
}

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"


def _po_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def _defuzz(comment: str) -> str | None:
    if not comment.startswith("#,"):
        return comment
    flags = [f.strip() for f in comment[2:].split(",") if f.strip()]
    flags = [f for f in flags if f != "fuzzy"]
    return ("#, " + ", ".join(flags)) if flags else None


def _strip_trailing_fuzzy(out: list[str]) -> None:
    k = len(out) - 1
    while k >= 0 and out[k].startswith("#"):
        k -= 1
    block = out[k + 1:]
    if not block:
        return
    new: list[str] = []
    for c in block:
        if c.startswith("#|"):
            continue
        d = _defuzz(c)
        if d is not None:
            new.append(d)
    out[k + 1:] = new


def apply_lang(lang: str, mapping: dict[str, str]) -> int:
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0
    lines = po_path.read_text(encoding="utf-8").splitlines(keepends=False)
    out: list[str] = []
    count = 0
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if line.startswith("msgid ") and not (
            i + 1 < n and lines[i + 1].startswith("msgid_plural")
        ):
            parts = [_unescape(line[len("msgid "):].strip().strip('"'))]
            j = i + 1
            while j < n and lines[j].startswith('"'):
                parts.append(_unescape(lines[j].strip().strip('"')))
                j += 1
            msgid = "".join(parts)
            if msgid in mapping and mapping[msgid]:
                _strip_trailing_fuzzy(out)
                m = j + 1
                while m < n and lines[m].startswith('"'):
                    m += 1
                out.extend(lines[i:j])
                out.append(f'msgstr "{_po_escape(mapping[msgid])}"')
                count += 1
                i = m
                continue
        out.append(line)
        i += 1
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return count


def main() -> None:
    for lang, mapping in TRANSLATIONS.items():
        print(f"[{lang}] {apply_lang(lang, mapping)} entrée(s) traitée(s)")


if __name__ == "__main__":
    main()
