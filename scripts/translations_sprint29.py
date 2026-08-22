#!/usr/bin/env python3
"""Traductions Sprint 29 — FR → EN/ES/MG.

Couvre FEAT-074 (suppression du chemin CUPS), FEAT-075 (écrans d'étiquettes
séparés), FEAT-076 (chapitre Méta-données) et FEAT-077 (horloge de la Box).

Le gros du sprint est une chaîne qui change : la description de l'écran « Étiquettes codes Ofelia » dans le menu
Avancé, qui annonçait un envoi direct à une imprimante CUPS et parle désormais
du ruban 62 mm. Le vocabulaire suit celui déjà retenu pour le bouton
« Ruban %(w)s mm (Brother QL) » : *tape* / *cinta* / *riban*.

Les chaînes supprimées (« Imprimer (CUPS) », « Serveur CUPS », étape
« Imprimante » du wizard…) sortent d'elles-mêmes des `.po` grâce au
`--no-obsolete` de `makemessages`.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint29.py
"""
from __future__ import annotations

from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

_LABELS_HELP = (
    "Génère les étiquettes (code Ofelia + titre + emplacement) à coller sur les "
    "ouvrages. PDF planche A4 ou ruban 62 mm pour l'étiqueteuse Brother QL."
)

# FEAT-075 / FEAT-076 — écrans d'étiquettes séparés et chapitre « Méta-données ».
# Le vocabulaire de la cote suit celui déjà retenu pour « Cote imprimée sur la
# tranche » (FEAT-067) : *shelf mark* / *signatura* / *kaody*.
_SPINE_MENU = (
    "Imprime la cote de la catégorie (« RO FI ADO ») à coller sur la tranche, pour "
    "ranger et retrouver un livre sans le sortir du rayon."
)
_SPINE_SUB = "Sélectionnez les exemplaires dont la cote doit être collée sur la tranche"
_SPINE_NO_ROLL = (
    "L'impression ruban est désactivée : seule la planche A4 est disponible ici. "
    "Activez-la dans Paramètres → Impressions — Ruban continu pour imprimer les "
    "cotes à l'étiqueteuse."
)
_META_INTRO = (
    "Les listes de référence du catalogue : elles alimentent les menus déroulants "
    "des notices et des exemplaires."
)
_TZ_HELP = (
    "Utilisé pour l'heure affichée sur l'accueil et pour toutes les dates. "
    "Vide = fuseau du système."
)

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        _LABELS_HELP: (
            "Generates the labels (Ofelia code + title + location) to stick on the "
            "books. A4 PDF sheet or 62 mm tape for the Brother QL label printer."
        ),
        _SPINE_MENU: (
            "Prints the category shelf mark (“RO FI ADO”) to stick on the "
            "spine, so a book can be shelved and found again without pulling it out."
        ),
        _SPINE_SUB: "Select the copies whose shelf mark goes on the spine",
        _SPINE_NO_ROLL: (
            "Tape printing is off: only the A4 sheet is available here. Turn it on "
            "under Settings → Printing — Continuous tape to print shelf "
            "marks on the label printer."
        ),
        _META_INTRO: (
            "The catalogue's reference lists: they fill the drop-down menus of "
            "records and copies."
        ),
        "PDF A4": "A4 PDF",
        "Date et heure de la Box": "Box date and time",
        "Fuseau horaire": "Time zone",
        _TZ_HELP: (
            "Used for the time shown on the home page and for every date. "
            "Blank = system time zone."
        ),
        "Fuseau du système : %(tz)s": "System time zone: %(tz)s",
        "Fuseau horaire inconnu : %(tz)s": "Unknown time zone: %(tz)s",
        "Cote imprimée": "Printed shelf mark",
        "Méta-données": "Metadata",
        "aucune": "none",
    },
    "es": {
        _LABELS_HELP: (
            "Genera las etiquetas (código Ofelia + título + ubicación) para pegar en "
            "los libros. Hoja PDF A4 o cinta de 62 mm para la etiquetadora Brother QL."
        ),
        _SPINE_MENU: (
            "Imprime la signatura de la categoría («RO FI ADO») para pegar en el lomo, "
            "y así ordenar y encontrar un libro sin sacarlo del estante."
        ),
        _SPINE_SUB: "Seleccione los ejemplares cuya signatura debe pegarse en el lomo",
        _SPINE_NO_ROLL: (
            "La impresión en cinta está desactivada: aquí solo está disponible la "
            "hoja A4. Actívela en Ajustes → Impresiones — Cinta continua para "
            "imprimir las signaturas en la etiquetadora."
        ),
        _META_INTRO: (
            "Las listas de referencia del catálogo: alimentan los menús desplegables "
            "de los registros y los ejemplares."
        ),
        "PDF A4": "PDF A4",
        "Cote imprimée": "Signatura impresa",
        "Date et heure de la Box": "Fecha y hora de la Box",
        "Fuseau horaire": "Zona horaria",
        _TZ_HELP: (
            "Se usa para la hora mostrada en la pantalla de inicio y para todas las "
            "fechas. Vacío = zona horaria del sistema."
        ),
        "Fuseau du système : %(tz)s": "Zona horaria del sistema: %(tz)s",
        "Fuseau horaire inconnu : %(tz)s": "Zona horaria desconocida: %(tz)s",
        "Méta-données": "Metadatos",
        "aucune": "ninguna",
    },
    "mg": {
        _LABELS_HELP: (
            "Mamorona ny marika (kaody Ofelia + lohateny + toerana) hapetaka amin'ny "
            "boky. Taratasy PDF A4 na riban 62 mm ho an'ny mpanonta marika Brother QL."
        ),
        _SPINE_MENU: (
            "Manonta ny kaodin'ny sokajy (« RO FI ADO ») hapetaka amin'ny lamosina, "
            "mba handaminana sy hahitana boky nefa tsy misintona azy eo amin'ny "
            "talantalana."
        ),
        _SPINE_SUB: "Fidio ireo boky tokony hapetahana kaody eo amin'ny lamosina",
        _SPINE_NO_ROLL: (
            "Mihidy ny fanontana amin'ny riban : ny taratasy A4 ihany no misy eto. "
            "Sokafy ao amin'ny Kirakira → Fanontana — Riban mitohy izy raha te "
            "hanonta ny kaody amin'ny mpanonta marika."
        ),
        _META_INTRO: (
            "Ny lisitra fanondro amin'ny katalaogy : izy ireo no mameno ny menio "
            "midina eo amin'ny rakitra sy ny boky."
        ),
        "PDF A4": "PDF A4",
        "Cote imprimée": "Kaody atao pirinty",
        "Date et heure de la Box": "Daty sy ora ny Box",
        "Fuseau horaire": "Faritra ora",
        _TZ_HELP: (
            "Ampiasaina ho an'ny ora aseho eo amin'ny pejy fandraisana sy ho an'ny "
            "daty rehetra. Foana = faritra ora ny rafitra."
        ),
        "Fuseau du système : %(tz)s": "Faritra ora ny rafitra: %(tz)s",
        "Fuseau horaire inconnu : %(tz)s": "Faritra ora tsy fantatra : %(tz)s",
        "Méta-données": "Metadata",
        "aucune": "tsy misy",
    },
}


def _unescape(value: str) -> str:
    return (
        value.replace('\\"', '"')
        .replace("\n", "\n")
        .replace("\t", "\t")
        .replace("\\\\", "\\")
    )


def _escape(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\n")
        .replace("\t", "\t")
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


def apply_lang(lang: str) -> int:
    """Applique les traductions du sprint à un `.po`. Renvoie le nombre de chaînes."""
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0
    singles = TRANSLATIONS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []  # commentaires en attente du msgid courant
    count = 0
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

        if j < len(lines) and lines[j].startswith("msgstr ") and msgid in singles:
            _v, k = _read_value(lines, j, "msgstr ")
            out.extend(_clean_comments(pending))
            out.extend(header)
            out.append(f'msgstr "{_escape(singles[msgid])}"')
            count += 1
            pending = []
            i = k
            continue

        out.extend(pending)
        pending = []
        out.extend(header)
        i = j

    out.extend(pending)
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return count


def main() -> None:
    for lang in ("en", "es", "mg"):
        print(f"[{lang}] {apply_lang(lang)} chaîne(s)")


if __name__ == "__main__":
    main()
