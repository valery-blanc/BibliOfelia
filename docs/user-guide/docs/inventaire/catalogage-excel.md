# Cataloguer depuis Excel

Beaucoup de bibliothèques arrivent dans le projet Ofelia avec un fonds
déjà saisi dans un **tableur Excel** (un identifiant maison, un titre, un
auteur, parfois un ISBN). Le **catalogage Excel** offre deux outils pour
exploiter ce fichier :

1. **Vérifier un fichier** — BibliOfelia annote votre tableur avec ce que
   les bases en ligne connaissent de chaque livre, sans rien modifier dans
   le catalogue. Idéal **avant** une migration, pour mesurer la qualité du
   fichier et le corriger à la main.
2. **Importer dans le catalogue** — BibliOfelia transforme une liste
   d'ISBN en notices et exemplaires, d'un seul coup.

!!! info "Réservé aux bibliothécaires"
    Le catalogage Excel se trouve dans le menu **Avancé**, accessible aux
    bibliothécaires et aux administrateurs.

## Ouvrir le catalogage Excel

Depuis le menu [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" },
section **Inventaire**, cliquez sur
[**Catalogage Excel**](/bibliofelia/fr/catalog/excel-catalog/){ target="_blank" }.

La page propose deux encadrés côte à côte : **Vérifier un fichier** (à
gauche) et **Importer dans BibliOfelia** (à droite).

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
