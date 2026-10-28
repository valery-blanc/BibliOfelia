# FEAT-101 — Tuile OFELIA International et fond animé

**Statut :** DONE
**Date :** 2026-10-26

## Contexte

Sur `bibliofelia.org`, le projet Ofelia n'était qu'un petit lien dans
l'en-tête (« Le projet Ofelia »). La page doit montrer OFELIA International
comme une grande tuile, et reprendre le fond animé du site
ofeliainternational.org : le garçon et la mappemonde qui tourne.

## Comportement

- Le lien d'en-tête disparaît.
- Sous les trois bibliothèques, une tuile pleine largeur mène à
  `https://ofeliainternational.org`.
- Le fond de la page est la vidéo d'accueil d'OFELIA International
  (`www/media/ofelia-home.mp4`, 1280×720, sans piste son, en boucle).
  Elle est servie par la page elle-même. Une image fixe
  (`ofelia-home-poster.jpg`) s'affiche le temps que la lecture démarre.
  FEAT-102 : la vidéo n'est plus remplacée par cette image quand le
  système demande moins d'animation — ce réglage laissait la page fixe.
- Le pied de page garde l'adresse `ofeliainternational.org`.

## Fichiers

- `www/index.html`
- `www/media/ofelia-home.mp4`
- `www/media/ofelia-home-poster.jpg`
- `www/Dockerfile`, `www/nginx.conf`
