# FEAT-090 — Imprimer la carte depuis la fiche usager

**Status:** DONE
**Date:** 2026-09-04

## Contexte

Demande Val (2026-09-04), en testant sur Grand-Saconnex : sur la fiche
(`/fr/members/1/`), un bouton pour imprimer la carte sur l'étiqueteuse
**62 mm** (Brother QL).

Jusqu'ici la carte ruban ne s'imprimait que depuis Avancé → Impression →
Cartes membres, en cochant l'usager dans une liste. Au comptoir, après une
inscription ou un « Remplacer la carte », ce détour est un geste de trop.

## Comportement

Sur la fiche, parmi les actions bibliothécaire, un bouton **« Imprimer la
carte (62 mm) »** ouvre le PDF ruban déjà produit par FEAT-062
(`printing:cards_roll_pdf?ids=<pk>`) dans un nouvel onglet. Même géométrie
(62 × 89 mm), même pilote Brother sur le poste. Pas de nouvel écran, pas
d'envoi serveur → imprimante (FEAT-074).

Visible des bibliothécaires et superadmins, pas du rôle lecture seule. Le
réglage `roll_printer_format.enabled` ne le masque pas : le PDF se génère
quand même, et une instance hébergée imprime depuis le poste local.

## Impact

- `templates/members/member_detail.html` : un lien.
- Aucune nouvelle route.
