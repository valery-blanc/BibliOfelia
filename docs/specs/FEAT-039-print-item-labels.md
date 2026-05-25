# FEAT-039 — Étiquettes livres : refonte + paramétrage séparé

**Status:** DONE
**Date:** 2026-05-25

## Context

Val observe que `/admin/settings/labels/` (un seul formulaire mélangeant
paramètres cartes et paramètres étiquettes livres) semble ne plus affecter les
étiquettes de codes Ofelia : titres tronqués sur 1 seule ligne, pas de logo,
identité visuelle pauvre. Il veut :

1. Séparer le paramétrage cartes membres / étiquettes livres en 2 sections
   dans la catégorie « Impressions ».
2. Pouvoir mettre le titre du livre sur 2 lignes (50 caractères par défaut).
3. Ajouter le logo `ofelia-logo.png` sur chaque étiquette.
4. Agrandir l'étiquette si besoin pour que tout tienne lisiblement.

## Behavior

- **Format par défaut** : 80×40 mm (3 colonnes × 7 lignes = 21 étiquettes par
  A4, vs 70×36 mm × 24 actuel). Configurable.
- **Layout** dans la cellule :
  - Logo Ofelia (24 px) en haut-gauche.
  - Titre (2 lignes max, wrap intelligent par mots, 50 caractères par défaut
    cumulés sur les 2 lignes) en haut-droite/centre.
  - Auteurs (1 ligne, 50 caractères max) sous le titre.
  - Code-barres EAN13 centré, hauteur ~45 % de la cellule.
  - Bas : `internal_id` à gauche, code Ofelia (EAN13) au milieu, location à droite.
- **Setting** `item_label_format` (JSON) : `{width_mm, height_mm, title_max_chars, title_lines, show_logo}`.

## Technical spec

- `apps/core/forms.py` : nouveau `ItemLabelFormatForm` (KEY=`item_label_format`).
  Anciennes valeurs `LabelFormatForm` migrées au boot via fallback dans
  `_format_settings`.
- `apps/printing/services.py` :
  - `_format_settings()` lit désormais 2 settings (`card_format`,
    `item_label_format`) avec migration douce depuis l'ancien `label_format`.
  - `_draw_item_label(...)` refondu : logo, titre wrap 2 lignes, layout
    élargi.
  - Helper `_wrap_lines(text, max_chars, max_lines)` pour le wrap titre.
- `apps/core/admin_views.py` : section `printing_labels`.
- `seed_defaults.py` : seed `item_label_format` avec valeurs par défaut.

## Impact on existing code

- `apps/printing/services.py` : `_format_settings`, `_draw_item_label`,
  `render_item_labels_pdf`.
- `apps/core/forms.py` : `LabelFormatForm` retiré, 2 nouveaux forms.
- `apps/core/admin_views.py` : `FORMS` mis à jour.
- `apps/core/management/commands/seed_defaults.py` : nouveau setting seed.
- Tests `apps/printing/tests/test_services.py` : couvrir wrap titre + agrandissement.
- SPEC §6.7 : mise à jour formats + sections settings.
