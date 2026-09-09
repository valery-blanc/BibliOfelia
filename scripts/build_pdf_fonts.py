#!/usr/bin/env python3
"""Fabrique les polices TTF du PDF à partir des woff2 du site. FEAT-093.

Le site sert **Bricolage Grotesque** (titres) et **DM Sans** (texte) en woff2,
que reportlab ne sait pas lire. Ce script produit les `.ttf` équivalents, une
fois pour toutes, et les dépose dans `static/fonts/pdf/`.

Trois opérations, dans cet ordre :

1. **Décompression** du woff2 en TTF (`fontTools.ttLib`).
2. **Fusion des sous-ensembles.** Google Fonts découpe chaque famille par plage
   Unicode (`latin`, `latin-ext`, `vietnamese`). Un titre de livre peut
   contenir n'importe quelle lettre : reportlab ne sait pas retomber sur une
   autre police, un glyphe absent se dessine en carré noir. On fusionne donc
   toutes les plages.
3. **Fixation du poids.** Ce sont des polices variables (400→800) ; reportlab
   n'instancie pas, il prendrait le poids par défaut pour le gras comme pour le
   maigre. On produit donc un fichier par graisse utilisée.

Les `.ttf` obtenus sont **versionnés** : le script n'a pas à tourner au
déploiement, et la Box n'a pas besoin de fontTools.

    python scripts/build_pdf_fonts.py
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
SOURCE = BASE / "static" / "fonts"
TARGET = SOURCE / "pdf"

# Chaque sortie : nom du fichier, sous-ensembles à fusionner, graisse voulue.
BUILDS = [
    (
        "DMSans-Regular.ttf",
        ["dm-sans-1.woff2", "dm-sans-2.woff2"],
        400,
    ),
    (
        "DMSans-Bold.ttf",
        ["dm-sans-1.woff2", "dm-sans-2.woff2"],
        700,
    ),
    (
        "BricolageGrotesque-Bold.ttf",
        [
            "bricolage-grotesque-1.woff2",
            "bricolage-grotesque-2.woff2",
            "bricolage-grotesque-3.woff2",
        ],
        700,
    ),
]

# Ce que les rapports écrivent réellement : accents des quatre langues, chevrons,
# tiret cadratin, espace fine insécable, symboles monétaires. Le script échoue
# si l'un d'eux manque — mieux vaut un échec ici qu'un carré noir dans un PDF
# tendu à un donateur.
REQUIRED = (
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    "àâäçéèêëîïôöùûüÿœÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸŒ"
    "áíóúñ¿¡ÁÍÓÚÑ"
    "«»—–…€$£¥%()[]{}/\\.,;:!?'\"@#&*+-=<>"
    "  ’"
)


def _load(path: Path):
    from fontTools.ttLib import TTFont

    font = TTFont(str(path))
    font.flavor = None  # retire la compression woff2
    return font


# Tables retirées après instanciation.
#
# Les tables de variation (HVAR, STAT, et le `VarStore` niché dans GDEF) sont
# résiduelles une fois la graisse figée, et le fusionneur ne sait pas les
# recoller — il lève « VarStore has no attribute mergeMap ».
#
# GSUB / GPOS / GDEF partent avec : reportlab n'applique ni substitution ni
# crénage OpenType, il lit les seules avances de `hmtx`. Les garder ne change
# rien au rendu et fait échouer la fusion.
VARIATION_TABLES = (
    "fvar", "gvar", "avar", "cvar", "HVAR", "VVAR", "MVAR", "STAT",
    "GDEF", "GSUB", "GPOS",
)


def _instance(font, weight: int):
    """Fige une police variable à la graisse voulue, sinon la renvoie telle quelle."""
    if "fvar" in font:
        from fontTools.varLib import instancer

        font = instancer.instantiateVariableFont(font, {"wght": weight}, inplace=False)
    for tag in VARIATION_TABLES:
        if tag in font:
            del font[tag]
    return font


def _merge(paths: list[Path], weight: int, out: Path) -> None:
    from fontTools.merge import Merger

    statics = []
    for index, path in enumerate(paths):
        font = _instance(_load(path), weight)
        temp = TARGET / f".tmp-{index}-{path.stem}.ttf"
        font.save(str(temp))
        statics.append(temp)

    if len(statics) == 1:
        statics[0].replace(out)
    else:
        merged = Merger().merge([str(p) for p in statics])
        merged.save(str(out))
        for temp in statics:
            temp.unlink(missing_ok=True)

    for leftover in TARGET.glob(".tmp-*"):
        leftover.unlink(missing_ok=True)


# L'espace fine insécable (U+202F) sert de séparateur de milliers dans tous les
# rapports et dans les montants (`apps/finance/money.py`). Google Fonts ne
# l'inclut dans aucun de ces sous-ensembles : sans alias, « 1 234 » sortirait
# « 1□234 » sur chaque page. On la fait pointer sur une espace déjà présente,
# par ordre de préférence — la fine d'abord, l'insécable ensuite.
SPACE_ALIASES = {0x202F: (0x2009, 0x00A0, 0x0020)}


def _alias_missing_spaces(path: Path) -> list[str]:
    """Ajoute au `cmap` les espaces absentes, en réutilisant un glyphe voisin."""
    from fontTools.ttLib import TTFont

    font = TTFont(str(path))
    tables = [t for t in font["cmap"].tables if t.isUnicode()]
    covered = set()
    for table in tables:
        covered.update(table.cmap.keys())

    added = []
    for target, candidates in SPACE_ALIASES.items():
        if target in covered:
            continue
        source = next((c for c in candidates if c in covered), None)
        if source is None:
            continue
        glyph = next(t.cmap[source] for t in tables if source in t.cmap)
        for table in tables:
            table.cmap[target] = glyph
        added.append(f"U+{target:04X}=U+{source:04X}")

    if added:
        font.save(str(path))
    return added


def _coverage(path: Path) -> set[int]:
    from fontTools.ttLib import TTFont

    font = TTFont(str(path))
    covered: set[int] = set()
    for table in font["cmap"].tables:
        covered.update(table.cmap.keys())
    return covered


def main() -> int:
    TARGET.mkdir(parents=True, exist_ok=True)
    failures = []

    for name, subsets, weight in BUILDS:
        sources = [SOURCE / subset for subset in subsets]
        missing = [p for p in sources if not p.exists()]
        if missing:
            print(f"[SKIP] {name} : source absente {[p.name for p in missing]}")
            continue

        out = TARGET / name
        _merge(sources, weight, out)
        aliased = _alias_missing_spaces(out)

        covered = _coverage(out)
        absent = sorted({c for c in REQUIRED if ord(c) not in covered})
        status = "OK" if not absent else "INCOMPLET"
        alias_note = f", alias {' '.join(aliased)}" if aliased else ""
        print(
            f"[{status}] {name} — {len(covered)} glyphes, "
            f"{out.stat().st_size // 1024} Ko{alias_note}"
        )
        if absent:
            failures.append((name, absent))
            print(f"         manquent : {' '.join(repr(c) for c in absent)}")

    if failures:
        print("\nDes caractères manquent : le PDF afficherait des carrés noirs.")
        return 1
    print("\nPolices PDF prêtes dans static/fonts/pdf/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
