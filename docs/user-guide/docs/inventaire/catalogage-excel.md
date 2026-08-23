# Cataloguer depuis Excel

Beaucoup de bibliothèques arrivent dans le projet Ofelia avec un fonds
déjà saisi dans un **tableur Excel** (un identifiant maison, un titre, un
auteur, parfois un ISBN). Le **catalogage Excel** offre quatre outils pour
exploiter ce fichier :

1. **Vérifier un fichier** — BibliOfelia annote votre tableur avec ce que
   les bases en ligne connaissent de chaque livre, sans rien modifier dans
   le catalogue. Idéal **avant** une migration, pour mesurer la qualité du
   fichier et le corriger à la main.
2. **Importer dans le catalogue** — BibliOfelia transforme une liste
   d'ISBN en notices et exemplaires, d'un seul coup.
3. **Exporter le catalogue** — BibliOfelia vous rend tout votre fonds dans
   un tableur, une ligne par exemplaire.
4. **Mettre à jour des exemplaires** — vous renvoyez ce tableur corrigé, et
   BibliOfelia applique vos corrections aux livres déjà catalogués, sans
   jamais en créer de nouveaux.

!!! info "Réservé aux bibliothécaires"
    Le catalogage Excel se trouve dans le menu **Avancé**, accessible aux
    bibliothécaires et aux administrateurs.

## Ouvrir le catalogage Excel

Depuis le menu [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" },
section **Inventaire**, cliquez sur
[**Catalogage Excel**](/bibliofelia/fr/catalog/excel-catalog/){ target="_blank" }.

La page propose quatre encadrés : **Vérifier un fichier**, **Importer dans
BibliOfelia**, **Exporter le catalogue** et **Mettre à jour des
exemplaires**.

## Vérifier un fichier

À utiliser pour **contrôler** un tableur sans toucher au catalogue.

Votre fichier doit être un **`.xlsx`** dont la première ligne contient au
moins ces quatre colonnes (la casse et les accents sont tolérés) :

| Colonne | Contenu |
|---|---|
| `ID` | votre identifiant maison (conservé tel quel) |
| `TITLE` | le titre du livre |
| `AUTHOR` | le ou les auteurs |
| `ISBN` | l'ISBN complet (10 ou 13 chiffres) |

!!! warning "ISBN incomplet ou erroné"
    La recherche par ISBN n'accepte qu'un ISBN **valide** (10 ou 13
    chiffres). Un ISBN incomplet ou faux est marqué `ISBN_INVALID` et ne
    permet **pas** de retrouver le livre par ISBN — c'est justement le cas
    catastrophe. C'est alors le `TITLE` et l'`AUTHOR` qui sauvent la mise,
    via la recherche par titre + auteur : soignez ces deux colonnes.

Dans l'encadré
[**Vérifier un fichier**](/bibliofelia/fr/catalog/excel-catalog/){ target="_blank" },
choisissez votre fichier puis cliquez sur **Lancer la vérification**.

BibliOfelia interroge **OpenLibrary, Google Books, la BNF et la BNE**,
d'abord par ISBN, puis par titre + auteur. Le traitement se fait en tâche
de fond : comptez environ **10 minutes pour 300 lignes**.

Quand le travail est terminé, cliquez sur **Télécharger le fichier
annoté**. Vous récupérez votre tableur d'origine, enrichi de colonnes
supplémentaires :

- `TITLE_FOUND_BY_ISBN`, `AUTHOR_FOUND_BY_ISBN`, `SOURCE_BY_ISBN` — ce que
  l'ISBN a permis de retrouver ;
- `ISBN_FOUND_BY_TA`, `TITLE_FOUND_BY_TA`, `AUTHOR_FOUND_BY_TA` — ce que la
  recherche par titre + auteur a trouvé ;
- `CONFIDENCE` — un score de 0 à 100 sur la fiabilité de l'appariement.

!!! tip "Lire les couleurs"
    Les cellules au score de confiance faible apparaissent en **orange** :
    ce sont les lignes à relire à la main. Un `ISBN_FOUND_BY_TA` différent
    de votre ISBN signale souvent une **faute de saisie** dans le fichier
    d'origine.

La vérification **n'écrit rien** dans le catalogue : vous pouvez la lancer
autant de fois que nécessaire.

## Importer dans le catalogue

À utiliser pour **créer** réellement les notices et les exemplaires à
partir d'une liste d'ISBN.

Votre fichier `.xlsx` doit contenir au moins une colonne **`ISBN`**.
Toutes les autres colonnes sont **facultatives** : ajoutez seulement
celles dont vous disposez, dans n'importe quel ordre.

| Colonne | Contenu |
|---|---|
| `ISBN` | **obligatoire** |
| `LOCATION` | le code d'emplacement (sinon l'exemplaire est créé sans emplacement) |
| `CATEGORY` | le nom d'une catégorie existante |
| `TITLE` | le titre de la fiche |
| `AUTHOR` | le ou les auteurs, séparés par des **points-virgules** |
| `TYPE` | le type de document (Livre, BD / manga, Revue, Journal, CD audio, Autre) |
| `EDITOR` | l'éditeur |
| `YEAR` | l'année de publication |
| `LANGUAGE` | le code langue (fr, en, es…) |
| `TAGS` | des mots-clés séparés par des **virgules** |
| `CONDITION` | l'état de l'exemplaire (Neuf, Bon, Usé, Abîmé) |
| `EXTERNAL_CODE` | le code d'une autre bibliothèque déjà posé sur le livre |
| `PROVENANCE` | le code ou le nom d'une provenance existante |
| `CATEGORY_ABBR` | l'abréviation de la catégorie (cote de rayon) |

