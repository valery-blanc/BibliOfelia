# FEAT-087 — Scan caméra ouvert à tous les formats

**Status:** DONE
**Date:** 2026-08-31

## Contexte

Suite directe de l'audit du 2026-08-23 (« code externe accepté partout où le
code Ofelia l'est »). Cet audit avait conclu que la **saisie clavier et la
douchette USB** étaient conformes partout, mais que le **scan caméra** rejetait
les codes externes (FEAT-063) dans deux cas :

- (a) EAN-13 valide mais d'un préfixe autre que 290/291/977/978/979 ;
- (b) Code39 / Code128 / Codabar — très courants sur les étiquettes de
  bibliothèque — que les deux moteurs n'étaient même pas configurés pour lire.

Décision Val (2026-08-31) : **ouvrir à tout type de code-barres que le lecteur
accepte** — (a) et (b) ensemble.

## Comportement

La caméra lit désormais tous les formats **linéaires** : EAN-13, EAN-8, UPC-A,
UPC-E, Code128, Code39, Code93, Codabar, ITF.

Les codes **2D** (QR, DataMatrix, Aztec) restent exclus : une étiquette de
bibliothèque est un code à barres, et les activer ferait lire n'importe quelle
affiche présente dans le champ.

### Garde-fous conservés

- **Clé de contrôle** : quand une lecture ressemble à un EAN-13 (13 chiffres),
  sa clé doit tomber juste. C'est ce qui attrape les confusions 1↔7 / 1↔0 du
  décodeur logiciel.
- **Consensus** : deux lectures identiques d'affilée restent exigées. Pour un
  Code39 ou un Code128, qui n'ont pas de somme de contrôle, c'est le seul
  filet — et il est le même que celui qui protégeait déjà les EAN-13.
- **Bande de décodage** centrale (~1/4 de hauteur) inchangée : un seul
  code-barres y tient.

Le paramètre `allowIssn` (FEAT-052) n'a plus d'effet sur le filtre. Il est
conservé pour ne pas toucher aux appels existants.

## Spécification technique

`static/js/scan-camera.js` :

- `isAcceptableCode()` — le filtre de préfixe disparaît ; ne reste que la
  vérification de clé sur les 13 chiffres et une longueur minimale de 3.
- `startHtml5()` — `formatsToSupport` liste les dix formats linéaires, filtrée
  sur les constantes réellement exposées par la version de html5-qrcode
  embarquée (une constante absente rendrait la liste invalide).
- `startQuagga()` — `decoder.readers` passe de `["ean_reader"]` à huit lecteurs.

## Impact sur l'existant

- **Décodage plus lent** côté Quagga : huit lecteurs au lieu d'un, sur le thread
  principal. C'est le prix pour lire un code externe Code128 ; le moteur natif
  (`BarcodeDetector`) n'est pas concerné.
- **Plus de fausses lectures possibles** : Code39 n'a pas de clé de contrôle.
  Le consensus de deux lectures reste le garde-fou, comme avant.
- Aucun changement serveur : `find_item` et `find_member` acceptaient déjà tout.
