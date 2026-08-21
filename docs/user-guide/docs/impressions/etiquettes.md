# Imprimer les étiquettes de livres

Les étiquettes-codes-barres se collent sur les livres pour permettre
leur scan rapide. BibliOfelia génère le PDF des étiquettes à imprimer
sur planches autocollantes.

## Ouvrir la page d'impression

**Avancé → Impressions →
[Étiquettes](/bibliofelia/fr/printing/labels/){ target="_blank" }**.

![Page de sélection des étiquettes](../assets/screenshots/fr/impressions/labels-picker.png)

## Choisir les exemplaires

La liste affiche tous les exemplaires sans étiquette imprimée.
Filtrez et cochez ceux à inclure dans le PDF.

Vous pouvez aussi imprimer des étiquettes pour des exemplaires déjà
imprimés (par exemple si une étiquette est abîmée) en désactivant le
filtre "Non imprimés".

## Choisir la langue

Comme pour les cartes, la langue détermine les libellés sur
l'étiquette.

## Générer le PDF

Cliquez sur **Générer le PDF**. Le format des étiquettes est
**70 × 42 mm** (5 par ligne, 14 par planche A4 = 70 étiquettes par
page).

## Que contient une étiquette

- Logo OFELIA discret
- Titre du livre (sur 2 lignes max)
- Auteur(s) (sur 2 lignes max)
- Code interne et code-barres EAN-13
- Code de localisation (rayon)

## Conseils d'impression

- Utilisez des **planches d'étiquettes adhésives A4** format 70 × 42 mm
  (Avery L7163 ou équivalent)
- Vérifiez l'alignement avec une **impression test** sur papier ordinaire
  d'abord
- Si vous imprimez beaucoup d'étiquettes en série, prévoyez une étape
  de **collage** avec plusieurs personnes : c'est plus rapide à deux

## Où coller l'étiquette

La convention recommandée :

- **Livres reliés** : sur le quatrième de couverture, en bas à droite
- **Livres souples** : sur la couverture, en bas à droite
- **BD / Albums** : sur le quatrième de couverture, dans le coin le
  moins visible

Choisissez un emplacement constant pour tous vos livres : ça facilite
le scan pendant le [récolement](../inventaire/recolement.md).

## Imprimer sur une étiqueteuse à ruban (Brother QL-810W)

Si votre poste a une **Brother QL-810W** branchée en USB avec un ruban
continu de 62 mm, un second bouton apparaît : **Ruban 62 mm (Brother
QL)**. Il imprime une étiquette par étiquette, sans planche A4 et sans
chutes de papier.

1. Cochez les exemplaires, puis cliquez sur **Ruban 62 mm (Brother QL)**.
2. Le PDF s'ouvre dans un nouvel onglet. Lancez l'impression (**Ctrl+P**, ou
   le bouton d'impression du visualiseur).
3. Dans le dialogue : imprimante **Brother QL-810W**, papier **62 mm**,
   orientation **portrait**, échelle **100 %** (surtout pas « ajuster à la
   page »).

Chaque étiquette est imprimée sur sa propre page : l'imprimante coupe entre
chacune.

Chaque étiquette fait **62 × 35 mm** : logo et nom de la bibliothèque en haut,
titre sur deux lignes, auteur en italique, code-barres, puis code Ofelia et
code de rayon en bas.

!!! tip "L'étiquette sort entièrement en noir"
    Le rouge du ruban bicolore (DK-22251) est réservé aux cartes de membres.
    Sur une étiquette, le code-barres doit rester noir : une barre rouge n'est
    plus lue par la douchette.

## Les étiquettes de tranche

Une étiquette de tranche ne porte qu'une chose : l'**abréviation de la
catégorie** du livre, en très gros. Collée sur la tranche, elle se lit à un
mètre du rayon et permet de ranger un livre sans le sortir de l'étagère.

Sur la page **Étiquettes**, sélectionnez vos exemplaires puis cliquez sur
**Étiquettes de tranche**. Même ruban, même format que les étiquettes de
livres (62 × 35 mm, une étiquette par page).

Le texte est centré et sa taille s'adapte toute seule : `PER` remplit
l'étiquette, `RO FI ADO` se répartit sur deux lignes.

```
|--------------------------|
|          RO FI           |
|           ADO            |
|--------------------------|
```

!!! warning "Il faut d'abord renseigner l'abréviation"
    L'abréviation se saisit sur la **catégorie**, pas sur le livre (voir
    [Catégories](../catalogue/categories.md)). Un exemplaire dont la
    catégorie n'a pas d'abréviation est ignoré à l'impression ; si aucun
    n'en a, BibliOfelia vous le dit au lieu de sortir un PDF vide.

## Voir aussi

- [Gérer les exemplaires](../catalogue/exemplaires.md)
- [Récolement](../inventaire/recolement.md)
