# BUG-042 — Changer de catégorie ne recalcule pas la cotisation

**Status:** FIXED
**Date:** 2026-09-03

## Symptôme

Signalé par Val (2026-09-03), en testant FEAT-089 sur Grand-Saconnex : création
d'une catégorie **EMPLOYE** à cotisation 0, puis passage de la fiche usager
`/fr/members/1/` dans cette catégorie. L'encadré Compte affiche encore
**« Cotisation 20 CHF »**.

## Reproduction

1. Catégorie Adulte à 20 CHF ; usager inscrit (facture de cotisation émise).
2. Créer une catégorie à cotisation 0.
3. Modifier la fiche, choisir cette catégorie, enregistrer.
4. La fiche affiche toujours Cotisation 20 CHF.

## Cause racine

`create_membership_invoice()` n'est appelée qu'à **l'inscription** et au
**renouvellement de carte**. `member_edit` changeait `Member.category` et
s'arrêtait là.

L'encadré Compte (FEAT-084) ne lit pas `category.membership_fee`. Il ventile
les **factures ouvertes**. La facture Adulte de 20 CHF était toujours `open`,
donc « Cotisation 20 CHF » — alors que la catégorie courante est gratuite.

Ce n'est pas un cache, ni un défaut de saisie du 0 sur EMPLOYE.

## Correctif

`apps/finance/services.py::reconcile_membership_invoices()` :

- annule les factures ouvertes **uniquement cotisation**, **sans paiement**
  (une amende, ou un acompte, ne bougent pas) ;
- si la nouvelle catégorie a une cotisation > 0, en émet une nouvelle ;
- si le montant ouvert est déjà le bon, ne touche à rien.

Appelée depuis `member_edit` dès que `category_id` change.

Une facture déjà réglée n'est pas remboursée.

Les fiches déjà basculées avant le correctif (dont `/members/1/` sur
Grand-Saconnex) sont réalignées une fois au déploiement.
