# BUG-003 — Un même exemplaire peut être prêté deux fois

**Statut** : FIXED
**Date** : 2026-05-22
**Sprint** : 2 (signalé par Val au test de fin de sprint)

## Symptôme

Il était possible d'enregistrer un second prêt actif sur un exemplaire déjà
prêté — physiquement impossible, l'`internal_id` étant unique.

## Reproduction / cause racine

`check_item_loanable` (`apps/loans/services.py`) ne consultait que le **cache**
`Item.status`. Or ce cache peut diverger de la réalité si un `Loan` est créé
hors du service `create_loan` (ex. via `/admin/`, qui ne met pas à jour
`Item.status`). Constat sur la base de test : un exemplaire portait deux `Loan`
`active`, l'un créé sans bibliothécaire ni entrée d'audit (donc hors UI), avec
`Item.status` resté `available` — l'écran de prêt l'a donc accepté de nouveau.

## Fix

`check_item_loanable` interroge désormais la table `Loan` (source de vérité) :
si un `Loan` au statut `active`/`overdue` existe déjà pour l'exemplaire, le prêt
est refusé, quel que soit `Item.status`.

Test ajouté : `test_check_rejects_item_with_existing_active_loan`.

## Section spec impactée

§6.3 (workflow de prêt, étape 5). Comportement renforcé, pas de changement
fonctionnel attendu côté usage normal. Pas d'incrément de version spec.