Dans l'encadré
[**Importer dans BibliOfelia**](/bibliofelia/fr/catalog/excel-catalog/){ target="_blank" },
choisissez votre fichier puis cliquez sur **Importer dans le catalogue**.

Chaque ISBN devient une notice et un exemplaire. Si un ISBN est **déjà
présent** dans le catalogue, BibliOfelia ne recrée pas la notice : il
ajoute simplement un exemplaire à la notice existante.

!!! info "Une colonne remplie remplace l'information de la fiche"
    Si vous ajoutez une des colonnes ci-dessus (titre, auteur, éditeur…)
    et que la **cellule est remplie**, sa valeur **écrase** le champ
    correspondant de la fiche — **même si la notice existe déjà**. Une
    **cellule vide ne touche à rien** : l'information déjà en place est
    conservée. Pour l'auteur et les tags, la liste du fichier **remplace**
    l'existante (elle ne s'y ajoute pas). Une valeur non reconnue pour
    `TYPE` ou `CONDITION`, ou une année qui n'est pas un nombre, est
    **ignorée** et signalée dans les avertissements du lot.

L'import crée un **lot de catalogage** : une fois le travail terminé,
cliquez sur **Voir le lot importé** pour l'ouvrir, ou retrouvez-le dans
[**Catalogage par scan**](/bibliofelia/fr/catalog/scan/){ target="_blank" },
exactement comme un lot scanné à la caméra.

!!! tip "Compléter ce qui manque en ligne"
    Vous n'avez que les ISBN, sans titre ni auteur ? Lancez ensuite un
    **enrichissement** sur le lot pour aller chercher les métadonnées en
    ligne (OpenLibrary, Google Books, BnF…). Les colonnes du fichier
    restent prioritaires : l'enrichissement ne complète que ce qui est
    encore vide.

## Exporter le catalogue

À utiliser pour **récupérer tout votre fonds** dans un tableur : pour le
relire, en garder une copie hors ligne, ou préparer une correction en masse.

Dans l'encadré **Exporter le catalogue**, cliquez sur **Exporter le
catalogue**. Le fichier `catalogue-AAAA-MM-JJ.xlsx` se télécharge
immédiatement — il n'y a rien à attendre.

Le tableur contient **une ligne par exemplaire**, pas par titre. Un livre
que vous possédez en trois exemplaires occupe donc trois lignes : c'est
normal, car l'emplacement, l'état, la provenance et le code externe
appartiennent à l'**exemplaire** et non à la fiche.

