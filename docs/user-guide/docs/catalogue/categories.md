# Catégories

Les **catégories** classent les livres : Romans, Albums, Documentaires…
Chaque notice en reçoit une, et c'est elle qui détermine la durée de prêt
par défaut.

Depuis [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" }, ouvrez
**Catégories** pour les créer, les modifier ou les supprimer.

## Les champs

- **Code** — court et sans espace : `ENF-ALB`, `ADU-ROM`
- **Nom** — ce que voient les bibliothécaires et les lecteurs
- **Abréviation** — la **cote** imprimée sur la tranche du livre (voir
  ci-dessous)
- **Catégorie parente** — pour ranger « Albums » sous « Enfance »
- **Durée de prêt** — en jours ; laissez vide pour la durée par défaut de la
  bibliothèque

## Les catégories fournies

BibliOfelia arrive avec les **20 catégories officielles Ofelia** : cinq tranches
d'âge croisées avec quatre types de document.

| | Fiction | Documentaire | Album | Bande dessinée |
|---|---|---|---|---|
| Adultes | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Jeunesse | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Adolescents | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Enfants | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Petite enfance | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

Le **code sert aussi de cote** : ce qui est écrit sur la tranche du livre est ce
que vous voyez dans le menu des catégories.

!!! info "La langue n'est pas dans la catégorie"
    Un livre en anglais rangé en fiction adulte va dans `AD FIC`, pas dans une
    catégorie « Anglais Adultes Fiction ». La langue se renseigne sur la fiche du
    livre et se retrouve avec le filtre **Langue** du catalogue. Une catégorie
    par langue multiplierait les lignes sans rien apporter.

## L'abréviation, ou cote de rayon

C'est la version courte du nom, celle qui tient sur une étiquette de
tranche. Pour « Romans fiction pour adolescents », on écrit `RO FI ADO`.

Elle vaut pour **toutes** les notices de la catégorie : une seule saisie, et
deux livres de la même catégorie ne pourront jamais afficher deux cotes
différentes.

À l'installation, les 16 catégories fournies reçoivent une abréviation de
départ (`ENF ALB`, `ADU ROM`…). Vous pouvez les remplacer par les vôtres :
BibliOfelia ne réécrira jamais une cote que vous avez saisie.

Une fois les abréviations en place, imprimez les
[étiquettes de tranche](../impressions/etiquettes.md).

## Supprimer une catégorie

**Aucun livre n'est supprimé.** Les notices concernées se retrouvent
simplement sans catégorie, et l'écran de confirmation vous dit combien elles
sont. Vous pourrez leur en réaffecter une avec les
[opérations en lot](operations-lot.md).

## Voir aussi

- [Opérations en lot](operations-lot.md)
- [Imprimer les étiquettes](../impressions/etiquettes.md)
