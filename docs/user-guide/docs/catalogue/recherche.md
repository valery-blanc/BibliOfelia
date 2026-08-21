# Recherche

BibliOfelia offre deux outils de recherche complémentaires : la
**recherche globale** depuis n'importe quelle page, et le **filtre du
catalogue** quand vous êtes déjà dans la liste des livres.

## La recherche globale

En haut de chaque page, un grand champ de recherche accepte :

- **Un titre ou un mot du titre** — "petit prince", "germinal"
- **Un nom d'auteur** — "hugo", "saint-exupéry"
- **Un ISBN-13** — 9782070612758 (code de l'éditeur, au dos du livre)
- **Un code Ofelia d'exemplaire** — 2900000000017 (code-barres de
  l'étiquette BibliOfelia)
- **Un code Ofelia externe** — BCF13298781X (code posé par une autre
  bibliothèque ou par un donateur, si vous l'avez enregistré sur
  l'exemplaire)
- **Un nom de membre** — "rakoto", "dubois"
- **Un numéro de carte** — 2910000000444 (code-barres de la carte)

BibliOfelia détecte automatiquement de quoi il s'agit (livre, membre,
exemplaire) et vous emmène directement sur la bonne page.

!!! tip "Tapez puis Entrée"
    Pas besoin de cliquer sur un bouton : tapez et appuyez sur Entrée,
    BibliOfelia s'occupe du reste.

## Le filtre du catalogue

Depuis la page [**Catalogue**](/bibliofelia/fr/catalog/){ target="_blank" },
la liste des notices peut être filtrée par :

- **Texte libre** (titre, auteur, éditeur)
- **Catégorie** (Adultes, Jeunesse, Documentaire…)
- **Langue**
- **Localisation**

![Liste du catalogue avec filtres](../assets/screenshots/fr/catalogue/record-list.png)

Les filtres se combinent : par exemple "Adultes" + "français" +
"Gallimard" pour ne voir que les romans Gallimard en français pour
adultes.

## Chercher les exemplaires plutôt que les notices

Par défaut, le catalogue affiche **une ligne par livre** (par notice) : si
vous avez trois exemplaires du *Petit Prince*, vous voyez une seule ligne
avec « 3 » dans la colonne **Ex.**

La barre de filtres se termine par deux boutons, qui lancent la même recherche
mais présentent le résultat autrement :

- **Rechercher des notices** — une ligne par livre (l'affichage habituel) ;
- **Rechercher des exemplaires** — **une ligne par exemplaire**. Les trois
  exemplaires du *Petit Prince* apparaissent alors sur trois lignes.

Le bouton du mode en cours est mis en avant : vous voyez d'un coup d'œil ce que
vous regardez. En mode exemplaire, la colonne « Ex. » laisse la place à trois
colonnes utiles :

- **Code Ofelia** — le code-barres de l'étiquette
- **Code Ofelia externe** — le code d'une autre bibliothèque, s'il existe
- **Provenance** — d'où vient cet exemplaire

C'est le seul écran qui montre qu'un même livre a un exemplaire **acheté par
la bibliothèque** et un autre **prêté par une bibliothèque partenaire**.
Combinez-le avec le filtre **Provenance** pour retrouver un fonds entier —
par exemple le jour où il faut le rendre.

!!! tip "Rendre un fonds prêté"
    Cochez **Chercher les exemplaires**, filtrez sur la provenance, cochez
    **Tout cocher**, puis **Supprimer les exemplaires sélectionnés**. Les
    livres sortent du catalogue, mais les notices restent : si la
    bibliothèque partenaire vous reprête les mêmes titres l'an prochain, il
    n'y a plus qu'à recréer des exemplaires. Voir
    [Provenances](provenances.md).

## Une recherche tolérante

La recherche n'est pas pointilleuse : taper "petit prince" trouve aussi
"Le Petit Prince" et "petits princes". Vous pouvez écrire en
majuscules ou en minuscules, avec ou sans accents, dans n'importe
quel ordre. BibliOfelia fait le reste.

## Recherche par code-barres

Avec une [douchette](../premiers-pas/saisie.md) ou la [caméra de votre
appareil](../premiers-pas/scanner-camera.md) (icône caméra à côté de la
barre de recherche), vous pouvez scanner directement le code-barres d'un
livre : la fiche du livre ou de l'exemplaire s'ouvre instantanément.
