# Classifications

Les **classifications** rangent les livres : Jeunesse Documentaire, Adultes
Fiction, Enfants Album… Chaque notice en reçoit une, et c'est elle qui
détermine la durée de prêt par défaut.

Depuis [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" }, ouvrez
**Classifications** pour les créer, les modifier ou les supprimer.

## Les champs

- **Code** — identifiant unique. Pour les classifications Ofelia, il est
  identique au code de classification (`JE DOC`)
- **Nom** — ce que voient les bibliothécaires et les lecteurs
  (ex. « Jeunesse Documentaire »)
- **Code de classification** — ce qui est **imprimé sur la tranche** du livre
  (voir ci-dessous)
- **Classification parente** — pour ranger une classification sous une autre
- **Durée de prêt** — en jours ; laissez vide pour la durée par défaut de la
  bibliothèque

## Les classifications fournies

BibliOfelia arrive avec les **20 classifications officielles Ofelia** : cinq
tranches d'âge croisées avec quatre types de document.

| | Fiction | Documentaire | Album | Bande dessinée |
|---|---|---|---|---|
| Adultes | `AD FIC` | `AD DOC` | `AD ALB` | `AD BD` |
| Jeunesse | `JE FIC` | `JE DOC` | `JE ALB` | `JE BD` |
| Adolescents | `ADO FIC` | `ADO DOC` | `ADO ALB` | `ADO BD` |
| Enfants | `EN FIC` | `EN DOC` | `EN ALB` | `EN BD` |
| Petite enfance | `PE FIC` | `PE DOC` | `PE ALB` | `PE BD` |

Le **code sert aussi de code de classification** : ce qui est écrit sur la
tranche du livre est ce que vous voyez dans le menu.

!!! info "La langue n'est pas dans la classification"
    Un livre en anglais rangé en fiction adulte va dans `AD FIC`, pas dans une
    classification « Anglais Adultes Fiction ». La langue se renseigne sur la
    fiche du livre et se retrouve avec le filtre **Langue** du catalogue. Une
    classification par langue multiplierait les lignes sans rien apporter.

## Le code de classification

C'est la version courte du nom, celle qui tient sur une étiquette de
tranche. Pour « Jeunesse Documentaire », on écrit `JE DOC`.

Il vaut pour **toutes** les notices de la classification : une seule saisie,
et deux livres de la même classification ne pourront jamais afficher deux
codes différents.

À l'installation, les classifications fournies reçoivent un code de
départ (`JE DOC`, `AD FIC`…). Vous pouvez les remplacer par les vôtres :
BibliOfelia ne réécrira jamais un code que vous avez saisi.

Une fois les codes en place, imprimez les
[étiquettes de tranche](../impressions/etiquettes.md).

## Supprimer une classification

**Aucun livre n'est supprimé.** Les notices concernées se retrouvent
simplement sans classification, et l'écran de confirmation vous dit combien
elles sont. Vous pourrez leur en réaffecter une avec les
[opérations en lot](operations-lot.md).

## Voir aussi

- [Opérations en lot](operations-lot.md)
- [Imprimer les étiquettes](../impressions/etiquettes.md)
