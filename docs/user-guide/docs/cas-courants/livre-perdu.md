# Livre perdu ou abîmé

Quand un livre ne revient pas, est endommagé ou doit sortir du
catalogue, il faut le sortir proprement de BibliOfelia.

## Livre perdu pendant un prêt

Quand un membre déclare avoir perdu un livre :

1. Ouvrez la [fiche du membre](../usagers/fiche.md)
2. Trouvez le prêt concerné dans **Prêts en cours**
3. Cliquez sur le bouton **Perdu** à droite de la ligne
4. Confirmez

Conséquences :

- Le prêt passe au statut **Perdu**
- L'exemplaire passe au statut **Perdu**
- L'exemplaire n'apparaît plus comme disponible
- Le membre n'a plus ce prêt dans ses livres en cours

Le membre garde son historique et peut continuer d'emprunter d'autres
livres. C'est à vous de gérer le remplacement ou l'amende selon vos
règles internes (BibliOfelia ne gère pas la facturation).

## Livre abîmé mais récupéré

Si le livre est rendu trop abîmé pour être prêté à nouveau :

1. Enregistrez le **retour** normalement
2. Ouvrez la [fiche de l'exemplaire](../catalogue/exemplaires.md)
3. Cliquez sur **Mettre au rebut**

Le livre reste dans le catalogue (pour mémoire) mais n'est plus
prêtable.

## Sortir définitivement un livre du catalogue

Si la notice n'a plus aucun exemplaire (tous perdus, donnés, jetés),
vous pouvez supprimer la notice elle-même :

1. Ouvrez la fiche de la notice
2. Cliquez sur **Supprimer la notice**
3. Confirmez

Ou utilisez l'[opération en lot](../catalogue/operations-lot.md) pour
en supprimer plusieurs d'un coup.

!!! danger "Le code Ofelia n'est jamais réutilisé"
    Quand vous supprimez un exemplaire, son code Ofelia reste réservé :
    aucun autre livre ne portera ce même code à l'avenir. Cela évite
    qu'une étiquette qui circule encore (poubelle, livre donné) ne
    désigne par erreur un autre livre quand on la scanne.

    Concrètement : si l'étiquette d'un livre supprimé est scannée plus
    tard, BibliOfelia répond "code inconnu" — et pas "voici le livre
    X" qui serait une confusion grave.

## Voir aussi

- [Gérer les exemplaires](../catalogue/exemplaires.md)
- [Opérations en lot](../catalogue/operations-lot.md)
