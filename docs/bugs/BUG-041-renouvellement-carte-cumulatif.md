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

- `can_renew(member)` — vrai si la carte expire dans 30 jours ou moins
  (`EXPIRY_WARNING_DAYS`, la même fenêtre que l'avertissement d'expiration
  déjà affiché), si elle est déjà expirée, ou si elle n'a pas de date.
- `renew_card()` lève `CardStillValid` sinon. **Le serveur refuse**, pas
  seulement l'interface : un POST direct ne doit pas non plus empiler.
- Le bouton de la fiche est `disabled` avec une infobulle donnant la date de
  validité — l'employé voit *pourquoi* il ne peut pas cliquer.
- `renew_card()` renvoie désormais `(date, facture)` et émet la cotisation.

## Section de spec impactée

`SPEC_BIBLIOFELIA.md` §6.2 — renouvellement de carte.
