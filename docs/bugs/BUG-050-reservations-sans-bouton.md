# BUG-050 — Aucun bouton pour réserver un livre

**Statut :** FIXED
**Symptôme :** la page Réservations liste les livres déjà réservés (notifier,
annuler, imprimer) mais ne permet pas d'en créer un. Le seul chemin était la
fiche d'une notice, ce qui n'est pas l'endroit où l'on vient pour réserver.

## Reproduction

1. Ouvrir **Réservations**.
2. Chercher un bouton pour réserver un livre. Il n'y en a pas.

## Cause

`loans:reservation_create` exige déjà une notice (`/reservations/new/<id>/`).
La page liste n'avait aucun lien vers ce formulaire, ni de recherche de livre.

## Correctif

Bouton **Réserver un livre** dans l'en-tête de la page. Il ouvre
`/loans/reservations/new/` : titre, auteur, ISBN ou code. Un code d'exemplaire
ouvre directement le choix du membre ; une recherche texte affiche les notices,
chacune avec **Réserver**.

La fiche notice garde son bouton **Réserver**.

## Spec

SPEC §6.4.
