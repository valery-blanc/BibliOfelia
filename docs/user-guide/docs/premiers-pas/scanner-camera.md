# Scanner avec la caméra

BibliOfelia sait scanner les codes-barres **directement avec la caméra**
de votre appareil — téléphone, tablette ou ordinateur portable équipé
d'une webcam. Aucune application à installer : tout se passe dans le
navigateur.

C'est le mode utilisé par tous les boutons **Scanner** du site (le
bandeau du tableau de bord, les pages Prêt et Retour, la recherche, le
champ ISBN d'une notice).

## Comment ça marche

1. Cliquez sur un bouton **Scanner** (ou sur l'icône caméra ronde à côté
   d'un champ de recherche).
2. La caméra s'ouvre dans une fenêtre, avec une **bande de visée** au
   centre de l'écran.
3. Placez le code-barres du livre ou de la carte **dans la bande
   centrale**. Inutile de viser toute l'image : seul ce qui passe dans la
   bande est lu.
4. Dès que le code est reconnu, vous entendez un **bip** (et le téléphone
   vibre). Le code est saisi automatiquement.

!!! tip "Visez la bande, pas tout l'écran"
    La lecture est volontairement limitée à une bande horizontale au
    milieu de l'image. Cela évite de lire par erreur un code-barres voisin
    quand plusieurs livres sont côte à côte. Approchez le livre jusqu'à ce
    que son code-barres remplisse la largeur de la bande.

## Deux façons de scanner

Selon la page, la caméra fonctionne différemment :

- **Scan unique** (Prêt, Retour, recherche, ISBN) : la caméra lit **un**
  code puis se ferme et renseigne le champ. Vous relancez le scan pour le
  suivant.
- **Scan en continu** (Récolement, Catalogage par scan) : la caméra
  **reste ouverte** et enchaîne les lectures. Un compteur s'affiche, un bip
  confirme chaque nouveau livre. Vous balayez toute une étagère ou une
  caisse sans rien recliquer. Appuyez sur **Terminer** quand vous avez fini.

## Ce que la caméra lit

La caméra ne reconnaît que les **codes-barres de livres et de cartes**
(format EAN-13, 13 chiffres). C'est volontaire : cela rend la lecture
beaucoup plus fiable et évite les fausses lectures. Sont reconnus :

- les **ISBN** au dos des livres (commençant par 978 ou 979) ;
- les **codes Ofelia** des étiquettes et des cartes de membre (commençant
  par 290 ou 291).

## La caméra ne s'ouvre pas ?

Quelques points à vérifier :

!!! warning "Connexion sécurisée (HTTPS) requise"
    Pour des raisons de sécurité, les navigateurs n'autorisent la caméra
    que sur une connexion **sécurisée (https://)**. Si vous accédez à
    BibliOfelia par une adresse locale en `http://` (par exemple
    `http://ofelia.local`), la caméra ne pourra pas s'ouvrir. Dans ce cas,
    utilisez une **douchette** ou la **saisie au clavier**, ou demandez à
    l'administrateur de la Box l'adresse sécurisée.

- **Autorisation refusée** : la première fois, le navigateur demande
  l'autorisation d'utiliser la caméra. Répondez **Autoriser**. Si vous avez
  refusé, réautorisez la caméra dans les réglages du site (icône de cadenas
  à gauche de l'adresse).
- **Aucune caméra détectée** : sur un poste fixe sans webcam, la caméra
  n'est pas disponible — utilisez la douchette ou le clavier.
- **Message d'erreur explicite** : en cas de problème, BibliOfelia affiche
  la raison exacte et vous invite à **saisir le code à la main**. Vous
  n'êtes jamais bloqué.

## Et si je n'ai pas de caméra ?

Tous les flux restent utilisables **sans caméra** :

- une **douchette** USB se comporte comme un clavier ultra-rapide ;
- la **saisie au clavier** est toujours possible (tapez le code, puis
  **Entrée** ou **Valider**).

Voir [Modes de saisie](saisie.md) pour choisir l'outil adapté.

## Voir aussi

- [Faire un prêt](../prets-retours/faire-pret.md)
- [Cataloguer en scannant](../inventaire/catalogage-scan.md)
- [Récolement](../inventaire/recolement.md)
