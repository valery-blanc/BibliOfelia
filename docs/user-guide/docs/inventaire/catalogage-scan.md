# Cataloguer en scannant

Quand une caisse de livres arrive, le **catalogage par scan** est la
façon la plus rapide de tout enregistrer : vous scannez les ISBN à la
chaîne avec la caméra, et BibliOfelia crée les notices et leurs
exemplaires d'un coup.

C'est l'équivalent, pour la création, du [récolement](recolement.md)
pour la vérification : un **scan en continu**, sans rien recliquer entre
deux livres.

## Démarrer un lot de catalogage

Depuis le [**Catalogue**](/bibliofelia/fr/catalog/){ target="_blank" } (ou
[**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" } → Inventaire),
cliquez sur
[**Cataloguer en scannant**](/bibliofelia/fr/catalog/scan/){ target="_blank" },
puis sur [**Nouveau lot**](/bibliofelia/fr/catalog/scan/new/){ target="_blank" }.

Avant de scanner, vous pouvez fixer des **valeurs par défaut** pour tout
le lot :

- une **catégorie** par défaut (Adultes, Jeunesse…) ;
- un **emplacement** par défaut (le rayon où iront ces livres) ;
- un **libellé** pour retrouver le lot plus tard.

Ces valeurs s'appliquent à chaque livre du lot, mais vous pourrez les
**changer ligne par ligne** ensuite.

## Scanner les ISBN à la chaîne

1. Cliquez sur **Lancer le scan** : la caméra s'ouvre en mode continu.
2. Scannez le code-barres ISBN au **dos** de chaque livre (il commence
   par 978 ou 979).
3. À chaque lecture, un **bip** confirme et la ligne apparaît dans la
   liste : BibliOfelia va chercher automatiquement le titre, l'auteur et
   la langue (OpenLibrary, Google Books, BnF…).
4. Pendant le scan, l'écran affiche le **titre et l'auteur** trouvés —
   ou, à défaut, l'ISBN et la langue.

!!! tip "Plusieurs exemplaires du même livre"
    Vous avez deux copies identiques ? Scannez le même ISBN **deux fois**.
    Au deuxième passage (après quelques secondes), BibliOfelia affiche
    « exemplaire 2 » en gros : il ajoutera un exemplaire supplémentaire à
    la même notice, sans créer de doublon. Un re-scan trop rapide (moins de
    3 secondes) est ignoré, pour éviter les lectures en double.

!!! warning "Codes Ofelia refusés"
    Le catalogage accepte les **ISBN** de livres (978/979) et les **ISSN**
    de revues (977, voir ci-dessous). Si vous scannez par erreur une
    étiquette code Ofelia (290/291) déjà posée sur un document, elle est
    refusée : ici on enregistre des documents neufs, pas des exemplaires
    déjà catalogués.

## Cataloguer une revue ou un magazine

Les revues et les magazines n'ont pas d'ISBN, mais un **ISSN** : un
code-barres qui commence par **977**. Pas besoin d'un outil à part —
scannez ce code-barres 977 **dans le même lot** que vos livres.

- BibliOfelia reconnaît l'ISSN et va chercher le **titre de la revue**
  (BnF, BNE).
- Tous les numéros d'une même revue partagent le **même ISSN** : ils
  retombent donc sur **une seule notice** « revue », à laquelle chaque
  numéro scanné ajoute un exemplaire.

!!! info "Un ISSN = une seule notice de revue"
    Si vous scannez deux numéros différents du même magazine, BibliOfelia ne
    crée pas deux fiches : il ajoute un exemplaire à la notice de la revue.
    Pour distinguer les numéros (date, n°), notez-les dans les notes de
    l'exemplaire.

## Vérifier et ajuster le lot

Quand vous appuyez sur **Terminer**, la liste du lot s'affiche. Pour
chaque ligne, vous voyez le livre trouvé (auteur, titre, langue) et vous
pouvez :

- changer la **catégorie**, l'**emplacement** ou l'**état** — à la ligne,
  ou pour plusieurs lignes d'un coup grâce aux cases à cocher et au bouton
  **Tout cocher** ;
- ajuster le **nombre d'exemplaires** ;
- **supprimer** une ligne (icône corbeille) en cas d'erreur de scan.

!!! info "Notice déjà existante"
    Si un ISBN correspond à un livre **déjà présent** dans le catalogue,
    BibliOfelia ne recrée pas la notice : il ajoute simplement vos nouveaux
    exemplaires à la notice existante, sans la modifier.

## Enregistrer le lot

Cliquez sur **Enregistrer le lot**. BibliOfelia crée toutes les notices
manquantes et tous les exemplaires, avec leurs codes Ofelia.

## Imprimer uniquement les étiquettes de ce lot

Chaque exemplaire créé est rattaché à **son lot de catalogage**. Au moment
d'imprimer les étiquettes, vous pouvez donc filtrer sur ce lot précis : seul
ce que vous venez d'enregistrer est proposé (et pré-coché), sans ressortir
toute la bibliothèque. Voir [Étiquettes de livres](../impressions/etiquettes.md).

## Voir aussi

- [Scanner avec la caméra](../premiers-pas/scanner-camera.md) — comment la
  caméra fonctionne
- [Ajouter un livre](../catalogue/ajouter-livre.md) — création d'une seule notice à la main
- [Étiquettes de livres](../impressions/etiquettes.md) — imprimer les
  étiquettes du lot
