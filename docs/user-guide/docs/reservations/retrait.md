# Retrait et expiration d'une réservation

Une fois le livre arrivé et le membre prévenu, il faut le mettre de
côté en attendant qu'il vienne le chercher. Si personne ne vient, la
réservation expire et le livre est libéré.

## Mettre le livre de côté

Au moment du retour, si le livre déclenche une réservation, BibliOfelia
vous l'indique avec un message :

> **À mettre de côté pour [Nom du membre]**

Rangez physiquement le livre dans la zone de réservations (étagère
dédiée derrière le bureau d'accueil, par exemple), pas en rayon.

## Quand le membre vient chercher

Le membre arrive avec sa carte. Faites un prêt normal :

1. Ouvrez la page [**Prêt**](/bibliofelia/fr/loans/lend/){ target="_blank" }
2. Scannez la carte
3. Scannez le livre

La réservation se transforme automatiquement en prêt. Sa date
d'expiration s'efface, son statut passe à **Honorée** dans
l'historique.

## Expiration : le membre ne vient pas

Si le membre prévenu ne vient pas chercher son livre dans un délai
défini (par défaut 7 jours), la réservation expire automatiquement.

Concrètement :

- La réservation passe au statut **Expirée**
- Le livre redevient disponible (ou passe au membre suivant dans la
  file d'attente)
- Le bouton **Mettre de côté** disparaît : remettez le livre en rayon

!!! info "Le délai est configurable"
    L'administrateur peut ajuster la durée par défaut dans les
    paramètres (`pickup_hold_days`). Par défaut, c'est 7 jours.

## Voir les réservations à risque d'expirer

Depuis **Rapports → Réservations à retirer**, vous voyez la liste des
réservations prêtes avec leur date d'expiration. Les plus proches
apparaissent en haut — c'est votre liste de relances prioritaires.

## Cas particuliers

### Le membre veut prolonger l'attente

Si le membre vous dit qu'il vient la semaine prochaine, vous pouvez
ouvrir la réservation et modifier la date d'expiration manuellement
pour éviter qu'elle expire trop tôt.

### Le membre renonce

S'il ne veut plus du livre, ouvrez la réservation et cliquez sur
**Annuler**. Le livre passe au membre suivant ou redevient disponible.