| Colonne | Contenu |
|---|---|
| `OFELIA_CODE` | le code Ofelia de l'exemplaire (le code-barres de l'étiquette) |
| `INTERNAL_ID` | le code lisible imprimé à côté du code-barres (`OFL-…`) |
| `EXTERNAL_CODE` | le code d'une autre bibliothèque posé sur le livre |
| `ISBN`, `TITLE`, `AUTHOR`, `EDITOR`, `YEAR`, `LANGUAGE` | les informations de la fiche |
| `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `TAGS` | le classement |
| `CONDITION`, `PROVENANCE`, `LOCATION` | les informations de l'exemplaire |

!!! tip "C'est le fichier de la mise à jour"
    Les colonnes de l'export sont **exactement** celles que BibliOfelia sait
    relire. Corrigez ce que vous voulez dans Excel, puis renvoyez le même
    fichier par **Mettre à jour des exemplaires** : rien d'autre à préparer.

## Mettre à jour des exemplaires

À utiliser pour **corriger en masse** des livres **déjà** dans le catalogue :
changer des emplacements après un déménagement de rayon, passer une série en
« Usé », attribuer des codes externes, rattraper des titres mal saisis.

!!! success "Aucun livre n'est créé"
    Cet outil ne crée **jamais** de fiche ni d'exemplaire. Si une ligne
    désigne un exemplaire qui n'existe pas, elle est **signalée** et laissée
    de côté — jamais transformée en nouveau livre. Vous pouvez donc renvoyer
    un export sans risquer de dupliquer votre bibliothèque.

Chaque ligne doit dire **de quel exemplaire elle parle**. Le fichier doit
donc contenir au moins une de ces deux colonnes :

| Colonne | Contenu |
|---|---|
| `OFELIA_CODE` | le code Ofelia de l'exemplaire — le code-barres `290…` **ou** le code lisible `OFL-…` |
| `EXTERNAL_CODE` | le code d'une autre bibliothèque posé sur le livre |

!!! info "Si les deux colonnes sont remplies"
    C'est le **code Ofelia** qui désigne l'exemplaire, et le code externe de
    la ligne **lui est appliqué**. C'est ainsi qu'on attribue des codes
    externes à beaucoup de livres d'un coup : une colonne `OFELIA_CODE` pour
    dire de quel livre il s'agit, une colonne `EXTERNAL_CODE` avec le code à
    poser.

Toutes les autres colonnes de l'import sont acceptées et **facultatives** :
`TITLE`, `AUTHOR`, `CATEGORY`, `CATEGORY_ABBR`, `TYPE`, `EDITOR`, `YEAR`,
`LANGUAGE`, `TAGS`, `CONDITION`, `PROVENANCE`, `LOCATION` et `ISBN`.

!!! warning "Une cellule vide n'efface rien"
    Une cellule **remplie** remplace la valeur existante ; une cellule
    **vide** laisse la valeur en place. Cet outil ne sert donc **pas** à
    vider un champ — pour cela, ouvrez la fiche du livre. C'est ce qui vous
    permet de renvoyer un export entier après n'avoir corrigé que deux
    colonnes.

Choisissez votre fichier, cliquez sur **Mettre à jour les exemplaires**,
puis suivez le travail comme un import. La page de détail affiche :

- **Exemplaires modifiés** — les lignes qui ont réellement changé quelque
  chose ;
- **Lignes sans changement** — l'exemplaire a bien été retrouvé, mais le
  fichier disait déjà la même chose que le catalogue ;
- **Erreurs** — les lignes non appliquées, avec un bandeau rouge et le
  détail plus bas.

| Avertissement | Ce qu'il veut dire |
|---|---|
| `OFELIA_CODE_UNKNOWN` | aucun exemplaire ne porte ce code Ofelia — ligne ignorée |
| `EXTERNAL_CODE_UNKNOWN` | aucun exemplaire ne porte ce code externe — ligne ignorée |
| `NO_KEY` | la ligne ne dit pas de quel exemplaire elle parle |
| `EXTERNAL_CODE_DUPLICATE` | ce code externe est déjà sur un autre livre — non repris, le reste de la ligne est appliqué |
| `ISBN_CONFLICT` | cet ISBN appartient déjà à une autre fiche — non repris, le reste est appliqué |
| `LOCATION_UNKNOWN`, `CATEGORY_UNKNOWN`, `PROVENANCE_UNKNOWN` | la valeur n'existe pas dans vos listes — ignorée, le reste est appliqué |

!!! tip "Une fiche, plusieurs exemplaires"
    Le titre, l'auteur ou l'éditeur appartiennent à la **fiche** : les
    corriger sur la ligne d'un exemplaire les corrige pour **tous** les
    exemplaires de ce livre. L'emplacement, l'état, la provenance et le code
    externe, eux, ne touchent que l'exemplaire de la ligne.

## Suivre vos travaux

En bas de la page
[**Catalogage Excel**](/bibliofelia/fr/catalog/excel-catalog/){ target="_blank" },
la section **Travaux récents** liste vos dernières vérifications et
imports. Cliquez sur **Détails** pour suivre l'avancement, télécharger un
fichier annoté ou consulter les avertissements ligne par ligne.

## Bon à savoir

!!! warning "Format et limites"
    - Seuls les fichiers **`.xlsx`** sont acceptés (pas de `.xls`, `.csv`
      ni `.ods`).
    - Taille maximale : **5 Mo**, **10 000 lignes**.
    - Pour une meilleure couverture des ISBN, une **clé Google Books** peut
      être configurée par l'administrateur ; sans elle, un quota peut
      laisser quelques lignes incomplètes (colonne `SOURCE_BY_ISBN` =
      `RATE_LIMITED`). Relancez le lendemain : le quota se réinitialise
      chaque jour.

## Voir aussi

- [Cataloguer en scannant](catalogage-scan.md) — le même import, mais à la
  caméra livre par livre
- [Ajouter un livre](../catalogue/ajouter-livre.md) — créer une seule
  notice à la main
