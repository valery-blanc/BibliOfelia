# FEAT-097 — Marque visible BiblOFELIA

**Statut :** DONE
**Date :** 2026-10-26

## Contexte

Le logiciel s'affichait « BibliOfelia ». La marque voulue est **BiblOFELIA** :
OFELIA en capitales, comme le logo.

## Comportement

Tous les libellés visibles (barre du haut, pied de page, titres, assistant
d'installation, PDF, guide utilisateur, catalogues de traduction) utilisent
BiblOFELIA.

Ne changent pas : les adresses (`bibliofelia.org`, `/bibliofelia/`), les noms
de fichiers (`bibliofelia.css`), les identifiants techniques, et le nom de
bibliothèque déjà enregistré (`San Juan`, `Grand-Saconnex`, `Canaima`…).

Le nom de bibliothèque proposé à une installation neuve, quand rien n'est
saisi, devient aussi BiblOFELIA. `seed_defaults` ne réécrit pas un nom déjà
enregistré.

## Spec

SPEC §1 et les gabarits `base.html`, `login.html`, `500.html`.
