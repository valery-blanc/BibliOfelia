# FEAT-072 — Gestion des familles (remplace les enfants)

**Status:** DONE
**Date:** 2026-08-20

## Contexte

FEAT-066 a remplacé le compte parent par une liste d'**enfants**. Le test
terrain montre que c'est trop étroit : une carte sert souvent à toute une
maisonnée — conjoint, grands-parents, enfants. Demande Val (2026-08-20) :
parler de **famille**, et accepter des adultes comme des enfants.

## Comportement

La section « Enfants » de la fiche usager devient **« Famille »**. Chaque
personne rattachée à la carte est décrite par :

- **Prénom**
- **Sexe** (facultatif)
- **Adulte ou enfant** — pour un enfant, on saisit son **année de naissance**
  (l'âge est calculé et affiché) ; pour un adulte, on ne saisit rien d'autre.
- **Langues parlées** (mêmes cases que le titulaire)

L'année de naissance plutôt que l'âge : un âge saisi une fois devient faux
l'année suivante, une année de naissance reste vraie.

L'âge affiché est `année courante − année de naissance`. Approximation
assumée : la bibliothèque a besoin de savoir « environ 7 ans », pas de la date
d'anniversaire.

### Carte de membre

La carte imprimée gagne une **colonne de droite « Famille »** listant les
prénoms des personnes rattachées, un par ligne (décision Val 2026-08-20). La
colonne n'apparaît que s'il y a au moins une personne ; au-delà de ce que la
carte peut afficher, la liste est tronquée par « … ».

## Spec technique

- `MemberChild` renommé **`MemberFamilyMember`** (`related_name="family"`),
  `age` (entier) remplacé par `birth_year` (entier, nullable) et `is_adult`
  (booléen). Migration de données : `age` → `birth_year = année courante − age`
  pour les lignes existantes.
- `Member.family_first_names` : liste ordonnée des prénoms, utilisée par la
  carte et la fiche.
- `apps/printing/services.py` : `_draw_member_card` et `_draw_roll_member_card`
  reçoivent la colonne famille (largeur ~35 % de la carte, police réduite).
- Formset et libellés mis à jour ; l'ancienne règle « ligne sans prénom
  ignorée » est conservée.

## Impact sur l'existant

- `apps/members/models.py` (+ migration), `forms.py`, `views.py`, `admin.py`.
- `apps/printing/services.py`, tests d'impression.
- Templates `members/member_form.html`, `member_detail.html`,
  `member_confirm_delete.html`.
- FEAT-066 : la spec est amendée, pas remplacée (le modèle change de nom et de
  portée).

## Implémentation

- `MemberChild` → `MemberFamilyMember` (migration `members/0005`, **renommage**
  pour ne pas perdre les fiches saisies au Sprint 28) ; `age` → `birth_year`
  converti en migration de données, `is_adult` ajouté.
- `MemberFamilyMemberForm` : un champ `kind` (Adulte / Enfant) plutôt qu'une
  case à cocher — « adulte ou enfant » se lit mieux qu'une case « adulte ».
  Choisir « Adulte » efface l'année de naissance : garder une donnée qui ne sera
  jamais affichée ne rend service à personne.
- `Member.family_first_names` alimente les deux cartes.
- `family_column_lines()` extraite du dessin : le flux PDF de ReportLab ne se
  relit pas de façon fiable, la logique de troncature se teste directement.
- **Carte A4** : le bloc texte se décale à gauche **uniquement** quand il y a une
  famille. Sans ça, la colonne tronquait le nom (« Rakoto H… ») — vu au rendu
  300 dpi. Une carte sans famille garde exactement le rendu validé au Sprint 27.
- Tests : 7 cas dans `test_roll_printing.py`, plus les cas famille de
  `test_languages_and_children.py`.
