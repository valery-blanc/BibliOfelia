# FEAT-068 — Étiquettes de tranche (catégorie abrégée)

**Status:** DONE
**Date:** 2026-08-19

## Contexte

Une fois les abréviations de catégorie saisies (FEAT-067), il faut les coller
sur la tranche des livres pour que le rangement en rayon se voie sans sortir le
livre. Même matériel que les étiquettes de livres : Brother QL-810W, ruban
continu 62 mm (FEAT-062).

## Comportement

Depuis **Impressions → Étiquettes**, un troisième bouton : « Étiquettes de
tranche ». Il produit un PDF au **même format que les étiquettes de livres —
62 × 35 mm, une étiquette par page** (une page = une coupe du ruban).

Contenu : la seule abréviation de la catégorie de la notice, **centrée**
horizontalement et verticalement, découpée en lignes sur les espaces. Pour
« Romans fiction pour adolescents » → `RO FI ADO` :

```
|--------------------------|
|          RO FI           |
|           ADO            |
|--------------------------|
```

La taille de police est calculée pour remplir l'étiquette : gros caractères
lisibles à un mètre du rayon, réduits automatiquement si l'abréviation est
longue. Monochrome, comme les étiquettes de livres.

Un exemplaire dont la notice n'a pas de catégorie, ou dont la catégorie n'a pas
d'abréviation, n'a rien à imprimer : il est ignoré. Si aucun exemplaire
sélectionné n'a d'abréviation, l'écran le dit au lieu de sortir un PDF vide.

## Spec technique

- `apps/printing/services.py` :
  - `spine_label_text(item)` → abréviation ou `""` ;
  - `render_spine_labels_roll_pdf(items)` → PDF 62 × 35 mm, 1 page par
    exemplaire imprimable ;
  - `_draw_roll_spine_label` : découpe en lignes (`_wrap_to_width`) et
    dichotomie sur la taille de police entre `SPINE_MIN_PT` (10) et
    `SPINE_MAX_PT` (48) pour remplir largeur et hauteur utiles.
- Vue `printing.views.spine_labels_roll_pdf`, route
  `printing/spine-labels-roll.pdf`, bouton sur `printing/labels_picker.html`
  (`formtarget="_blank"`, comme les autres sorties ruban depuis FEAT-062).
- Le format (largeur de ruban, longueur d'étiquette) reste celui du réglage
  `roll_printer_format` : une seule géométrie à régler pour toutes les
  impressions ruban.

## Impact sur l'existant

- `apps/printing/services.py`, `views.py`, `urls.py`.
- `templates/printing/labels_picker.html`.

## Implémentation

- `apps/printing/services.py` : `spine_label_text`, `spine_layout`,
  `render_spine_labels_roll_pdf`, `_draw_roll_spine_label`, `_wrap_words`.
- `spine_layout(text, inner_w, inner_h)` cherche la plus grande taille de police
  (de `SPINE_MAX_PT` = 96 à `SPINE_MIN_PT` = 10, par pas de 0,5) qui tienne en
  largeur **et** en hauteur. Extraite du dessin pour être testable directement,
  sans relire le flux PDF.
- Le plafond a été relevé de 48 à 96 pt après vérification visuelle : à 48 pt,
  une cote courte comme « PER » laissait la moitié de l'étiquette vide.
- Vue `spine_labels_roll_pdf` + route `printing/spine-labels-roll.pdf` + bouton
  « Étiquettes de tranche » dans le picker (PDF direct, `_blank`, masqué si le
  ruban est désactivé).
- Vérification visuelle 300 dpi (pypdfium2) : « RO FI » / « ADO » conforme à la
  maquette, « PER » pleine étiquette, « BANDES DESSINEES JEUNESSE » sur
  3 lignes sans débordement.
- Tests : `apps/printing/tests/test_spine_labels.py` (19).
