# BUG-049 — Le sélecteur de langue du guide sort du guide

**Statut :** FIXED
**Symptôme :** depuis une bibliothèque (`https://sanjuan.bibliofelia.org/docs/`,
bouton « ? »), choisir English ou Español ouvre l'application (souvent la page
de connexion), pas le guide traduit. Sur `docs.bibliofelia.org` le même
sélecteur fonctionnait.

## Reproduction

1. Ouvrir `https://sanjuan.bibliofelia.org/docs/`.
2. Cliquer le globe, puis English.
3. Le navigateur va sur `https://sanjuan.bibliofelia.org/en/` (l'application),
   alors que le guide anglais existe à `/docs/en/`.

## Cause

Le même site MkDocs est servi à la racine (`docs.bibliofelia.org`) et sous un
préfixe (`/docs/` sur une instance, `/bibliofelia/docs/` sur la Box). Sur la
page d'accueil, Material émet des liens absolus (`/en/`, `/es/`, `/mg/`). Le
navigateur les résout depuis l'hôte, donc hors du préfixe `/docs/`.

## Correctif

`docs/user-guide/relative_url.py` réécrit ces liens en relatif (`en/`, `../es/`).
Le filtre Jinja `rel_alt` (`hooks.py` + `overrides/partials/alternate.html`)
l'applique à chaque page. Le bouton « ? » ouvre en plus le guide dans la langue
déjà choisie dans l'application (`/docs/en/` quand l'interface est en anglais ;
le français reste à `/docs/`, sans préfixe `fr`).

## Spec

SPEC §6.9.
