# FEAT-061 — Accès au guide utilisateur sur smartphone

**Status:** DONE
**Date:** 2026-08-03

## Context

Le bouton « ? » de la topbar porte `class="icon-btn hide-sm"`, et
`.hide-sm { display: none !important }` sous 600 px. Sur un smartphone en
**portrait**, le guide utilisateur n'était donc atteignable **nulle part** —
alors que c'est précisément le contexte où on en a le plus besoin (bibliothécaire
debout dans les rayons, tablette ou téléphone en main).

Constaté par Val le 2026-08-03, juste après FEAT-057 qui venait de rendre ce même
bouton fonctionnel sur les instances hébergées.

## Behavior

- ≥ 600 px : inchangé — icône « ? » dans la barre du haut.
- < 600 px : une entrée **« Guide utilisateur »** apparaît en tête du menu
  utilisateur (le menu déroulant sous l'avatar), au-dessus de « Mon compte ».
  Elle ouvre le guide dans un nouvel onglet, comme l'icône.

Pas de doublon : l'entrée du menu porte `.only-sm` (masquée ≥ 600 px), l'icône
porte `.hide-sm` (masquée < 600 px) — exactement l'un ou l'autre.

## Technical spec

`templates/base.html`, bloc `.user-menu-drop` : un `<a href="{{ docs_url }}"
target="_blank" rel="noopener" class="only-sm">` avec l'icône `circle-help`.

Aucun CSS nouveau : `.only-sm` existait déjà
(`@media (min-width: 600px) { .only-sm { display: none !important } }`), et
`.user-menu-drop a` fournit déjà la mise en forme (flex, padding, icône grise).

`docs_url` est calculé par le context processor et vaut le bon préfixe selon le
déploiement (`/docs/` sur les instances, `/bibliofelia/docs/` sur la Box) — cf.
FEAT-057.

## Impact on existing code

- Aucune chaîne i18n nouvelle : « Guide utilisateur » est déjà traduit (libellé
  de l'icône de la topbar).
- Aucun impact serveur.
