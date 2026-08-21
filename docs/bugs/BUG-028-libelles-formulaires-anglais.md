# BUG-028 — Libellés de formulaire en anglais dans une interface française

**Status:** DONE
**Date:** 2026-08-21

## Symptôme

Sur `/fr/catalog/<pk>/edit/`, les libellés **Title**, **Language**, **Publisher**,
**Summary**, **Category**… s'affichent en anglais alors que l'interface est en
français (signalé par Val sur grand-saconnex).

## Reproduction

1. Ouvrir n'importe quelle notice → **Modifier**.
2. Les champs propres au formulaire (`Auteur(s)`, `ISSN`) sont bien traduits ;
   tous les autres sont en anglais.

## Cause racine

Quand un `ModelForm` ne fournit ni `labels` dans son `Meta`, ni `verbose_name`
sur le champ du modèle, **Django dérive le libellé du nom du champ Python** :
`title` → « Title », `publication_year` → « Publication year ». Cette chaîne est
fabriquée à la volée, elle ne passe pas par `gettext` : elle n'apparaît donc
**jamais** dans les fichiers `.po` et le gate i18n ne pouvait pas la voir.

Les champs déclarés explicitement dans le formulaire (`authors_text`, `issn`)
ont un `label=_()` — d'où le mélange constaté à l'écran.

## Ampleur

L'audit de tous les `ModelForm` du projet remonte **25 champs réellement en
anglais**, sur deux formulaires centraux :

- `BibliographicRecordForm` — 14 champs (toute la fiche notice) ;
- `MemberForm` — 11 champs (nom, prénom, date de naissance, téléphone, adresse,
  dates d'inscription et d'expiration…).

Les autres occurrences relevées sont des faux positifs : « Code », « Notes »,
« Description », « Parent », « Photo », « Provenance » s'écrivent pareil en
français et en anglais.

## Fix appliqué

`verbose_name=_()` posé sur les champs des modèles `BibliographicRecord`,
`Member`, `Category` et `Location`, plutôt que des `labels` dans chaque
formulaire : le libellé suit alors le champ partout — formulaires, `/admin/`,
messages d'erreur de validation — au lieu d'être à recopier dans chaque `Meta`.

## Garde-fou

`apps/core/tests/test_form_labels.py` parcourt **tous** les `ModelForm` du
projet, les instancie en français et échoue si un libellé est identique à la
dérivation anglaise de Django. Les quelques mots identiques dans les deux
langues sont listés explicitement dans le test, avec la raison — un ajout à
cette liste doit rester un geste conscient.

C'est le pendant du contrôle des `.po` : `i18n_check.py` vérifie que les chaînes
extraites sont traduites, ce test vérifie qu'elles sont bien **extraites**.

## Spec section impactée

SPEC §6.9 (Multilingue).

## Vérification

`verbose_name=_()` posé sur **41 champs** de `BibliographicRecord`, `Member`,
`Category`, `Location`, `Provenance`, `Language`, `MemberCategory`, `User`,
`InventorySession` et `InHouseConsultation` — migrations `catalog/0018`,
`catalog/0019`, `members/0006`, `accounts/0002`, `inventory/0004`, `loans/…`
(changements de métadonnées uniquement, aucune donnée touchée).

Cas particulier : le libellé d'un **ManyToMany** n'est pas dérivé du
`verbose_name` mais du `related_name` ; `tags` a donc reçu une entrée dans
`Meta.labels`.

Le garde-fou `test_no_form_label_is_left_in_english` compare la **nature** de
l'objet (`Promise` lazy) plutôt que les mots : un libellé passé par `gettext`
reste lazy jusqu'au rendu, un libellé fabriqué par Django est une `str`. On
évite ainsi de maintenir une liste de mots identiques en français et en anglais
(« Code », « Notes », « Date », « Tags »…) — et surtout de laisser passer un vrai
oubli qui se trouverait ressembler à du français.

L'audit a débusqué **8 champs supplémentaires** hors des deux formulaires
signalés (rôle et langue par défaut d'un utilisateur, nom et périmètre d'une
session de récolement, usager/date/nombre d'une consultation sur place).

## Audit élargi (question Val : « faut-il faire un tour complet du site ? »)

Le tour a été fait, automatiquement plutôt qu'à l'œil, sur les trois angles
morts que ni le gate `.po` ni le test des libellés ne couvraient :

| Angle mort | Trouvé | Suite |
|---|---|---|
| Texte français en dur dans un template, hors `{% trans %}` | 3 (tous dans `500.html`) | **exception justifiée** : `handler500` n'exécute ni les context processors ni le middleware de langue — la page porte ses textes en 4 langues en dur, c'était déjà documenté dans le template |
| `messages.*` / `ValidationError` / `help_text` sans `_()` | 0 | — |
| Libellés de `TextChoices` et `verbose_name` de `Meta` sans `_()` | 3 | **corrigés** : les 4 rôles utilisateur (`Bibliothécaire`, `Superadmin`…) et `Setting.Meta.verbose_name` |

Les rôles étaient le seul cas réellement visible par un bibliothécaire : ils
s'affichent dans le formulaire de création d'utilisateur.

`apps/core/tests/test_i18n_coverage.py` rejoue ces trois contrôles à chaque
`pytest`. Avec `test_form_labels.py` et `scripts/i18n_check.py`, les trois
maillons sont désormais tenus : la chaîne est **écrite** traduisible, elle est
**extraite**, et elle est **traduite**.
