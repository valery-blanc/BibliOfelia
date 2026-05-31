# Récolement (inventaire des rayons)

Le **récolement** consiste à passer dans les rayons et vérifier que
chaque livre est à sa place. C'est l'opération la plus puissante du
système : vous parcourez les étagères en scannant avec la **caméra**, et
BibliOfelia se met à jour automatiquement.

Le récolement se fait désormais **directement depuis le site**, avec la
caméra de votre téléphone ou de votre tablette — aucune application à
installer. (OfeliaScan reste possible pour le récolement de masse, voir
en bas de page.)

## Préparer le récolement

Avant de commencer :

1. Choisissez le **rayon** à récoler (un seul à la fois pour ne pas se
   perdre).
2. Munissez-vous d'un appareil avec caméra (téléphone, tablette).
3. Ouvrez la page **Avancé → Inventaire** sur cet appareil.

!!! warning "Connexion sécurisée requise pour la caméra"
    La caméra ne fonctionne que sur une connexion **sécurisée (https://)**.
    Voir [Scanner avec la caméra](../premiers-pas/scanner-camera.md) si la
    caméra refuse de s'ouvrir.

## Démarrer une session de récolement

1. Cliquez sur **Nouvelle session de récolement**.
2. Choisissez la **portée** : un **emplacement** précis (ex. « Rayon A1 »)
   ou **tout le fonds**. Si vous choisissez un emplacement, il devient
   obligatoire de le sélectionner.
3. Validez : BibliOfelia ouvre directement la page de **rapport**, qui
   sert aussi d'écran de pointage.

## Scanner les livres en continu

1. Cliquez sur **Lancer l'inventaire** : la caméra s'ouvre en **mode
   continu** et reste ouverte.
2. Scannez chaque livre du rayon, l'un après l'autre. Un **bip** (et une
   vibration) confirme chaque nouveau livre, et un **compteur** monte à
   l'écran.
3. Pour chaque scan :
   - livre **dans le bon rayon** : il est marqué « vu » ;
   - livre **rangé ailleurs** (portée = un emplacement) : BibliOfelia met
     automatiquement à jour son rayon vers celui que vous récolez ;
   - **code inconnu** : signalé, à investiguer.

Le même livre scanné deux fois n'est compté qu'une fois. Si une notice a
plusieurs exemplaires, l'écran indique « exemplaire 2 », « exemplaire 3 »…
pour vous aider à tous les retrouver.

!!! tip "Allez vite, ne réfléchissez pas"
    Inutile de vérifier chaque scan : BibliOfelia trie tout à la fin.
    Concentrez-vous sur la vitesse et la couverture complète du rayon. La
    liste et les compteurs se mettent à jour en direct.

Quand le rayon est parcouru, appuyez sur **Terminer**.

## Lire le rapport

Le rapport s'affiche **par notice**, classé par auteur et titre. Tous les
codes Ofelia y sont en pastilles :

- **vert** : exemplaire trouvé pendant le récolement ;
- **rouge** : exemplaire **manquant** (présent dans la base, pas vu dans le
  rayon).

Vous y voyez aussi le nombre de livres scannés, déplacés automatiquement,
et les codes inconnus rencontrés.

## Que faire des livres manquants ?

Pour chaque exemplaire en rouge, deux possibilités :

- **Il est ailleurs dans la bibliothèque** : récolez les autres rayons, il
  sera automatiquement repositionné au passage.
- **Il est perdu** : marquez l'exemplaire comme **Perdu** depuis sa fiche
  (voir [Livre perdu](../faq.md#livre-perdu)).

## Fréquence recommandée

- **Petite bibliothèque** : récolement complet 1 à 2 fois par an.
- **Grande bibliothèque** : 1 rayon par mois en rotation.

Faites-le idéalement quand la bibliothèque est calme (matin, jour de
fermeture).

## Et OfeliaScan ?

Pour de **gros récolements**, l'application mobile [OfeliaScan](../ofeliascan/activer.md)
peut aussi envoyer une session entière de scans à BibliOfelia. La logique
est la même (livres vus, déplacés, manquants). Pour le récolement courant
d'un rayon, la caméra du site décrite ci-dessus est le moyen le plus simple.
