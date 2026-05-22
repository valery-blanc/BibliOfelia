# FEAT-009 — Réservations

Statut : **DONE — tests écrits, non exécutés** (2026-05-21)
Sprint : 2
Task : #9 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.4

## Périmètre

Logique dans `apps/loans/services.py`, vues dans `apps/loans/views.py`.

### Création

`loans:reservation_create` (depuis la fiche notice) — `create_reservation` :
`Reservation` `pending`, `expires_at` = aujourd'hui + `reservation_expiry_days`
(`Setting`, défaut 7).

### Satisfaction (FIFO)

`satisfy_reservations_for_item` — appelée à chaque retour d'exemplaire : la
réservation `pending` la plus ancienne sur la notice passe `ready_for_pickup`
(`ready_since`, `fulfilled_by_item`), l'exemplaire passe `reserved_for_pickup`.

Si l'usager prend en prêt un exemplaire d'une notice qu'il avait réservée, sa
réservation passe `fulfilled` (`_fulfil_reservation_on_loan`).

### Liste à honorer

`loans:reservations` — réservations prêtes + en attente, impression navigateur,
annulation possible (`cancel_reservation` libère l'exemplaire mis de côté et
sert la réservation suivante).

### Expiration

`expire_stale_reservations` :
- `pending` au-delà d'`expires_at` → `expired` ;
- `ready_for_pickup` non retirée au-delà de `pickup_hold_days` (`Setting`,
  défaut 5) → `expired`, l'exemplaire est libéré et passe à la réservation
  suivante.

`python manage.py expire_reservations` — à planifier quotidiennement (django-q2,
`Schedule` créé au paramétrage Task #15).

## Tests (`apps/loans/tests/`)

`test_services.py` : création, satisfaction FIFO, satisfaction au retour,
annulation libérant l'exemplaire, expiration. `test_views.py` : création,
liste, annulation.
