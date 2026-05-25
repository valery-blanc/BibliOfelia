# BUG-014 — Saisie clavier interceptée par le scan-handoff

**Status:** DONE
**Date:** 2026-05-25

## Symptom

Sur `/loans/lend/` et `/loans/return/`, l'utilisateur tape manuellement le n° de carte (ou le code Ofelia d'un livre) et appuie sur **Entrée** : au lieu de valider la saisie, l'application lance la séquence « ouverture caméra / fallback OfeliaScan ». Conséquence : impossible de saisir au clavier, le panier reste vide et le bouton « Prêter X livre(s) » de l'étape 3 n'apparaît jamais.

## Reproduction steps

1. Aller sur `/loans/lend/`
2. Cliquer dans le champ « Scanner ou saisir le n° de carte »
3. Taper un n° de carte au clavier
4. Appuyer sur Entrée

→ Le navigateur affiche le flash « Caméra interne indisponible … OfeliaScan utilisé en secours » (en HTTP / sans OfeliaScan, échec). Aucune soumission du formulaire.

## Root cause

Dans `templates/loans/lend.html` et `templates/loans/return.html`, le bouton « Scanner … » est à la fois `type="submit"` du formulaire **et** porteur de la classe `js-scan-handoff`. Quand l'utilisateur appuie sur Entrée dans un champ texte du formulaire, le navigateur déclenche l'**implicit form submission** en cliquant programmatiquement sur le 1er bouton submit. Le listener global de `static/js/scan-handoff.js` capte ce clic, appelle `ev.preventDefault()` puis lance la routine de scan → la soumission normale du formulaire est annulée.

## Fix applied

Découpler le rôle « lancer un scan » du rôle « soumettre le formulaire » :

- Le bouton scan passe en `type="button"` (ne déclenche plus la soumission au clavier).
- Un `<button type="submit" hidden>` est ajouté à chaque formulaire pour que la touche Entrée continue de soumettre la saisie manuelle (implicit submission).

Fichiers modifiés :
- `templates/loans/lend.html` — boutons « Scanner la carte » et « Scanner un livre »
- `templates/loans/return.html` — bouton « Enregistrer le retour »

Aucun changement de JS nécessaire : le listener `click` de `scan-handoff.js` reste piloté par le clic sur le bouton scan.

## Spec section impacted

`SPEC_BIBLIOFELIA.md` §6.3 — workflow Prêt / Retour : la saisie clavier reste toujours possible en parallèle du scan.
