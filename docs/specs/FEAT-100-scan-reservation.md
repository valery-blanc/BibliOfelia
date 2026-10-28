# FEAT-100 — Scan ISBN ou code Ofelia pour réserver

**Statut :** DONE
**Date :** 2026-10-26

## Contexte

Le bouton **Réserver un livre** (BUG-050) était dans l'en-tête de la page
Réservations, à droite du titre, à côté d'Imprimer. Il passait au-dessus de
la liste sans se voir. La recherche d'un livre à réserver n'avait pas le
scan caméra déjà présent sur le catalogue.

## Comportement

- Sur la page Réservations, **Réserver un livre** est un bouton large
  juste au-dessus de **Prêtes à retirer**. Imprimer reste dans l'en-tête.
- À côté de ce bouton, le scan caméra (`data-scan-kind="auto"`) accepte un
  ISBN ou un code Ofelia et ouvre la recherche avec `?q=`.
- Sur la page de recherche (`/loans/reservations/new/`), le même scan est
  à côté du champ. Il remplit le champ et lance la recherche. Un code
  d'exemplaire reconnu ouvre directement le choix du membre, comme une
  saisie exacte.

Pas de nouveau scanner : c'est le bouton `.js-scan-handoff` du catalogue.
Le bouton est `type="button"`.

## Fichiers

- `templates/loans/reservations.html`
- `templates/loans/reservation_pick.html`
- `static/css/ofelia.css` (`.reserve-start`, `.scan-field`)
- Guide `docs/user-guide/docs/reservations/creer.md` (+ `.en`, `.es`, `.mg`)
