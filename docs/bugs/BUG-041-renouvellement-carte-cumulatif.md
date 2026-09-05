# BUG-041 — « Renouveler la carte » empile les années

**Status:** FIXED
**Date:** 2026-08-31

## Symptôme

Signalé par Val (2026-08-31) : « si on clique plusieurs fois ça ne devrait pas
rajouter plusieurs années de validité. Bouton à griser quand la carte est encore
valide. »

Trois clics sur « Renouveler la carte » repoussent l'expiration de trois ans,
sans aucun avertissement. Rien à l'écran ne dit que le bouton vient d'être
utilisé — le seul retour est un message de succès qui, lui, change à chaque fois.

## Reproduction

1. Ouvrir la fiche d'un usager dont la carte expire dans onze mois.
2. Cliquer « Renouveler la carte » trois fois de suite.
3. `expiration_date` est passée à ~3 ans et 11 mois.

## Cause racine

`apps/members/services.py::renew_card()` ancrait la nouvelle échéance sur
l'ancienne :

```python
anchor = max(date.today(), member.expiration_date or date.today())
member.expiration_date = anchor + relativedelta(months=months)
```

Cet ancrage est **juste** — renouveler une carte qui expire dans un mois doit
donner treize mois, pas douze. Ce qui manquait, c'est la condition d'entrée :
rien n'interdisait de renouveler une carte encore valable pour des mois.

Le défaut a pris de l'importance avec FEAT-084 : le renouvellement émet
désormais une **facture de cotisation**. Trois clics auraient produit trois
factures.

## Correctif

D'abord (Sprint 31) : bouton grisé si la carte est valable plus de
30 jours, `CardStillValid` côté serveur.

**FEAT-092 (Sprint 33, retour Val)** : le bouton a rejoint **Modifier**
et doit **toujours** fonctionner. `renew_card()` pose
aujourd'hui + durée de la catégorie. Un second clic le même jour ne
change pas la date et n'émet pas de seconde facture — plus besoin de
griser. `can_renew` et `CardStillValid` sont **supprimés**.
Message : « Nouvelle date d'expiration : jj/mm/aaaa ».

## Section de spec impactée

`SPEC_BIBLIOFELIA.md` §6.2 — renouvellement de carte.
