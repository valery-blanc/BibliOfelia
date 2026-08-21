# FEAT-066 — Enfants rattachés à l'usager (remplace le compte parent)

**Status:** DONE
**Date:** 2026-08-19

## Contexte

Le champ `parent_account` rattachait un usager à un « compte collectif »
(école, famille). En pratique il n'a jamais servi : les enfants d'un usager
inscrit ne sont pas eux-mêmes des usagers, ils n'empruntent pas et n'ont pas de
carte. Ce dont la bibliothèque a besoin, c'est de savoir **qui** accompagne
l'adulte inscrit — pour proposer les bons livres.

Demande Val : supprimer `parent_account`, le remplacer par une liste d'enfants
décrits directement sur la fiche.

## Comportement

Le champ « Compte collectif parent » disparaît du formulaire et de la fiche.

Nouvelle section **« Enfants »** dans la fiche usager : autant de lignes que
d'enfants, chacune avec

- **Sexe** : Fille / Garçon / Autre (facultatif) ;
- **Prénom** ;
- **Âge** en années (0 à 25) ;
- **Langues** parlées : mêmes cases à cocher que l'usager (FEAT-065), plus le
  champ libre « autres langues ».

Ajout et suppression de lignes sans quitter le formulaire. Une ligne dont le
prénom est vide est ignorée à l'enregistrement — pas d'erreur bloquante pour un
formulaire à moitié rempli.

Supprimer un usager supprime ses enfants (ce ne sont que des données
descriptives de sa fiche).

## Spec technique

- Suppression du champ `Member.parent_account` (migration destructive, cf.
  ci-dessous).
- Nouveau modèle `MemberChild` : `member` (FK `CASCADE`, `related_name="children"`),
  `first_name` (80), `gender` (`f`/`m`/`x`, facultatif), `age`
  (`PositiveSmallIntegerField`, nullable), `languages` (JSON, mêmes codes que
  FEAT-065), `languages_other` (200). `ordering = ["first_name"]`.
- Formulaire : `inlineformset_factory(Member, MemberChild)`, `extra=1`,
  `can_delete=True`. Ajout d'une ligne en JS à partir du `empty_form`
  (pas de dépendance externe).

### Données existantes

`parent_account` est renseigné sur **1 usager de la Box** (jeu de démo) et sur
**0 usager** des instances san juan et grand-saconnex (relevé 2026-08-19). La
migration supprime la colonne : ce lien est perdu, c'est l'effet demandé.

## Impact sur l'existant

- `apps/members/models.py` (+ migration), `forms.py`, `views.py`
  (`member_delete` ne remet plus les dépendants à NULL), `admin.py`.
- Templates `members/member_form.html`, `members/member_detail.html`.
- `apps/members/tests/test_toggle_and_delete.py` (test du détachement des
  dépendants, devenu sans objet).

## Implémentation

- `Member.parent_account` supprimé (modèle, formulaire, admin, vues, fiche,
  page de suppression) ; modèle `MemberChild` créé — migration `members/0004`.
- `MemberChildFormSet` (`inlineformset_factory`, `extra=1`) rendu dans
  `member_form.html` : ajout de lignes par clonage de `empty_form` en JS, retrait
  par vidage de la ligne. CSS `.child-row` / `.child-langs`.
- `BaseMemberChildFormSet.clean` marque `DELETE` sur toute ligne sans prénom :
  une ligne laissée vide est ignorée, une ligne vidée est supprimée.

### Piège Django rencontré

Marquer `DELETE` **après** `super().clean()` est sans effet :
`BaseModelFormSet.clean()` appelle `validate_unique()`, qui lit la
`cached_property` `deleted_forms`. La ligne vidée était alors enregistrée avec
un prénom vide au lieu d'être supprimée. Les suppressions sont donc marquées
**avant** l'appel au parent (test de non-régression :
`test_clearing_the_first_name_removes_the_child`).

- Tests : 7 cas dans `apps/members/tests/test_languages_and_children.py` +
  `test_delete_removes_children` (ex-`test_delete_detaches_dependents`).
