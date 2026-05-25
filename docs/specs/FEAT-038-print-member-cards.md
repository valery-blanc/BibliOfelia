# FEAT-038 — Refonte impression cartes membres

**Status:** DONE
**Date:** 2026-05-25

## Context

Les cartes membres générées par `apps/printing/services.py:render_member_cards_pdf`
ressemblent à un brouillon : pas d'identité visuelle Ofelia (pas de logo, pas de
fond coloré), nom + code-barres alignés à gauche, photo du membre ignorée alors
que `Member.photo` existe depuis FEAT-037. Val veut une carte reconnaissable au
premier coup d'œil, avec la photo du membre, la langue préférée discrète et le
logo OFELIA en arrière-plan.

## Behavior

Chaque carte (1 cellule de la planche A4) doit respecter cette mise en page :

- **Fond** : couleur unie `rgb(248, 238, 229)` (crème Ofelia) sur toute la cellule.
- **Logo OFELIA** (`static/img/ofelia-grandes-lettres.png`) centré, taille maximale
  possible sans déborder, opacité légère pour rester en filigrane sous le texte.
- **Photo du membre** en haut à gauche (si `member.photo` présent) — vignette
  carrée ~18 mm de côté, marges 4 mm. Si pas de photo : zone laissée vide.
- **Langue préférée** (`member.preferred_language.upper()`) en bas à gauche, petit
  texte (6.5 pt).
- **Côté droit** (colonne verticale, alignement gauche du bloc à droite du logo) :
  - Nom Prénom (12 pt bold)
  - Catégorie (8 pt)
  - « Valide jusqu'au JJ/MM/AAAA » (8 pt)
  - Code-barres EAN13 (haut ~16 mm)
  - Numéro de carte (8 pt)

## Technical spec

- Réutiliser `Member.photo` (`FileField` ajouté FEAT-037). Si présent et
  lisible (Pillow), embarquer la miniature ; sinon ignorer silencieusement.
- Copier `Logo_ofelia_grandes_lettres.png` (racine repo) dans
  `static/img/ofelia-grandes-lettres.png` pour qu'il soit accessible côté serveur
  via `finders.find()` ou chemin direct (`settings.BASE_DIR / "static" / "img"`).
- Nouveau setting `card_format` (JSON) : `{per_a4: 8, background_color: [248,238,229], show_logo: true}` —
  laisse Val tuner via `/admin/settings/printing/cards/`.
- `_draw_member_card(...)` refondu :
  - `pdf.setFillColorRGB(248/255, 238/255, 229/255)` puis `pdf.rect(..., fill=1)`.
  - `pdf.drawImage(logo, ...)` centré, alpha via masque PNG (déjà transparent).
  - Vignette photo : `ImageReader(member.photo.path)` si existe, sinon skip.
- Pas d'opacité réelle (ReportLab ne fait pas d'alpha simple) : on règle la
  visibilité par la transparence du PNG source ou par un `setFillAlpha()` si
  besoin.

## Impact on existing code

- `apps/printing/services.py` : `_draw_member_card`, `render_member_cards_pdf`,
  `_format_settings`.
- `apps/core/forms.py` : split `LabelFormatForm` → `MemberCardFormatForm`
  (FEAT-038) + `ItemLabelFormatForm` (FEAT-039).
- `apps/core/admin_views.py` : `FORMS` dict + nouvelle section `printing_cards`.
- `apps/core/management/commands/seed_defaults.py` : seed `card_format`.
- `static/img/ofelia-grandes-lettres.png` : asset ajouté.
- `templates/core/admin/settings_index.html` : regrouper visuellement les
  paramètres d'impression sous une étiquette « Impressions ».
- Tests : `apps/printing/tests/` adaptés (cartes membre + nouveau setting).
