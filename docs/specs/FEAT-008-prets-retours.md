# FEAT-008 — Prêts, retours, renouvellements, livres perdus

Statut : **DONE — tests écrits, non exécutés** (2026-05-21)
Sprint : 2
Task : #8 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.3

## Périmètre

Toute la logique métier est dans `apps/loans/services.py` (testable hors HTTP).

### Prêt — workflow scan carte → scan livres → valider

`loans:lend` — workflow en 3 étapes, panier stocké en session
(`lend_member`, `lend_basket`) :

1. `set_member` — résout la carte (n° actuel ou `replaces_card_number`),
   affiche les alertes (retards, carte expirante, réservations à retirer).
2. `add_item` — scanne un EAN13, applique `check_item_loanable`.
3. `validate` — crée les `Loan`, passe les exemplaires en `on_loan`.

`check_item_loanable` (SPEC §6.3 étape 5) :
- exemplaire disponible (ou mis de côté pour cet usager) — sinon **erreur** ;
- type de document autorisé pour la catégorie — sinon **erreur** ;
- limite de prêts simultanés — sinon **erreur** ;
- réservation d'un autre usager sur la notice — **avertissement** (override
  possible, note saisissable à la validation).

`compute_due_date` : durée du type de document si définie, sinon de la catégorie
d'usager, sinon 21 jours.

### Retour

`loans:return_items` — scan des EAN13, chaque retour traité immédiatement,
journal de séance en session. `return_item` gère :
- retour normal → `Loan` `returned`, exemplaire `available` ;
- retard → note automatique ;
- retour différé d'un livre perdu → réintégration (exemplaire `available`, le
  `Loan` reste `lost`) ;
- satisfaction des réservations en attente (FIFO).

### Renouvellement

`renew_loan` — refusé si max atteint (`Setting max_renewals`, défaut 2) ou si
une réservation est en attente sur la notice.

### Livre perdu

`declare_lost` — `Loan` → `lost`, exemplaire → `lost`. Aucune facturation.

### Consultation sur place

`loans:consultation` — `InHouseConsultation` (usager optionnel, comptage),
sans modification du statut d'exemplaire.

## Écarts / décisions

- **Retour traité au scan** : pas de « validation finale » différée (SPEC §6.3) ;
  chaque scan est committé immédiatement, le journal de séance fait foi.
  Simplification assumée pour la v1.
- **Reçu papier** (§6.3 étape 8) : hors périmètre — impression Task #12.
- Exemplaire mis de côté pour un autre usager → **erreur** (pas d'override) ;
  l'override ne concerne que les réservations `pending`.
- **BUG-003** (corrigé) : `check_item_loanable` interroge la table `Loan`, pas
  seulement le cache `Item.status`, pour interdire tout double prêt. Message
  affiché : « Cet ouvrage est déjà prêté ». Les messages du moteur de prêt
  (`check_item_loanable`, `renew_loan`) sont passés en `gettext_lazy` et traduits
  dans les 4 langues.

## Tests (`apps/loans/tests/`)

- `test_services.py` : durée de prêt, toutes les branches de `check_item_loanable`,
  création de prêt, retour (normal / retard / réintégration / sans prêt),
  renouvellement (ok / max / bloqué par réservation), déclaration de perte.
- `test_views.py` : workflow de prêt complet, carte inconnue, exemplaire
  indisponible rejeté, retour, renouvellement, livre perdu, consultation.
