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

## Le code Ofelia externe

Certains livres arrivent avec une étiquette qui n'est pas la vôtre : un
fonds prêté par une autre bibliothèque, un don déjà catalogué, un
inventaire d'avant BibliOfelia. Plutôt que de recoller une étiquette
par-dessus, saisissez ce code dans le champ **Code Ofelia externe** de
l'exemplaire (jusqu'à 20 lettres ou chiffres, par exemple `BCF13298781X`).

Ensuite, ce code marche **exactement comme un code Ofelia** : au prêt, au
retour, au récolement, dans la recherche. Vous pouvez le taper ou le
scanner, avec ou sans tirets, en majuscules ou en minuscules.

!!! warning "Un code, un exemplaire"
    Deux exemplaires ne peuvent pas porter le même code externe : sinon,
    BibliOfelia ne saurait pas lequel vous scannez. Si le code est déjà
    pris, le formulaire vous dit sur quel exemplaire il se trouve.

## La provenance

Le champ **Provenance** dit d'où vient cet exemplaire : acheté par la
bibliothèque, donné, prêté par une bibliothèque partenaire… Elle se
choisit dans une liste que vous gérez vous-même (voir
[Provenances](provenances.md)).

C'est la provenance qui permet, le jour venu, de retrouver **tous** les
livres d'un dépôt pour les rendre — même quand un même titre a aussi un
exemplaire qui vous appartient.

## Imprimer les étiquettes

Pour imprimer les codes-barres des exemplaires sur étiquettes physiques,
voir [Étiquettes de livres](../impressions/etiquettes.md).
