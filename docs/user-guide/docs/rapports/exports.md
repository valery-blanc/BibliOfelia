# Imprimer et enregistrer un rapport

Tout ce qui s'affiche à l'écran peut être **imprimé en PDF** ou
**enregistré en Excel**. Rien n'est réservé à l'un ou à l'autre : ce que
vous voyez est ce que vous obtenez.

## Les deux boutons en haut de l'écran

En haut de chaque rapport, à gauche :

- **Imprimer (PDF)** — le rapport entier, mis en page, avec le logo et le
  nom de la bibliothèque. C'est le document à tendre à un donateur ou à
  joindre à un dossier de subvention.
- **Fichier Excel** — le même rapport, chiffres et graphes, dans un
  classeur. Un onglet par tableau, et le graphe posé à côté de ses données.

Les deux reprennent la **période** et les **réglages** affichés à l'écran :
si vous regardez « 2025 », le fichier porte sur 2025.

## Un seul tableau, pas tout l'écran

Sous le titre de chaque tableau, deux petits liens : **PDF** et **Excel**.
Ils n'exportent que **ce tableau-là**.

Utile quand vous voulez la seule liste des factures impayées sans sortir
les huit tableaux de l'écran « L'argent ».

!!! tip "Retrouver un tableau"
    La page [Tous les rapports](liste.md) liste tous les écrans et tous
    leurs tableaux, avec un lien direct vers chacun.

## Sortir toutes les colonnes (CSV)

Les écrans [Le fonds](/bibliofelia/fr/reports/collection/){ target="_blank" }
et [Les prêts](/bibliofelia/fr/reports/loans/){ target="_blank" } proposent,
tout en bas, des fichiers **CSV**.

Ce ne sont pas des rapports : ils ne sont ni mis en page ni commentés, mais
ils sortent **toutes** les colonnes de la base — bien plus que ce que le
tableau affiche.

| Fichier | Ce qu'il contient |
|---|---|
| Catalogue complet | Une ligne par exemplaire : ISBN, éditeur, année, tags, résumé, provenance, emplacement… |
| Prêts et réservations en cours | La situation d'aujourd'hui, prêts et réservations dans un même fichier |
| Les prêts de la période | Tous les prêts de la période affichée en haut de l'écran |

Utile pour : un **inventaire annuel**, le partage de votre fonds avec une
autre bibliothèque, ou un calcul que BibliOfelia ne fait pas.

## Comment ouvrir un CSV

1. Cliquez sur le lien
2. Le fichier `.csv` se télécharge
3. Ouvrez-le dans LibreOffice Calc, Excel ou Google Sheets

Les colonnes sont séparées par des **virgules**. Tous les caractères
accentués (à, é, è, ô, ï…) s'affichent correctement dans LibreOffice Calc
et Google Sheets.

!!! tip "Si Excel ouvre tout dans une seule colonne"
    Excel français attend par défaut le point-virgule comme séparateur.
    Utilisez **Données → Depuis le texte/CSV** et indiquez « virgule »
    comme séparateur — vos colonnes apparaîtront correctement.

## Et le rapport annuel ?

C'est la [Vue d'ensemble](/bibliofelia/fr/reports/overview/){ target="_blank" }
avec la période **2025** ou **2026** : tous les chiffres importants sur une
page, comparés à l'année précédente. Imprimez-la en PDF.
