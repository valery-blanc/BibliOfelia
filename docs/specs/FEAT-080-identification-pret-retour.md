# FEAT-080 — Identifier complètement le livre et l'usager au prêt et au retour

**Statut** : DONE
**Sprint** : 30
**Demande** : Val, 2026-08-23, après le test physique du code externe
`BCF132770013` sur `grand-saconnex` :

> page prêt : quand on a scanné le livre (avec son code barre interne ou
> externe) il faut afficher le titre + auteur du livre + code ofelia + code
> externe. page retour […] il faut afficher le nom/prénom de la personne qui
> retourne le livre, le titre et l'auteur du livre, le n° ofelia, le n° externe
> et un message indiquant que le retour a été effectué.
>
> pour la personne qui retourne le livre il faut afficher nom, prénom, age sexe
> photo (si ces info sont présentes)

## Contexte

Le test de FEAT-063 (codes Ofelia externes) a mis le doigt sur un manque plus
ancien : les deux écrans du comptoir affichaient un titre et le **code interne**
(`OFL-…`), c'est-à-dire l'identifiant que personne ne lit. Avec deux codes
possibles par exemplaire, le bibliothécaire ne pouvait plus vérifier qu'il avait
scanné le bon livre sans rouvrir sa fiche. Et au retour, la personne debout en
face de lui n'était nommée nulle part.

## Comportement

### Écran de prêt — panier

Chaque ligne du panier affiche désormais :

- le **titre** de la notice ;
- le ou les **auteurs** ;
- le **code Ofelia** (EAN13 `290…`) ;
- le **code externe**, s'il existe.

Les deux codes sont montrés quel que soit celui qui a été scanné : on ne sait
pas lequel le bibliothécaire a sous les yeux, et l'intérêt est justement de
vérifier qu'ils désignent bien le même livre. Ils sont rendus en pastilles
monospace (`.code-chip`), le code externe dans une teinte distincte.

Le code interne `OFL-…` disparaît de cette ligne : il n'est imprimé sur aucune
étiquette (`_draw_roll_item_label` ne pose que l'EAN13, décision Val) et ne sert
donc à rien au comptoir.

### Écran de retour — journal de la séance

Chaque ligne du journal affiche :

- **qui rapporte le livre** : photo (ou une pastille neutre si absente), **nom**,
  **prénom**, et **âge** s'il est calculable — le tout cliquable vers la fiche
  usager ;
- le **titre** et le ou les **auteurs** ;
- le **code Ofelia** et le **code externe** ;
- une mention explicite de l'issue : « Retour effectué », « Retour effectué —
  livre perdu réintégré au fonds », ou « Aucun prêt actif — rien à solder ».

Le badge de droite (En retard / À temps / réservation) est conservé.

Le message flash devient lui aussi nominatif : « Retour effectué : *titre*,
rendu par *Prénom Nom*. »

### Le sexe de l'usager n'est pas affiché

`Member` **n'a pas de champ sexe**. Seules les personnes rattachées à une carte
en ont un (`MemberFamilyMember.gender`, FEAT-072), et ce ne sont pas elles qui
empruntent. La demande dit « si ces info sont présentes » : l'information
n'existant pas en base, il n'y a rien à afficher. L'ajouter supposerait un champ
sur tous les usagers, une migration et une donnée personnelle de plus à
collecter — **décision à prendre par Val**, hors périmètre de ce correctif.

## Spec technique

### `apps/loans/services.py`

`ReturnResult` transporte le **prêt soldé** (`loan: Loan | None`). Sans lui, la
vue n'a aucun moyen de retrouver l'emprunteur : au moment où elle reprend la
main, le prêt est déjà passé en `returned`.

Cas du livre perdu réintégré : le prêt était soldé par un `update()` de masse
qui ne renvoie aucun objet. Il est désormais **lu avant** d'être mis à jour,
sinon la réintégration serait le seul retour incapable de nommer l'emprunteur.

### `apps/members/models.py`

Nouvelle propriété `Member.age` — âge en **années révolues**, `None` sans date de
naissance. Elle décompte l'anniversaire pas encore passé, contrairement à
`MemberFamilyMember.age` qui n'a qu'une année de naissance et approxime : ici la
date complète est connue, un usager né en décembre ne doit pas paraître un an
plus vieux pendant onze mois.

### `apps/loans/views.py`

- `lend` : `prefetch_related("record__authors")` sur le panier (sinon une requête
  par livre scanné).
- `_process_return` : `prefetch_related("record__authors")` sur la résolution, et
  l'entrée de journal porte `authors`, `ean13`, `external_code`, `member_*`.

**Le journal vit en session (JSON).** Les entrées écrites avant cette version
n'ont pas les nouvelles clés : le gabarit teste la présence de chacune et se
rabat sur `internal_id` pour le code. Un test le vérifie.

### Gabarits

`templates/loans/lend.html`, `templates/loans/return.html` : classes `.code-chip`
et `.returner*`, définies localement dans chaque page.

## Correctif de gabarit rencontré au passage

Trois commentaires ont d'abord été écrits en `{# … #}` **à cheval sur deux
lignes**. Vérifié dans un conteneur : le lexer Django (`tag_re`) n'active pas le
drapeau `DOTALL`, un tel commentaire n'en est donc pas un et **s'affiche en clair
dans la page**. Tous repassés en `{% comment %}`, et un test interdit désormais
que `FEAT-080` ou `{#` apparaisse dans le HTML rendu des deux écrans.

## Impact

- Aucune migration : `Member.age` est une propriété calculée.
- `ReturnResult` gagne un champ optionnel — les appelants existants sont
  inchangés.
- Aucun effet sur l'API, le récolement ou le catalogage.

## Tests

`apps/loans/tests/test_lend_return_display.py` — 13 tests : âge en années
révolues et absence de date de naissance, panier affichant titre + auteur + les
deux codes **quel que soit le code scanné** (paramétré), exemplaire sans code
externe, retour complet (titre, auteur, nom, prénom, âge, deux codes, message),
contenu de l'entrée de journal, `ReturnResult.loan` renseigné, réintégration d'un
livre perdu nommant encore l'emprunteur, retour sans prêt actif (aucun nom, et le
journal le dit), usager sans photo ni date de naissance, entrée de journal
antérieure à FEAT-080, et le garde-fou anti-commentaire cassé.
