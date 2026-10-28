# FEAT-103 — Filtrer la personne d'une réservation

**Statut :** DONE
**Date :** 2026-10-28

## Contexte

Le formulaire « Réserver une notice » proposait toutes les personnes dans
une liste déroulante. En production, cette liste est trop longue pour
qu'on la fasse défiler.

## Comportement

- Au-dessus de la liste, un champ : **Tapez un nom pour filtrer**.
- Chaque mot saisi doit se trouver dans le nom. Les accents ne comptent
  pas (« elodie » retrouve « Élodie »). L'ordre des mots non plus
  (« jean dupont » retrouve « Dupont Jean »).
- La liste ne garde que les personnes qui correspondent. La personne
  déjà choisie reste, même si la frappe ne la contient plus.
- Entrée sélectionne la personne quand un seul nom correspond à la
  frappe. La flèche bas passe dans la liste.
- Le formulaire envoie l'identifiant de la personne, comme avant. Sans
  JavaScript, la liste complète reste utilisable.
- Le bouton **Réserver un livre** et les scans ISBN / code Ofelia ne
  changent pas.

## Fichiers

- `apps/loans/forms.py`
- `templates/loans/reservation_form.html`
- `static/js/member-picker.js`
- `static/css/ofelia.css`
- `docs/user-guide/docs/reservations/creer.md` et `.en.md`, `.es.md`, `.mg.md`

## Spec

SPEC §6.4.
