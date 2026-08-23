# FEAT-081 — Une ancienne carte d'usager reconnue partout

**Statut** : DONE
**Sprint** : 30
**Demande** : Val, 2026-08-23 — « quand je scan ma carte de membre depuis la
home page ou depuis la page de membres il ne me reconnait pas 2910000000017 »

## Ce qui se passait réellement

Enquête sur l'instance `grand-saconnex` (un seul usager en base) :

| Fait | Valeur |
|---|---|
| Carte courante | `2919000000003` |
| Ancienne carte (`replaces_card_number`) | `2910000000017` — celle qui était scannée |
| Inscription de l'usager | 2026-08-18 |
| Remplacement de la carte | **2026-08-20 à 14:02 UTC** (16:02 CEST) |

Le compteur `Setting.next_replacement_card_seq` est passé de sa valeur par
défaut `900 000 000` à `900 000 001` à cet horodatage : `replace_card()` a donc
été exécutée **une fois**, le 20 août. `2910000000017` est le numéro attribué
automatiquement à la création (`build_ean13("291", pk=1)`), `2919000000003` le
premier numéro de la plage des cartes de remplacement.

`replace_card()` n'est appelable que depuis le bouton **« Remplacer la carte »**
de la fiche usager (POST, derrière un `confirm()`). Il n'existe aucun autre
chemin — ni impression, ni édition, ni commande.

**Le vrai défaut n'est donc pas la résolution du code, mais deux trous autour :**

1. **Rien ne dit qu'il faut réimprimer.** Le numéro change en base, la carte
   physique dans la poche de l'usager porte encore l'ancien. Le décalage se
   découvre au comptoir, des jours plus tard.
2. **Les écrans ne répondaient pas pareil.** L'écran de prêt acceptait déjà
   l'ancienne carte (`replaces_card_number`), la recherche de l'accueil et la
   liste des usagers non. Le même code-barres ouvrait la fiche au prêt et ne
   rendait rien ailleurs.

## Comportement

### Résolution unifiée

Nouveau module `apps/members/lookup.py`, pendant de
`apps.catalog.lookup.find_item` pour les exemplaires :

- `find_member(raw, queryset=None)` — carte **courante** d'abord, puis
  **ancienne carte**. Normalise la saisie (`normale_code` : casse, tirets,
  espaces). L'ordre compte : si un numéro était à la fois carte courante d'un
  usager et ancienne carte d'un autre, c'est le **porteur actuel** qui gagne.
- `is_replaced_card(member, raw)` — vrai si `raw` est l'ancienne carte, pour
  prévenir le bibliothécaire.

Utilisé par les **trois** écrans :

| Écran | Avant | Après |
|---|---|---|
| Recherche de l'accueil (`core:search`) | carte courante seule | `find_member` + avertissement |
| Liste des usagers (`members:list`) | `card_number__icontains` | `+ replaces_card_number__icontains` |
| Prêt (`loans:lend`) | les deux, en code dupliqué | `find_member` + avertissement |

### Avertissement « carte remplacée »

Quand la résolution passe par l'ancienne carte, un message d'information
s'affiche : « Carte remplacée : *ancien n°*. *Prénom Nom* utilise désormais la
carte n° *nouveau n°*. » Sans ce signal, une carte périmée continuerait de
fonctionner sans que personne ne s'aperçoive qu'elle n'aurait plus dû circuler.

### Rappel de réimpression

`members:replace_card` ajoute un avertissement après le message de succès : la
carte en circulation porte encore l'ancien numéro, il faut imprimer la nouvelle
et la remettre à l'usager. C'est exactement la situation qui a produit ce
ticket.

## Spec technique

- `apps/members/lookup.py` (nouveau).
- `apps/core/views.py` — `global_search` passe par `find_member`. Le module
  n'importait ni `messages` ni `gettext` : les deux sont ajoutés (la recherche
  ne parlait à personne, elle ne faisait que rediriger).
- `apps/members/views.py` — `member_list` étend le `Q()` ;
  `member_replace_card` avertit qu'il faut réimprimer.
- `apps/loans/views.py` — `set_member` abandonne son doublon au profit de
  `find_member`.

Aucune migration : `replaces_card_number` existe déjà.

## Ce qui n'a pas été fait

**Le bouton « Remplacer la carte » n'a pas été touché.** Il est voisin de
« Renouveler la carte » — deux boutons fantômes identiques dont l'un prolonge la
validité et l'autre invalide le numéro — et son `confirm()` est facile à
valider sans lire. C'est un candidat sérieux à un durcissement (libellé plus
explicite, message de confirmation nommant le numéro qui va être désactivé),
mais c'est un changement d'UX à arbitrer, pas un correctif : **décision Val**.

## Tests

`apps/members/tests/test_card_lookup.py` — 13 tests : résolution par carte
courante, par ancienne carte, avec séparateurs, numéro inconnu et chaîne vide,
priorité du porteur actuel sur l'ancienne carte d'un autre, `is_replaced_card`,
et surtout **les trois écrans qui répondent pareil au même code** (accueil avec
et sans avertissement, liste des usagers, prêt), le rejet d'une carte inconnue
toujours en place, et le rappel de réimpression après remplacement.
