# FEAT-098 — Page d'accueil bibliofelia.org

**Statut :** DONE
**Date :** 2026-10-26

## Contexte

`bibliofelia.org` et `www.bibliofelia.org` répondaient par une redirection 301
vers `https://ofeliainternational.org/what-we-do/`. Il faut une page à l'adresse
du logiciel, dans la même charte que l'application et que la Box, qui présente
les bibliothèques et pointe vers le projet Ofelia.

## Comportement

Page statique (crème, bordeaux, Bricolage Grotesque, DM Sans, logo OFELIA).
Trois cartes :

| Bibliothèque | Lieu | Adresse |
|---|---|---|
| Canaima | Venezuela, Ofelia Box | `https://canaima.bibliofelia.org` |
| Grand-Saconnex | Suisse | `https://grand-saconnex.bibliofelia.org` |
| San Juan | Venezuela | `https://sanjuan.bibliofelia.org` |

Le projet Ofelia est une grande tuile sous les trois bibliothèques, vers
`https://ofeliainternational.org` (FEAT-101). Le pied de page garde
l'adresse. Le fond de page est la vidéo d'accueil d'OFELIA International.
Les bandeaux et le sélecteur de langue sont ceux de l'application (FEAT-102).

## Technique

- `www/index.html`, `www/Dockerfile`, `www/nginx.conf`
- `deploy/www/docker-compose.yml` — sur Fez et Avignon, dossier
  `~/docker/bibliofelia-www/`, image `bibliofelia-www:latest`, route Traefik
  `Host(bibliofelia.org) || Host(www.bibliofelia.org)`.
- Le fichier `~/docker/traefik/dynamic/bibliofelia.org-redirect.yml` est retiré
  des deux nœuds : il entrait en conflit avec la nouvelle route.
- Les polices et le logo sont copiés dans l'image (pas de CDN).

## Spec

SPEC §2.2.
