# BUG-044 — Le code interne OFL-… n'est pas résolu au prêt ni à la recherche

**Status:** FIXED
**Date:** 2026-09-05

## Symptôme

Un bibliothécaire recopie le code interne `OFL-20260525-0014` affiché
à l'écran et le tape dans la recherche ou au prêt : rien. La fenêtre
« Mettre à jour des exemplaires » (Excel) l'accepte.

## Cause

`find_item` ne connaissait que l'EAN-13 Ofelia et le code externe.
L'Excel avait sa propre résolution (`internal_id__iexact`), en
violation de « un code résolu quelque part doit l'être partout ».

## Correctif

`apps/catalog/lookup.py::find_item` essaie ensuite le code interne,
avec ou sans tirets (`OFL-YYYYMMDD-NNNN` / `OFLYYYYMMDDNNNN`).
`_find_item_by_ofelia_code` (Excel) s'aligne sur `find_item`.

## Section de spec

`SPEC_BIBLIOFELIA.md` §5.2 ordre de `find_item`.
