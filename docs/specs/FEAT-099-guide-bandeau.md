# FEAT-099 — Bandeau du guide : icône vers l'application, titre vers le guide

**Statut :** DONE
**Date :** 2026-10-26

## Contexte

Dans le guide, l'icône OFELIA en haut à gauche et le texte « Guide BiblOFELIA »
étaient un seul lien, vers l'accueil du guide. Le bibliothécaire qui a ouvert
le guide depuis une bibliothèque (San Juan, Grand-Saconnex, la Box) n'avait
pas de retour direct vers BiblOFELIA.

Le sélecteur de langue, lui, est déjà relatif (BUG-049) sur toutes les
bibliothèques : le même conteneur `bibliofelia-docs` sert San Juan,
Grand-Saconnex et `docs.bibliofelia.org`.

## Comportement

- L'icône OFELIA (bandeau, et la même icône du menu latéral) ouvre
  l'application dans la langue du guide :
  - `/docs/…` → `/fr/`, `/en/`, `/es/` ou `/mg/`
  - `/bibliofelia/docs/…` → `/bibliofelia/fr/` (ou `en`, `es`, `mg`)
  - `docs.bibliofelia.org`, qui n'a pas d'application à côté → `https://bibliofelia.org/`
- Le texte « Guide BiblOFELIA » ouvre l'accueil du guide, dans la langue
  en cours. Le titre de la page, qui défile à la place au scroll, ne change pas.

Le français du guide n'a pas de segment `fr` dans l'adresse. L'application,
si. Sans JavaScript, l'icône garde son lien d'origine (l'accueil du guide).

## Fichiers

- `docs/user-guide/docs/javascripts/header-links.js`
- `docs/user-guide/header_home.py` + `test_header_home.py`
- `docs/user-guide/mkdocs.yml` (`extra_javascript`)
- `docs/user-guide/docs/stylesheets/extra.css`
