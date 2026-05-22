# BUG-004 — Le récolement signale un exemplaire prêté comme manquant

**Statut** : FIXED
**Date** : 2026-05-22
**Sprint** : 2 (signalé par Val au test de fin de sprint)

## Symptôme

Dans le rapport de récolement, un exemplaire actuellement prêté à un usager
remontait dans la liste des « manquants », avec l'action « marquer perdu »
proposée — alors qu'il n'est ni manquant ni perdu, juste sorti en prêt.

## Cause racine

`scope_items` (`apps/inventory/services.py`) considérait comme « attendus » tous
les exemplaires non pilonnés, y compris les exemplaires `on_loan` (chez
l'usager). Non pointés au récolement — forcément, ils ne sont pas dans la
bibliothèque — ils étaient classés « manquants ».

## Fix

Le périmètre attendu (`scope_items`) se limite aux exemplaires censés être
physiquement présents : statut `available` ou `reserved_for_pickup`. Les
exemplaires `on_loan`, `lost`, `in_repair`, `discarded` sont exclus.

Test ajouté : `test_scope_excludes_on_loan_items`.

## Section spec impactée

§6.5 (Rapport) — précision du périmètre « attendu ». Mise à jour de la note
d'écarts Sprint 2 dans `SPEC_BIBLIOFELIA.md`.
