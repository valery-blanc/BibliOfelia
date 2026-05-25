# FEAT-036 — Flag « notifié » sur les réservations + cadre dashboard

**Status:** DONE
**Date:** 2026-05-25

## Context

La bibliothécaire notifie les membres **par téléphone** que leur livre les attend (pas d'internet côté membre). Aujourd'hui, rien ne trace cette action : impossible de savoir si la personne a déjà été contactée. Sur la page `/loans/reservations/`, il manque aussi le code Ofelia de l'exemplaire mis de côté, l'heure de mise de côté, et la date avant laquelle le livre doit être retiré.

## Behavior

### Modèle

Ajouter `Reservation.notified_at` (`DateTimeField`, nullable). Quand non-null, signifie « le bibliothécaire a appelé le membre pour lui dire que son livre est prêt ».

### Page /loans/reservations/

Section « Prêtes à retirer » enrichie pour chaque ligne :
- Titre du livre (police plus grande)
- **Code Ofelia** de l'exemplaire mis de côté (le couple membre ↔ exemplaire est fixe une fois la mise de côté faite — les exemplaires ne sont pas interchangeables).
- Nom du membre + n° de carte (police plus grande)
- Date + heure de la réservation initiale (`created_at`)
- Date + heure de la mise de côté (`ready_since` rendu en datetime — voir note ci-dessous)
- Date avant laquelle le livre doit être retiré (`ready_since + pickup_hold_days`, date sans heure)
- Bouton **« Notifier le membre »** → POST `loans:reservation_notify` → set `notified_at = now()`. Si déjà notifié : badge « ✓ Notifié le … » non cliquable.
- Bouton « Annuler »

Note `ready_since` : actuellement `DateField`. Pour l'heure de mise de côté, on garde `ready_since` (date) pour rétrocompatibilité + on lit `Reservation.fulfilled_by_loan.return_date` quand il existe (la mise de côté est faite lors du `return_item` qui met `loan.return_date = timezone.now()`). À défaut, on retombe sur `ready_since` (00:00). Solution simple, pas de migration de données.

Section « En attente » : ajout du code couleur pour position dans la file (1, 2, 3) — déjà calculée mais pour l'instant tout le monde était affiché « Pos. 1 ». Bug à corriger en passant.

### Dashboard

Nouveau cadre « Notifications à faire » placé **entre la grille de tuiles et la bannière scan** :
- Visible uniquement si au moins une réservation `READY_FOR_PICKUP` non encore notifiée existe.
- Pour chaque réservation : nom du membre, n° de carte, titre du livre.
- Bouton « Notifier » par ligne (même endpoint `loans:reservation_notify`).
- Lien « Voir tout » vers `/loans/reservations/`.

Visible uniquement pour les rôles `librarian` / `superadmin`.

## Technical spec

1. **Migration** : `apps/loans/migrations/0002_reservation_notified.py` ajoute `notified_at = models.DateTimeField(null=True, blank=True)`.
2. **Service** : `apps/loans/services.py:mark_reservation_notified(reservation, by_user)` (transaction, set `notified_at = timezone.now()`, idempotent — pas d'erreur si déjà notifié).
3. **Vue** : `apps/loans/views.py:reservation_notify_view` (POST, require role write). Redirige vers `next` (param URL) ou liste réservations.
4. **URL** : `loans:reservation_notify` → `<pk>/notify/`.
5. **Template** : `templates/loans/reservations.html` réécrit la section ready, augmente la police (`font-size: 16px` titre, `15px` corps).
6. **Dashboard** : `apps/core/views.py:dashboard` injecte `notifications_pending = Reservation.objects.filter(status=READY_FOR_PICKUP, notified_at__isnull=True).select_related("record","member","fulfilled_by_item")`.
7. **Template dashboard** : nouveau bloc avant le scan-banner.

## Impact on existing code

- `apps/loans/models.py` : nouveau champ
- `apps/loans/migrations/0002_reservation_notified.py` : nouvelle migration
- `apps/loans/services.py` : `mark_reservation_notified`
- `apps/loans/views.py` : nouvelle vue + import
- `apps/loans/urls.py` : nouvelle route
- `apps/loans/admin.py` (si présent) : exposer `notified_at`
- `templates/loans/reservations.html` : refonte ligne ready + ajout bouton notifier
- `apps/core/views.py:dashboard` : injection
- `templates/core/dashboard.html` : nouveau cadre
- `SPEC §6.4` + §6.6 : ajout
- Tests : `apps/loans/tests/test_sprint11.py`
