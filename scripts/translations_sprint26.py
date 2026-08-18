#!/usr/bin/env python3
"""Traductions Sprint 26 — FR → EN/ES/MG.

- FEAT-059/060 : sources de métadonnées (Swisscovery, K10plus) + libellés et
  aide du formulaire « Sources de métadonnées » / page Enrichissement.
- FEAT-058 : consultation d'un lot de catalogage validé.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint26.py
"""
from __future__ import annotations

from pathlib import Path

_GB_HELP = (
    "Facultative mais recommandée : sans clé, Google Books partage un quota "
    "par adresse IP et répond « quota atteint ». Gratuite via Google Cloud Console."
)
_ENRICH_SUB = (
    "Complète le catalogue depuis OpenLibrary, Google Books et les "
    "bibliothèques nationales."
)

_IMPORT_ERR = (
    "Ces lignes ont un ISBN manquant ou invalide : l'import se fait par ISBN, "
    "elles n'ont donc pas été ajoutées au catalogue. Le détail est listé plus "
    "bas — cataloguez ces livres à la main."
)
_MISSING = "Ligne sans ISBN : non importée, à cataloguer à la main."
_INVALID = "ISBN invalide (ni 10 ni 13 chiffres) : ligne non importée."

TRANSLATIONS = {
    "en": {
        "BnF (livres FR)": "BnF (French books)",
        "Swisscovery (livres CH)": "Swisscovery (Swiss books)",
        "K10plus (livres DE)": "K10plus (German books)",
        _GB_HELP: (
            "Optional but recommended: without a key, Google Books shares a "
            "per-IP quota and answers « quota reached ». Free via Google Cloud Console."
        ),
        _ENRICH_SUB: (
            "Fills in the catalogue from OpenLibrary, Google Books and national libraries."
        ),
        "Activer ou désactiver des sources": "Enable or disable sources",
        "Voir le lot": "View batch",
        _IMPORT_ERR: (
            "These rows have a missing or invalid ISBN: the import works by ISBN, "
            "so they were not added to the catalogue. Details are listed below — "
            "catalogue those books by hand."
        ),
        _MISSING: "Row without an ISBN: not imported, catalogue it by hand.",
        _INVALID: "Invalid ISBN (neither 10 nor 13 digits): row not imported.",
        "Voir la notice": "View record",
        "Ce lot ne contient aucun livre.": "This batch contains no books.",
    },
    "es": {
        "BnF (livres FR)": "BnF (libros FR)",
        "Swisscovery (livres CH)": "Swisscovery (libros CH)",
        "K10plus (livres DE)": "K10plus (libros DE)",
        _GB_HELP: (
            "Opcional pero recomendada: sin clave, Google Books comparte una "
            "cuota por dirección IP y responde « cuota alcanzada ». Gratuita en "
            "Google Cloud Console."
        ),
        _ENRICH_SUB: (
            "Completa el catálogo desde OpenLibrary, Google Books y las "
            "bibliotecas nacionales."
        ),
        "Activer ou désactiver des sources": "Activar o desactivar fuentes",
        "Voir le lot": "Ver el lote",
        _IMPORT_ERR: (
            "Estas líneas tienen un ISBN ausente o inválido: la importación se hace "
            "por ISBN, así que no se añadieron al catálogo. El detalle está más "
            "abajo — catalogue esos libros a mano."
        ),
        _MISSING: "Línea sin ISBN: no importada, catalóguela a mano.",
        _INVALID: "ISBN inválido (ni 10 ni 13 cifras): línea no importada.",
        "Voir la notice": "Ver el registro",
        "Ce lot ne contient aucun livre.": "Este lote no contiene ningún libro.",
    },
    "mg": {
        "BnF (livres FR)": "BnF (boky FR)",
        "Swisscovery (livres CH)": "Swisscovery (boky CH)",
        "K10plus (livres DE)": "K10plus (boky DE)",
        _GB_HELP: (
            "Tsy voatery fa soso-kevitra : raha tsy misy fanalahidy, mizara "
            "quota araka ny adiresy IP ny Google Books ka mamaly « feno ny quota ». "
            "Maimaim-poana ao amin'ny Google Cloud Console."
        ),
        _ENRICH_SUB: (
            "Mameno ny katalôgy avy amin'ny OpenLibrary, Google Books sy ireo "
            "tranomboky nasionaly."
        ),
        "Activer ou désactiver des sources": "Alefa na atsahatra ny loharano",
        "Voir le lot": "Hijery ny andiany",
        _IMPORT_ERR: (
            "Tsy misy ISBN na diso ny ISBN amin'ireo andalana ireo: amin'ny alalan'ny "
            "ISBN no anaovana ny fampidirana, ka tsy nampiana tao amin'ny katalôgy izy "
            "ireo. Hita etsy ambany ny antsipiriany — raketo an-tanana ireo boky ireo."
        ),
        _MISSING: "Andalana tsy misy ISBN: tsy nampidirina, raketo an-tanana.",
        _INVALID: "ISBN diso (tsy 10 na 13 isa): tsy nampidirina ilay andalana.",
        "Voir la notice": "Hijery ny rakitra",
        "Ce lot ne contient aucun livre.": "Tsy misy boky ao amin'ity andiany ity.",
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
