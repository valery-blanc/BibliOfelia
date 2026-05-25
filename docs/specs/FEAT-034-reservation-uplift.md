# FEAT-034 — Compléments mécanisme des réservations

**Status:** DONE
**Date:** 2026-05-25

## Context

Demande de Val (temp.txt) : formaliser le mécanisme des réservations. La majeure partie est déjà implémentée par FEAT-009 (`apps/loans/services.py`, SPEC §6.4) :

- File FIFO au niveau notice (`Reservation.created_at`).
- Statut `RESERVED_FOR_PICKUP` sur l'exemplaire dès qu'une réservation devient `READY_FOR_PICKUP`.
- Blocage du prêt à un autre membre que le réservant (`check_item_loanable`).
- Expiration `pickup_hold_days` paramétrable → bascule automatique vers la réservation suivante (`expire_stale_reservations`).
- Création de réservation refusée implicitement si l'usager peut prendre directement un exemplaire disponible (workflow `loans/lend/` côté librarian).

Ce FEAT n'ajoute que **ce qui manque** : visibilité côté UI de la date d'expiration et du membre réservant sur la fiche notice, bandeau de relances de retrait sur la page Retour, et exposition des paramètres `reservation_expiry_days` / `pickup_hold_days` dans `/settings/`.

## Behavior

### Fiche notice (`catalog:record_detail`)

Pour chaque exemplaire en statut `RESERVED_FOR_PICKUP`, afficher en plus du badge actuel :
- Le n° de carte + nom du membre ayant la réservation `READY_FOR_PICKUP` qui retient l'exemplaire.
- La date d'expiration de la mise de côté = `ready_since + pickup_hold_days`.

### Page Retour (`loans:return_items`)

Nouvelle section « Relances réservations » : liste des réservations `READY_FOR_PICKUP` dont la date d'expiration est ≤ aujourd'hui + 2 jours (ou déjà dépassée). Permet au bibliothécaire d'identifier en un coup d'œil les membres à appeler pour qu'ils viennent retirer leur livre avant qu'il ne reparte au suivant.

### Paramètres (`core:settings_section` section `reservations`)

Nouveau formulaire `ReservationDefaultsForm` exposant :
- `reservation_expiry_days` (validité d'une réservation `PENDING` avant qu'elle ne meure sans avoir trouvé d'exemplaire), défaut 7.
- `pickup_hold_days` (durée de mise de côté `READY_FOR_PICKUP` avant bascule à la réservation suivante), défaut 5.

## Technical spec

1. **Annotation de l'exemplaire** : `apps/catalog/views.py:record_detail` annote chaque `item` réservé avec sa `Reservation` `READY_FOR_PICKUP` (`item.active_reservation` via assignation en Python, pas de prefetch fragile). Template `templates/catalog/record_detail.html` : afficher membre + expiration.
2. **Helpers** : `apps/loans/services.py:reservations_due_soon(within_days=2)` → queryset `Reservation` `READY_FOR_PICKUP` triées par date d'expiration croissante, accompagnée de la date calculée. Pas d'index dédié.
3. **Vue retour** : `apps/loans/views.py:return_items` injecte `reservations_due` dans le contexte.
4. **Settings** : `apps/core/forms.py:ReservationDefaultsForm` (KEY non utilisée → stockage direct `Setting.set("reservation_expiry_days", ...)` + `Setting.set("pickup_hold_days", ...)` pour rester compatible avec le code qui les lit aujourd'hui). Câblage dans `apps/core/admin_views.py` + template `templates/core/admin/settings_index.html`.

## Impact on existing code

- `apps/catalog/views.py` : ajout annotation
- `templates/catalog/record_detail.html` : ligne d'info réservation par exemplaire
- `apps/loans/services.py` : helper `reservations_due_soon`
- `apps/loans/views.py` : injection contexte retour
- `templates/loans/return.html` : nouvelle section
- `apps/core/forms.py` + `admin_views.py` : nouveau formulaire de paramètres
- `templates/core/admin/settings_index.html` : nouvelle section
- `apps/core/management/commands/seed_defaults.py` : les clés existent déjà, pas de migration nécessaire
- `SPEC_BIBLIOFELIA.md` §6.4 : ajout des sous-sections UI + paramètres
