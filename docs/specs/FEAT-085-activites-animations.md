# FEAT-085 — Activités et animations

**Status:** DONE
**Date:** 2026-08-31

## Contexte

Demande Val (`temp.txt`, 2026-08-31). BibliOfelia sait tout du catalogue et des
prêts, et **rien du travail des employés**. Impossible de répondre en fin
d'année à « combien d'animations avons-nous organisées, et qui est venu ? » —
alors que c'est exactement ce qu'un bailleur demande.

But affiché par Val : produire une phrase comme « cette année, la bibliothèque
a organisé *x* animations auxquelles ont participé *y* membres et *z*
non-membres, dont *t* adultes et *s* enfants ».

## Comportement

### Activités

Chaque employé saisit ce qu'il a fait et **le temps passé** : administration,
rangement, accueil, animation… Les natures d'activité viennent d'une **liste
administrable** (ajout, renommage, désactivation). Une activité désactivée
disparaît du formulaire mais reste dans les saisies passées et dans les
statistiques — sinon désactiver une ligne réécrirait l'histoire.

### Animations

Chaque employé saisit les animations qu'il a présentées : intitulé, temps
passé, et **qui était là**.

- **Membres présents** : retrouvés en scannant leur carte **ou** en tapant les
  **4 derniers chiffres** de leur numéro de membre. La résolution passe par
  `apps/members/lookup.py` — carte courante puis ancienne carte (FEAT-081) —
  étendue aux 4 derniers chiffres. Une saisie de 4 chiffres qui désigne
  **plusieurs** usagers affiche la liste et demande de choisir : deviner ferait
  compter la mauvaise personne.
- **Non-membres** : simplement comptés, *x* adultes et *y* enfants.
- L'intitulé se choisit dans une liste administrable, mais **l'animateur peut
  en ajouter un** en texte libre depuis son formulaire — c'est le seul
  référentiel que le rôle bibliothécaire enrichit tout seul, parce qu'une
  animation s'invente le jour même.

### Saisie rétroactive

Activités et animations portent une **date modifiable** : un employé qui a
oublié de saisir sa journée la rattrape plus tard. La date est bornée à
aujourd'hui — on ne saisit pas le travail de demain.

### Statistiques

Écran `/closing/stats/` : totaux mois par mois et pour l'année — nombre
d'animations, participants membres, non-membres adultes, non-membres enfants,
et temps passé par nature d'activité. Export CSV.

## Spécification technique

Nouvelle application `apps/closing` (elle porte aussi FEAT-086).

```
ActivityType(label, is_active, order)
ActivityEntry(user, occurred_on, activity_type, minutes, note, created_at)
AnimationType(label, is_active, created_by)
AnimationSession(occurred_on, animation_type, presenter, minutes,
                 non_member_adults, non_member_children, note, created_at)
AnimationAttendance(session, member)      # unique_together
```

- `minutes` en `PositiveIntegerField` : la saisie se fait en heures + minutes
  dans le formulaire, le stockage reste en minutes — une durée en décimal se
  prête aux arrondis, pas une durée en minutes.
- `AnimationSession.presenter` et `ActivityEntry.user` en `PROTECT` : un
  employé supprimé emporterait les statistiques de l'année avec lui.
- `AnimationType.label` unique : l'ajout libre par l'animateur produirait sinon
  « Heure du conte » et « heure du conte » comptés séparément — la recherche
  d'un intitulé existant est insensible à la casse avant création.
- Résolution des présences : `apps/members/lookup.py::find_members_by_code()`
  (carte complète **ou** 4 derniers chiffres) à côté de `find_member`,
  conformément à la règle « un code résolu quelque part doit l'être partout ».

Rôles : saisie ouverte à `LIBRARIAN`/`SUPERADMIN` ; référentiel des activités
`SUPERADMIN` ; statistiques également en `READONLY`.

## Impact sur l'existant

- `apps/members/lookup.py` : nouvelle fonction de recherche par suffixe.
- Accueil : tuile « Bouclement » (FEAT-086) qui mène à la saisie.
- Aucun modèle existant modifié.
