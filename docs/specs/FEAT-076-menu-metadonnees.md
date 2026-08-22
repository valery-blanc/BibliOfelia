# FEAT-076 — Chapitre « Méta-données » dans le menu Avancé

- **Statut** : DONE
- **Sprint** : 29
- **Demandé par** : Val (2026-08-22)
- **Sections spec impactées** : §11.1

## Contexte

Le chapitre **Inventaire** du menu Avancé avait accumulé neuf entrées de trois
natures différentes : des sessions de travail (récolement, catalogage par scan /
douchette / Excel) et des **listes de référence** (emplacements, langues,
catégories, provenances, enrichissement des métadonnées). Ces dernières ne
relèvent pas de l'inventaire : elles se règlent une fois et alimentent ensuite
les menus déroulants du catalogue.

## Comportement

Un quatrième chapitre, **Méta-données**, entre Inventaire et Administration,
visible pour les bibliothécaires comme les autres chapitres non-admin. Il
regroupe, dans cet ordre :

1. **Emplacements** — zones de rangement
2. **Langues** — langues des documents et langues parlées des usagers
3. **Catégories** — classement et cote imprimée sur la tranche
4. **Provenances** — d'où viennent les exemplaires
5. **Enrichissement métadonnées** — complétion depuis OpenLibrary, Google
   Books, BnF, BNE

Le chapitre Inventaire conserve les quatre entrées qui sont bien des sessions de
travail : sessions d'inventaire, catalogage par scan, par douchette, Excel.

Codage couleur : le chapitre reprend le bleu `--sky` du système OFELIA (les
listes de référence), là où l'inventaire garde son olive et l'impression son
orange. Icône `database`.

## Spec technique

`templates/core/advanced.html` uniquement — aucune vue, aucune route, aucun
modèle ne change. Les cinq entrées sont déplacées telles quelles, seule la
variable de couleur des pastilles passe de `--olive-light` / `#6B5A0E` à
`--sky-light` / `#1a4a80`.

## Impact sur l'existant

Aucun lien profond ne casse : les URL des cinq écrans sont inchangées, seule
leur place dans le menu bouge.
