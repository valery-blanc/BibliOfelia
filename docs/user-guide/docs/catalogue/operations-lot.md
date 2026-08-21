# Opérations en lot

Pour gagner du temps quand vous avez plusieurs notices à modifier de la
même façon, BibliOfelia propose des **opérations en lot** (ou "actions
de masse") depuis la liste du catalogue.

## Sélectionner plusieurs notices

Deux cases, au-dessus de la liste, cochent tout d'un coup :

- **Sélectionner les N résultats visibles** — les lignes de la page affichée.
- **Sélectionner les N résultats de la recherche** — **toutes les pages**. Cette
  case n'apparaît que s'il y a plus d'une page.

Le nombre annoncé est le nombre réel : vous savez donc toujours combien de
livres vous vous apprêtez à modifier ou à supprimer.

!!! warning "Ne confondez pas les deux"
    Cocher « résultats visibles » ne prend que la page courante — 25 lignes.
    Sur un fonds de plusieurs centaines de livres, c'est la deuxième case qu'il
    vous faut. Cocher l'une décoche l'autre, et cocher une ligne à la main
    annule la sélection étendue.

Avant une suppression, la page de confirmation rappelle le total. Au-delà de
100 lignes, elle n'en affiche que les 100 premières et indique combien
d'autres suivront — mais **toutes** seront bien supprimées.

Depuis la page [**Catalogue**](/bibliofelia/fr/catalog/){ target="_blank" },
chaque ligne de notice a une case à cocher à gauche. Cochez les notices que vous voulez traiter.

Une barre d'actions apparaît en haut, avec un compteur ("3 notices
sélectionnées") et les opérations disponibles.

## Opérations disponibles

### Affecter en masse depuis le catalogue

Dès que vous cochez une ligne, une barre apparaît en haut de la liste avec des
menus déroulants et un bouton **Affecter**.

**En mode notices** (l'affichage par défaut), deux menus :

- **Catégorie** — appliquée aux notices cochées
- **Emplacement** — appliqué à **tous les exemplaires** de ces notices

**En mode exemplaires** (case « Chercher les exemplaires » cochée), un menu :

- **Provenance** — appliquée aux exemplaires cochés

Chaque information se règle là où elle vit : la catégorie appartient au livre,
la provenance à l'exemplaire.

!!! tip "« Ne pas modifier » est la valeur de départ"
    Un menu laissé sur **Ne pas modifier** ne touche à rien. Vous pouvez donc
    changer la catégorie sans risquer de vider l'emplacement au passage.
    Pour retirer une affectation, choisissez **— (vider)**.

Après l'affectation, vous revenez sur le catalogue **avec vos filtres
toujours actifs** : pratique pour enchaîner plusieurs lots.

### Supprimer les notices sélectionnées

Pour faire le ménage (livres qui ne sont plus dans la bibliothèque,
doublons), cochez les notices et cliquez sur **Supprimer les notices
sélectionnées**.

!!! danger "Suppression définitive"
    Les notices ET tous leurs exemplaires sont supprimés. Les prêts en
    cours sont marqués **Perdu**, les réservations actives sont
    annulées. **Ces suppressions sont définitives.**

    Lisez attentivement le message de confirmation avant de valider.
    Les codes des exemplaires supprimés ne pourront pas être réutilisés
    (voir [Cas courants : livre perdu](../faq.md#livre-perdu)).

## Astuce : tout sélectionner sur la page

La case à cocher en haut de la colonne sélectionne (ou désélectionne)
toutes les notices visibles sur la page. Si vous avez activé un filtre
(par exemple "catégorie = Désuet"), vous ne sélectionnez que les
notices filtrées.

!!! tip "Bien filtrer avant de tout cocher"
    Pour une opération en lot, le plus sûr est de **filtrer d'abord**
    pour ne voir que les notices à traiter, puis de **tout cocher**.
    Vous évitez les erreurs d'inattention.
