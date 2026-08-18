# FEAT-058 — Consulter un lot de catalogage validé

**Status:** DONE
**Date:** 2026-08-03

## Context

Sur `/catalog/scan/`, les lots « En cours » ont un bouton « Continuer » qui mène
au hub. Les lots « Validés » n'avaient que « Étiquettes » : impossible de revoir
**quels livres** un lot contenait. Demande Val 2026-08-03 : « il faut un bouton
pour voir le contenu de la session (les livres trouvés) ».

C'est aussi le moyen de comprendre après coup ce qu'un lot a produit — par
exemple pour retrouver des notices arrivées sans titre.

## Behavior

- Liste des lots : chaque lot validé porte un bouton **« Voir le lot »** (à côté
  de « Étiquettes ») qui ouvre le hub du lot.
- Hub d'un lot validé : le bandeau « Ce lot a été envoyé au catalogue » est
  suivi du tableau des livres du lot, **en lecture seule** — auteur / titre /
  ISBN, langue, catégorie, emplacement, nombre d'exemplaires, et un bouton
  « Voir la notice » par ligne.
- Aucun formulaire d'édition, aucun bouton « Enregistrer » ni « Envoyer au
  catalogue » : un lot validé ne se re-finalise pas (décision Val : pas de
  réouverture, pour ne pas risquer de recréer des exemplaires déjà matérialisés).
- Lot validé sans ligne : « Ce lot ne contient aucun livre. »

## Technical spec

- `apps/catalog/views.py:scan_session` — chaque `ScanItem` reçoit
  `record_pk = processing_result["record_id"]`, l'identifiant de la notice
  réellement créée ou complétée par `finalize_scan_session`. Rien d'autre à
  charger : le résultat de finalisation est déjà stocké par item.
- `templates/catalog/scan_session.html` — la branche `{% if finalized %}` rend
  désormais le tableau de consultation.
- `templates/catalog/scan_session_list.html` — bouton « Voir le lot ».

Aucune migration, aucun changement de modèle.

## Impact on existing code

- La branche « lot ouvert » du hub est inchangée (scan, édition par lot, envoi).
- 3 chaînes i18n nouvelles (« Voir le lot », « Voir la notice », « Ce lot ne
  contient aucun livre. ») traduites EN/ES/MG.
- Tests : `test_finalized_hub_lists_items_read_only`,
  `test_session_list_links_to_finalized_batch`.
