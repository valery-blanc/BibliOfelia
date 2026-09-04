# FEAT-089 — Tarifs et Catégories d'usagers, un seul écran

**Status:** DONE
**Date:** 2026-09-03

## Contexte

Jusqu'ici les **catégories d'usagers** se gèrent dans Django admin
(`/admin/members/membercategory/`) et les **tarifs** (amendes, animations,
autres frais) dans Avancé → Tarifs (`/finance/tariffs/`). La cotisation, elle,
vit déjà sur `MemberCategory.membership_fee` (FEAT-084) — mais l'écran des
tarifs ne faisait que **l'afficher**, avec un renvoi vers l'admin.

Val : tout mettre sur la page des tarifs, renommée **« Tarifs et Catégories
d'usagers »**.

C'est aussi le dernier référentiel métier encore coincé dans `/admin/`
(les catégories de notices, langues, emplacements et provenances ont déjà
leur écran librarian). `/admin/` reste le filet de debug, pas l'outil du
bibliothécaire — `feedback_admin_django_scope`.

## Comportement

Un seul écran, SUPERADMIN comme le référentiel des tarifs :

1. **Catégories d'usagers** — table : code, nom, cotisation, validité, prêts
   max, durée de prêt, nombre d'usagers. Création / édition / suppression.
2. **Autres tarifs** — inchangé (nature, libellé, montant, actif).

Le formulaire de catégorie porte tout ce que l'admin exposait, plus la
cotisation qui n'y figurait même pas en `list_display` :

- code (unique, majuscules, sans espace)
- nom dans les **4 langues** (FR obligatoire ; EN/ES/MG facultatifs, repli
  modeltranslation vers le français)
- cotisation annuelle (0 = gratuit, aucune facture à l'inscription)
- validité de la carte en mois
- nombre max de prêts simultanés
- durée de prêt par défaut
- types de documents autorisés (cases ; **aucune cochée = tous autorisés**,
  c'est déjà la sémantique de `allowed_document_types` vide)

Suppression : `Member.category` est en **PROTECT**. Une catégorie qui a encore
des usagers ne se supprime pas — l'écran le dit et refuse le POST. Une
catégorie vide se confirme puis disparaît.

## Spécification technique

- `MemberCategoryForm` dans `apps/members/forms.py`
- vues `member_category_create` / `_edit` / `_delete` dans `apps/finance/views.py`
  — c'est la page tarifs qui les héberge, pas un nouvel écran usagers
- URLs sous `/finance/tariffs/categories/`
- gabarits `templates/finance/member_category_form.html` et
  `member_category_confirm_delete.html`
- `MemberCategoryAdmin` **conservé** (debug Claude / superadmin), plus le
  chemin normal

Pas de migration : tous les champs existent déjà (`members/0007` pour
`membership_fee`, `members/0002` pour les `name_<lang>`).

## Implémentation (2026-09-03)

- Formulaire `MemberCategoryForm` (`apps/members/forms.py`) : code normalisé
  en majuscules, 4 noms, cotisation, règles de prêt, cases à cocher
  `DocumentType` (vide = tout autorisé).
- Vues `member_category_create` / `_edit` / `_delete` dans
  `apps/finance/views.py`, URLs sous `/finance/tariffs/categories/`.
- Suppression : GET de confirmation ; POST refusé si `member_count > 0`
  (PROTECT), autorisé si la catégorie est vide.
- Tests : `apps/finance/tests/test_member_categories.py` (9 tests).
  Suite complète : **881 passed**.
- i18n : `scripts/translations_sprint32.py`, `i18n_check.py` = 0.
- Déployé : `grand-saconnex` et `sanjuan` (Fez, healthy) ; image reconstruite
  sur Avignon (secours).

## Impact

- Plus besoin d'ouvrir `/admin/` pour une cotisation ou une nouvelle catégorie.
- La phrase « se modifie dans l'administration des catégories d'usager » de
  l'écran tarifs disparaît.
- Lien Avancé → Administration : libellé aligné sur le nouveau titre.
