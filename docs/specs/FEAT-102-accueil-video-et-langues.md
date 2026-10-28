# FEAT-102 — Vidéo d'accueil et langues

**Statut :** DONE
**Date :** 2026-10-28

## Contexte

Sur `bibliofelia.org`, le fond montrait le garçon et la mappemonde comme
une image fixe. La page n'avait pas de sélecteur de langue, et ses
bandeaux ne reprenaient pas ceux de l'application (Canaima, par exemple).

## Cause de l'image fixe

La page cachait la vidéo dès que le système demande moins d'animation
(`prefers-reduced-motion`). Sous Windows, couper les animations active
ce réglage : le visiteur ne voyait plus que l'affiche
`ofelia-home-poster.jpg`.

## Comportement

- La vidéo démarre toute seule, en muet, en boucle. L'affiche ne sert
  qu'avant la première image.
- Le bandeau du haut est blanc : logo OFELIA, **BiblOFELIA**, sous-titre,
  puis la pilule de langue FR / EN / ES / MG, comme sur l'écran de
  connexion.
- Le pied est le bandeau bordeaux : **BiblOFELIA — Projet Ofelia** et
  `ofeliainternational.org`.
- Changer la langue traduit le titre, le texte, les lieux (« Suisse »,
  « Switzerland », « Suiza », « Soisa ») et les boutons. Le choix est
  retenu sur l'appareil. `?lang=en` (ou `es`, `mg`) ouvre directement
  cette langue. Sans paramètre, la page est en français.
- Les trois bibliothèques restent devant la tuile OFELIA International.

## Fichiers

- `www/index.html`
