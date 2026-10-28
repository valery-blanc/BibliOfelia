# Cataloguer en scannant

Quand une caisse de livres arrive, le **catalogage par scan** est la
façon la plus rapide de tout enregistrer : vous scannez les ISBN à la
chaîne, et BiblOFELIA crée les notices et leurs exemplaires d'un coup.

Deux outils font le même travail. La **caméra** du téléphone ou de la
tablette, et la **douchette USB** branchée sur un poste fixe. Seule la
façon de lire le code-barres change. Le lot, les valeurs par défaut, la
vérification et l'envoi au catalogue sont les mêmes.

C'est l'équivalent, pour la création, du [récolement](recolement.md)
pour la vérification : un **scan en continu**, sans rien recliquer entre
deux livres.

!!! info "Caméra ou douchette ?"
    La **douchette** est idéale au bureau, sur un poste fixe, et fonctionne
    même sans connexion sécurisée (`https://`). La **caméra** est idéale en
    mobilité, tablette en main. Les deux remplissent le même catalogue.

## À quoi sert une session de catalogage

Une **session** de catalogage (on dit aussi un **lot**) sert à ajouter
**beaucoup de livres d'un coup** au catalogue. Le principe se déroule en trois
temps :

1. **Vous ouvrez un lot et vous scannez** tous les livres de la caisse à la
   suite. Rien n'entre encore au catalogue : le lot n'est qu'une liste de
   travail, que vous pouvez corriger ou vider.
2. **Vous vérifiez la liste** — et surtout, vous appliquez des **modifications
   par lot** : cochez plusieurs lignes (ou toutes) et affectez-leur en un seul
   clic la même **classification**, le même **emplacement** dans la bibliothèque ou
   le même **état**. C'est tout l'intérêt de cataloguer ensemble des livres qui
   vont ensemble.
3. **Vous envoyez le lot au catalogue** : les notices et les exemplaires sont
   créés pour de bon, avec la **provenance** choisie au départ, et vous pouvez
   imprimer d'un coup les étiquettes **de ce lot seulement**.

Un lot validé reste consultable : depuis la liste des lots, **Voir le lot**
rappelle quels livres il contenait, avec un lien vers chaque notice.

## Démarrer un lot

