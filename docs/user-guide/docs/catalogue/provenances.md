# Provenances

Une **provenance** dit d'où vient un exemplaire : acheté par la
bibliothèque, donné par quelqu'un, prêté par une bibliothèque partenaire.

Elle est portée par l'**exemplaire**, pas par le livre. C'est important :
vous pouvez très bien avoir deux exemplaires du même titre, l'un acheté par
Ofelia, l'autre prêté par la médiathèque voisine.

## Créer une provenance

Depuis [**Avancé**](/bibliofelia/fr/advanced/){ target="_blank" }, ouvrez
**Provenances**, puis cliquez sur **Nouvelle provenance**.

- **Code** — court et sans espace : `OFELIA`, `BM-GE`, `DON-DUPONT`
- **Nom complet** — ce que verront les bibliothécaires dans les listes :
  « Prêt Bibliothèque de Genève »
- **Notes** — le contact, la date de restitution prévue, les conditions du
  dépôt

## Affecter une provenance

Trois façons, de la plus rapide à la plus ponctuelle :

1. **Au catalogage** — quand vous démarrez un lot de scan, choisissez une
   **Provenance par défaut** : tous les exemplaires du lot la recevront.
   C'est la bonne méthode pour un carton de livres prêtés.
2. **Depuis le catalogue** — cochez **Chercher les exemplaires**,
   sélectionnez les lignes voulues, puis **Affecter une provenance**.
3. **Un exemplaire à la fois** — le champ **Provenance** du formulaire
   d'exemplaire.

L'[import Excel](../inventaire/catalogage-excel.md) accepte aussi une
colonne `PROVENANCE`.

## Rendre un fonds prêté

C'est le cas qui justifie tout le reste :

1. Ouvrez le [**Catalogue**](/bibliofelia/fr/catalog/){ target="_blank" }
2. Cochez **Chercher les exemplaires**
3. Filtrez sur la provenance concernée
4. **Tout cocher**, puis **Supprimer les exemplaires sélectionnés**

Vous voyez la liste exacte avant de valider. Les exemplaires disparaissent,
les notices restent au catalogue.

!!! warning "Vérifiez les prêts en cours"
    L'écran de confirmation vous dit combien de ces livres sont chez un
    lecteur. Leur prêt sera clos en « perdu » — mieux vaut les récupérer
    avant, ou attendre leur retour.

## Supprimer une provenance

Tant qu'un exemplaire la porte, BibliOfelia **refuse** de la supprimer : ce
serait perdre la seule trace de l'origine de ces livres. L'écran vous
propose alors de voir les exemplaires concernés pour les traiter d'abord.

## Voir aussi

- [Gérer les exemplaires](exemplaires.md)
- [Recherche](recherche.md)
- [Cataloguer depuis Excel](../inventaire/catalogage-excel.md)
