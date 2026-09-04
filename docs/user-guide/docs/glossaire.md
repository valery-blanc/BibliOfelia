# Glossaire

Petit lexique des termes utilisés dans BibliOfelia.

## Les différents codes : à quoi servent-ils ?

BibliOfelia utilise plusieurs sortes de codes pour identifier les livres
et les membres. C'est important de bien les distinguer car ils ne servent
pas à la même chose.

### Code Ofelia (sur les étiquettes et les cartes)

C'est le **code-barres** qu'on scanne avec la douchette ou OfeliaScan.
Il commence par **290** pour un livre, ou **291** pour une carte de
membre. Il a 13 chiffres au total.

Exemples :

- `2900000000017` → étiquette d'un livre
- `2910000000444` → carte d'un membre

C'est ce code que BibliOfelia génère automatiquement quand vous créez
un nouvel exemplaire ou un nouveau membre. C'est lui qu'on imprime
sur les étiquettes et sur les cartes physiques. C'est lui qu'on scanne
pour les prêts, les retours, le récolement.

Une fois imprimé, ce code ne change jamais. Si une étiquette ou une
carte est perdue, **on n'imprime pas la même** : on en crée une
nouvelle avec un autre code (voir
[Livre perdu](faq.md#livre-perdu) et
[Carte perdue](faq.md#carte-perdue)).

### Code interne (sur la fiche du livre, pas sur l'étiquette)

À côté du code Ofelia, chaque livre a aussi un **code interne** plus
lisible pour le bibliothécaire. Il a la forme **OFL-AAAAMMJJ-NNNN** :

- `OFL-20260525-0014` → 14e livre saisi le 25 mai 2026

Ce code apparaît dans BibliOfelia sur la fiche de l'exemplaire. Il
permet de repérer rapidement quand un livre a été enregistré. **On
ne le scanne pas, on ne l'imprime pas** sur l'étiquette : c'est juste
pour faciliter la gestion à l'écran.

### ISBN-13 (sur la couverture du livre, imprimé par l'éditeur)

C'est le code à 13 chiffres que l'**éditeur** imprime au dos du livre,
généralement à côté d'un code-barres standard. Il identifie le titre
universellement.

Exemple : `9782070612758` → identifie *Le Petit Prince* chez Gallimard.

Quand vous créez une nouvelle notice, BibliOfelia interroge la base
OpenLibrary à partir de l'ISBN-13 pour pré-remplir le titre, l'auteur
et l'éditeur. L'ISBN-13 sert donc surtout au **catalogage**, pas au
prêt quotidien.

Pour le prêt, c'est le code Ofelia du livre qu'on scanne, **pas
l'ISBN** (un livre peut avoir 3 exemplaires : ils ont le même ISBN,
mais chacun son code Ofelia).

### ISBN-10 (ancien format)

Avant 2007, les livres avaient un code éditeur à 10 chiffres : c'est
l'ISBN-10. Vous pouvez le rencontrer sur les livres anciens.
BibliOfelia accepte les deux : si vous tapez un ISBN-10, il est
automatiquement converti en ISBN-13.

### ISSN (revues et magazines)

L'**ISSN** est l'équivalent de l'ISBN pour les **revues et magazines**.
Sur le code-barres au dos d'un magazine, il commence par **977**.

À la différence de l'ISBN, l'ISSN identifie **le titre de la revue**, pas
un numéro précis : tous les numéros d'un même magazine partagent le même
ISSN. BibliOfelia crée donc **une seule notice** par revue, à laquelle
chaque numéro ajoute un exemplaire. On catalogue une revue comme un livre,
en scannant simplement son code-barres 977.

### Numéro de carte / numéro de membre

C'est le code Ofelia d'une carte de membre (préfixe 291). On
l'appelle aussi "numéro de carte" ou "numéro de membre" — c'est la
même chose.

## Les autres termes

### BibliOfelia

Le logiciel de gestion de bibliothèque, installé sur l'**Ofelia Box**.
On y accède depuis n'importe quel ordinateur ou tablette de la
bibliothèque via un navigateur web.

### Consultation sur place

Un livre lu dans la bibliothèque sans être emprunté (BD feuilletée,
dictionnaire consulté pour un devoir). Peut être enregistrée pour les
statistiques. Voir [Consultation sur place](prets-retours/consultation.md).

### Douchette

Lecteur de codes-barres branché par câble USB sur l'ordinateur. Il
se comporte comme un clavier : on scanne, le code apparaît dans le
champ de saisie. C'est l'outil le plus rapide.

### Exemplaire

Une copie physique d'un livre. Une notice peut avoir plusieurs
exemplaires (par exemple, 3 copies du *Petit Prince* en rayon). Chaque
exemplaire a son propre code Ofelia. Voir
[Gérer les exemplaires](catalogue/exemplaires.md).

### Localisation

Le rayon ou l'étagère où on range un livre. Identifié par un code
court (`A1`, `JEUN`, `BD`…). Voir
[Localisations](catalogue/localisations.md).

### Membre

Un lecteur inscrit à la bibliothèque. Possède une carte avec un
numéro unique. Aussi appelé **usager** ou **lecteur**.

### Notice

La fiche descriptive d'un livre (titre, auteur, ISBN…). Indépendante
des exemplaires physiques : une notice peut exister sans exemplaire
(livre référencé mais pas encore reçu) ou avec plusieurs exemplaires
(livre populaire). Voir [Ajouter un livre](catalogue/ajouter-livre.md).

### Ofelia Box

Le petit boîtier (un mini-ordinateur Raspberry Pi) qui héberge
BibliOfelia. Branché sur le réseau de la bibliothèque, il diffuse
l'application à tous les postes connectés. Pas besoin d'internet
pour qu'il fonctionne.

### OfeliaScan

L'application Android compagnon de BibliOfelia. Elle transforme un
téléphone en scanner pour les codes-barres. Voir
[Activer OfeliaScan](ofeliascan/activer.md).

### Amende

Montant facturé **à la main** depuis la fiche d'un usager (motif +
montant). BibliOfelia ne calcule aucune amende de retard tout seul.
Voir [Caisse et factures](caisse/caisse.md).

### Animation

Séance avec du public (heure du conte, atelier). On y compte les
membres présents (scan ou 4 derniers chiffres de la carte) et, à
part, les non-membres. Voir
[Activités et animations](caisse/activites.md).

### Bouclement

Fin de service du jour : activités, caisse, envois, sauvegarde, et
sur la Box seulement l'extinction. Voir
[Bouclement de la journée](caisse/bouclement.md).

### Caisse

Registre des entrées et sorties d'espèces, distinct des virements.
Solde du tiroir, factures, file d'emails. Voir
[Caisse et factures](caisse/caisse.md).

### Cotisation

Montant annuel porté par la **catégorie d'usager**, facturé
automatiquement à l'inscription et à chaque renouvellement. 0 =
gratuit. Voir [Tarifs et Catégories d'usagers](caisse/tarifs.md).

### Prêt

L'emprunt d'un livre par un membre, avec une date de retour. Voir
[Faire un prêt](prets-retours/faire-pret.md).

### Récolement

L'inventaire d'un rayon : on parcourt les étagères et on scanne
chaque livre pour vérifier qu'il est à sa place. Voir
[Récolement](inventaire/recolement.md).

### Réservation

Une demande d'emprunt pour un livre actuellement non disponible. Le
membre est servi en priorité quand le livre revient. Voir
[Réservations](reservations/creer.md).
