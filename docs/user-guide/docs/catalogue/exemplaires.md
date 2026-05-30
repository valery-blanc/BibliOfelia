# Gérer les exemplaires

Un **exemplaire** est une copie physique d'un livre. Une notice peut
avoir un seul exemplaire (un livre rare), plusieurs (livre populaire en
plusieurs copies), ou aucun (livre référencé mais pas encore reçu).

## Ajouter un exemplaire

Depuis la fiche d'une notice (page d'un livre), cliquez sur
**+ Ajouter un exemplaire**.

![Formulaire d'ajout d'exemplaire](../assets/screenshots/fr/catalogue/item-create.png)

Choisissez :

- **Localisation** — le rayon ou l'étagère (voir [Localisations](localisations.md))
- **Nombre d'exemplaires** — pour en créer plusieurs d'un coup
- **Notes** — état du livre, provenance, etc.

Cliquez sur **Créer**. Chaque exemplaire reçoit automatiquement :

- Un **code Ofelia** unique (commence par 290 — c'est le code-barres
  qu'on imprime sur l'étiquette du livre)
- Un **code interne** sous la forme `OFL-AAAAMMJJ-NNNN` (visible sur
  la fiche dans BibliOfelia, pratique pour repérer rapidement la date
  de saisie)

Voir le [glossaire](../glossaire.md) pour comprendre les différents
codes en détail.

!!! info "Le code n'est jamais réutilisé"
    Quand vous supprimez un exemplaire, son code Ofelia reste
    "réservé" : aucun nouvel exemplaire ne portera ce même numéro.
    C'est important pour éviter qu'une étiquette imprimée correspondant
    à un livre radié ne devienne par accident valide pour un autre
    livre.

## Voir tous les exemplaires d'une notice

La fiche d'une notice affiche en bas la liste de tous ses exemplaires
avec leur statut : **Disponible**, **En prêt**, **Réservé**,
**Perdu**, **Au rebut**.

## Modifier un exemplaire

Cliquez sur la ligne d'un exemplaire pour ouvrir son formulaire d'édition.
Vous pouvez changer sa localisation, ajouter une note, ou modifier son
statut.

## Mettre un exemplaire au rebut

Si un exemplaire est trop abîmé pour être prêté (mais pas perdu), vous
pouvez le **mettre au rebut** : il reste dans la base mais devient
non-prêtable. Utilisez le bouton **Mettre au rebut** depuis sa fiche.

## Imprimer les étiquettes

Pour imprimer les codes-barres des exemplaires sur étiquettes physiques,
voir [Étiquettes de livres](../impressions/etiquettes.md).
