# Cataloguer avec la douchette

Si votre poste est équipé d'une **douchette USB** (lecteur de code-barres
filaire, branché comme un clavier), vous pouvez cataloguer une caisse de
livres **sans caméra** : vous scannez les ISBN à la chaîne, directement sur
l'écran de BibliOfelia.

C'est le pendant, à la douchette, du [catalogage par
scan caméra](catalogage-scan.md) : même résultat (BibliOfelia crée les
notices et les exemplaires), mais piloté par la douchette du poste fixe.

!!! info "Douchette ou caméra ?"
    La **douchette** est idéale au bureau, sur un poste fixe, et fonctionne même
    sans connexion sécurisée (`https://`). La **caméra** est idéale en mobilité,
    tablette en main. Les deux remplissent le même catalogue.

## Démarrer un lot à la douchette

Depuis [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" } → Inventaire,
cliquez sur
[**Catalogage par douchette**](/bibliofelia/fr/catalog/scan/new-douchette/){ target="_blank" }.

Comme pour le catalogage caméra, vous pouvez fixer des **valeurs par défaut**
pour tout le lot (catégorie, emplacement, libellé). Vous pourrez les
**changer ligne par ligne** ensuite.

## Scanner les ISBN à la chaîne

1. La page s'ouvre avec le champ de saisie **déjà actif** : vous n'avez
   **rien à cliquer**.
2. Scannez le code-barres ISBN au **dos** de chaque livre (il commence par
   978 ou 979) avec la douchette.
3. À chaque lecture, la ligne apparaît dans la liste : BibliOfelia va
   chercher automatiquement le titre, l'auteur et la langue (OpenLibrary,
   Google Books, BnF…).

!!! tip "Plusieurs exemplaires du même livre"
    Vous avez deux copies identiques ? Scannez le même ISBN **deux fois**.
    Au deuxième passage (après quelques secondes), BibliOfelia ajoute un
    exemplaire supplémentaire à la même notice, sans créer de doublon. Un
    re-scan trop rapide est ignoré, pour éviter les lectures en double.

!!! warning "Codes Ofelia refusés"
    Le catalogage accepte les **ISBN** de livres (978/979) et les **ISSN** de
    revues (977). Si vous scannez par erreur une étiquette code Ofelia
    (290/291) déjà posée sur un document, elle est refusée : ici on enregistre
    des documents neufs, pas des exemplaires déjà catalogués.

## Terminer et vérifier le lot

Quand vous avez fini de scanner, cliquez sur **Terminer et voir le lot**. La
liste du lot s'affiche. Pour chaque ligne, vous voyez le livre trouvé (auteur,
titre, langue) et vous pouvez :

- changer la **catégorie**, l'**emplacement** ou l'**état** — à la ligne, ou
  pour plusieurs lignes d'un coup grâce aux cases à cocher ;
- ajuster le **nombre d'exemplaires** ;
- **supprimer** une ligne (icône corbeille) en cas d'erreur de scan.

## Enregistrer le lot

Cliquez sur **Envoyer au catalogue**. BibliOfelia crée toutes les notices
manquantes et tous les exemplaires, avec leurs codes Ofelia. Vous pouvez
ensuite [imprimer uniquement les étiquettes de ce
lot](../impressions/etiquettes.md).

## Voir aussi

- [Cataloguer en scannant (caméra)](catalogage-scan.md) — la même chose avec la
  caméra
- [Modes de saisie](../premiers-pas/saisie.md) — douchette, caméra, clavier
- [Étiquettes de livres](../impressions/etiquettes.md) — imprimer les
  étiquettes du lot