Les deux entrées ouvrent **le même formulaire**. Choisissez les
[valeurs par défaut](#defauts), puis cliquez sur **Démarrer le catalogage**.

### Avec la caméra { #camera }

Depuis le [**Catalogue**](/bibliofelia/fr/catalog/){ target="_blank" },
cliquez sur
[**Cataloguer en scannant**](/bibliofelia/fr/catalog/scan/){ target="_blank" },
puis sur [**Nouveau lot**](/bibliofelia/fr/catalog/scan/new/){ target="_blank" }.

Le même écran est aussi dans
[**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" } → Inventaire →
**Catalogage par scan**.

### Avec la douchette { #douchette }

Depuis [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" } →
Inventaire, cliquez sur
[**Catalogage par douchette**](/bibliofelia/fr/catalog/scan/new-douchette/){ target="_blank" }.

## Valeurs par défaut du lot { #defauts }

Avant de scanner, vous pouvez fixer des **valeurs par défaut** pour tout
le lot. **C'est facultatif** : un lot sans classification, sans emplacement
et sans provenance se catalogue très bien.

Pour utiliser l'une de ces valeurs, il faut **l'avoir créée avant**. Le
formulaire du lot ne propose que ce qui existe déjà, et il ne permet pas
d'en ajouter une nouvelle. Ces listes sont dans
[**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" } → Méta-données :

- une [**classification**](/bibliofelia/fr/catalog/categories/){ target="_blank" }
  par défaut (Jeunesse Documentaire, Adultes Fiction…). Les classifications
  Ofelia sont déjà fournies ; n'ouvrez la liste que pour en ajouter une ;
- un [**emplacement**](/bibliofelia/fr/catalog/locations/){ target="_blank" }
  par défaut (le rayon où iront ces livres) ;
- une [**provenance**](/bibliofelia/fr/catalog/provenances/){ target="_blank" }
  par défaut — d'où viennent ces livres : achat de la bibliothèque, don,
  prêt d'une autre bibliothèque. **Tous les exemplaires du lot** la
  reçoivent. C'est le bon choix pour un carton de livres prêtés : le jour
  du retour, un filtre sur cette provenance les retrouve tous ;
- un **nom du lot**, pour le retrouver plus tard. Lui se tape directement :
  il n'a pas de liste à préparer.

La classification et l'emplacement s'appliquent à chaque livre, et vous
pourrez les **changer ensuite**, une ligne ou plusieurs d'un coup. La
provenance, elle, est celle de **tout le lot** : on la choisit ici, avant
de scanner. Pour la modifier une fois les exemplaires créés, passez par
[Provenances](/bibliofelia/fr/catalog/provenances/){ target="_blank" }.

## Scanner les ISBN à la chaîne

Le code-barres ISBN est au **dos** du livre. Il commence par 978 ou 979.
À chaque lecture, BiblOFELIA va chercher automatiquement le titre,
l'auteur et la langue (OpenLibrary, Google Books, BnF…).

### À la caméra

1. Cliquez sur **Scanner des livres** : la caméra s'ouvre en mode continu.
2. Scannez chaque livre.
3. Un **bip** confirme la lecture. L'écran affiche le **titre et l'auteur**
   trouvés — ou, à défaut, l'ISBN et la langue.
4. Appuyez sur **Terminer** : la caméra se ferme et la liste du lot
   s'affiche, prête à être vérifiée.

### À la douchette

1. La page s'ouvre avec le champ de saisie **déjà actif** : vous n'avez
   **rien à cliquer**.
2. Scannez chaque livre avec la douchette. La ligne apparaît dans la liste
   au fur et à mesure.
3. Quand vous avez fini, cliquez sur **Terminer et voir le lot** pour
   passer à la vérification.

Dans les deux cas, le champ **Saisir un ISBN à la main** permet de taper
un code abîmé, puis **Ajouter**.

!!! tip "Plusieurs exemplaires du même livre"
    Vous avez deux copies identiques ? Scannez le même ISBN **deux fois**.
    Au deuxième passage (après quelques secondes), BiblOFELIA indique
    « exemplaire 2 » — en gros dans le viseur de la caméra, dans la liste
    à la douchette. Il ajoutera un exemplaire supplémentaire à la même
    notice, sans créer de doublon. Un re-scan trop rapide (moins de
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
scannez ce code-barres 977 **dans le même lot** que vos livres, à la
caméra comme à la douchette.

- BiblOFELIA reconnaît l'ISSN et va chercher le **titre de la revue**
  (BnF, BNE).
- Tous les numéros d'une même revue partagent le **même ISSN** : ils
  retombent donc sur **une seule notice** « revue », à laquelle chaque
  numéro scanné ajoute un exemplaire.

!!! info "Un ISSN = une seule notice de revue"
    Si vous scannez deux numéros différents du même magazine, BiblOFELIA ne
    crée pas deux fiches : il ajoute un exemplaire à la notice de la revue.
    Pour distinguer les numéros (date, n°), notez-les dans les notes de
    l'exemplaire.

## Vérifier et ajuster le lot

La liste est la même, que le lot ait été scanné à la caméra ou à la
douchette. Pour chaque ligne, vous voyez le livre trouvé (auteur, titre,
langue) et vous pouvez :

- changer la **classification**, l'**emplacement** ou l'**état** : cochez
  une ou plusieurs lignes (la case en tête du tableau les coche toutes),
  choisissez les valeurs dans **Modifier les lignes cochées**, puis
  **Appliquer aux lignes cochées** ;
- ajuster le **nombre d'exemplaires** sur la ligne ;
- **supprimer** une ligne (icône corbeille) en cas d'erreur de scan.

**Enregistrer** garde ces ajustements sans rien créer au catalogue. Vous
pouvez reprendre le lot plus tard.

!!! info "Notice déjà existante"
    Si un ISBN correspond à un livre **déjà présent** dans le catalogue,
    BiblOFELIA ne recrée pas la notice : il ajoute simplement vos nouveaux
    exemplaires à la notice existante, sans la modifier.

## Envoyer le lot au catalogue

Cliquez sur **Envoyer au catalogue**. BiblOFELIA crée toutes les notices
manquantes et tous les exemplaires, avec leurs codes Ofelia et la
**provenance** choisie au départ du lot.

## Imprimer uniquement les étiquettes de ce lot

Chaque exemplaire créé est rattaché à **son lot de catalogage**. Au moment
d'imprimer les étiquettes, vous pouvez donc filtrer sur ce lot précis : seul
ce que vous venez d'enregistrer est proposé (et pré-coché), sans ressortir
toute la bibliothèque. Voir [Étiquettes de livres](../impressions/etiquettes.md).

## Voir aussi

- [Provenances](../catalogue/provenances.md) — d'où vient un exemplaire, et
  comment retrouver un fonds prêté
- [Scanner avec la caméra](../premiers-pas/scanner-camera.md) — comment la
  caméra fonctionne
- [Modes de saisie](../premiers-pas/saisie.md) — douchette, caméra, clavier
- [Ajouter un livre](../catalogue/ajouter-livre.md) — création d'une seule
  notice à la main
- [Étiquettes de livres](../impressions/etiquettes.md) — imprimer les
  étiquettes du lot
