# FEAT-013 — Notifications offline + alertes

Statut : DONE (validé Val 2026-05-22)
SPEC : §6.8

## Contexte

Le système est intégralement offline : pas d'email, pas de SMS. Les
alertes sont des éléments d'interface affichés à l'identification d'un
usager (retards, réservations à retirer, carte expirante) + des listes
imprimables pour relance manuelle + des compteurs permanents dans la
barre de navigation.

## Implémentation

### `apps/members/notifications.py`

Module centralisé pour calculer les alertes :

- `MemberAlert(level, message)` — niveau ∈ {`info`, `warning`, `error`}.
- `member_alerts(member)` — liste des alertes pertinentes :
  - prêts en retard (count)
  - réservations à retirer (count)
  - carte expirée (jours dépassés) ou expirante (≤ 30 j).
- `navbar_counts()` — compteurs pour la barre de nav (retards globaux +
  réservations prêtes globales).

### Intégration

- `apps/loans/views.py:lend` : utilise `member_alerts` (refacto, l'ancien
  helper local `_member_alerts` est supprimé).
- `apps/members/views.py:member_detail` : passe les alertes au template
  qui affiche un bandeau par alerte (niveau ⇒ classe CSS `msg-*`).
- `apps/core/context_processors.py:notifications` : délègue à
  `navbar_counts()` (refacto idempotent).

### Liste imprimable des réservations prêtes

- `apps/reports/services.py:reservations_ready_for_pickup`.
- Vue `reports:reservations_pickup` + template imprimable
  `templates/reports/reservations_pickup.html` (style `@media print`).

## Décisions

- **Pas de modèle Notification persistant** en v1. Les alertes sont
  recalculées à la demande (la BD est petite, requêtes < 50 ms). Si on
  veut un historique, on basculera sur un modèle dédié quand le
  scheduler tournera (Task #14 backup hourly est déjà actif).
- **Niveau d'alerte** mappé sur les classes CSS existantes (`msg-info`,
  `msg-warning`, `msg-error`) ; `msg-info` ajouté au CSS.
- **Pas d'expiration globale dans la nav** : `navbar_counts` ne renvoie
  que retards + réservations (le badge « cartes expirantes » serait
  bruyant et le wizard de fin de cycle de vie le couvre déjà via
  `expire_members`).
