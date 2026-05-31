# FEAT-047 — Nettoyage UI Paramètres + Avancé

**Status:** DONE (code) — en test Val
**Date:** 2026-05-31

## Context

Retours Val (temp.txt 2026-05-31) : la page `/admin/settings/` et la page
`/advanced/` présentent des entrées redondantes ou inutiles qui alourdissent la
navigation. Cohérent avec la philosophie « petite biblio : simplicité >
exhaustivité » ([[feedback_small_library_simplicity]]).

## Behavior

### `/admin/settings/` — entrées retirées
- **Impressions — Cartes membres** (`printing_cards`) et **Impressions —
  Étiquettes codes Ofelia** (`printing_labels`) : l'impression se fait depuis
  `/advanced/ → Impression`. Les écrans de *format* sont retirés ; les valeurs
  seed font foi (8 cartes/A4, étiquettes 70×42, logo OFELIA). Décision Val :
  retirer, garder les défauts (non modifiable via UI désormais).
- **ZeroTier** (`zerotier`) : géré au niveau de la box (keebee), pas dans
  BibliOfelia.
- **Sources de métadonnées** (`sources`) : la sélection des sources se fait
  désormais uniquement dans `/advanced/ → Enrichissement métadonnées` (cases par
  job). Les sources seed (OpenLibrary + Google Books + BnF + BNE) font foi.
- **Comptes utilisateurs** : lien doublon — déjà dans `/advanced/ →
  Administration`. Retiré de `settings_index.html`.

Sections conservées : Identité, Langues, Durées prêts & réservations,
Sauvegardes, + liens Diagnostic.

### `/advanced/` — catégorie Rapports
On ne garde que le lien **« Tous les rapports »** (`reports:index`). Les liens
Retards / Réservations à retirer / Inactifs / Rapport annuel sont déjà
accessibles depuis cette page d'accueil des rapports.

### `/advanced/` — catégorie Inventaire
L'icône de la ligne **« Emplacements »** était vide : le template appelait
`{% icon "map-pin" %}` mais `static/icons/map-pin.svg` n'existait pas. Ajout
d'une icône d'étagère (Lucide `library`) et bascule de la ligne dessus.

## Technical spec

- `apps/core/admin_views.py` : retirer `printing_cards`, `printing_labels`,
  `zerotier`, `sources` du dict `FORMS` ; nettoyer les imports devenus inutiles
  (`ItemLabelFormatForm`, `MemberCardFormatForm`, `ZeroTierForm`,
  `MetadataSourcesForm` au niveau module — cette dernière reste importée
  localement dans les vues d'enrichissement).
- `templates/core/admin/settings_index.html` : retirer le lien « Comptes
  utilisateurs » + nettoyer les branches per-slug devenues mortes
  (printing_cards/printing_labels/zerotier).
- `templates/core/advanced.html` : section Rapports réduite à « Tous les
  rapports » ; ligne « Emplacements » → `{% icon "library" %}`.
- `static/icons/library.svg` : nouvelle icône Lucide (étagère).

## Impact on existing code

- Les formats d'impression (`card_format`, `item_label_format`) et les sources
  actives ne sont plus éditables via l'UI Paramètres — les valeurs seed
  s'appliquent. Les forms `MemberCardFormatForm` / `ItemLabelFormatForm` /
  `MetadataSourcesForm` / `ZeroTierForm` restent dans `apps/core/forms.py`
  (MetadataSourcesForm toujours utilisée par l'enrichissement).
- `settings_section` redirige déjà vers l'index pour une section inconnue : les
  anciennes URL `/settings/printing_cards/` etc. redirigent proprement.
- Aucun test ne référence les sections retirées (vérifié).
