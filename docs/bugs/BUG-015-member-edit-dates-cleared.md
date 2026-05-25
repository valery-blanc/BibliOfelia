# BUG-015 — Dates remises à 0 sur /members/<pk>/edit/

**Status:** DONE
**Date:** 2026-05-25

## Symptom

Sur `/members/<pk>/edit/`, les champs `birth_date`, `registration_date` et `expiration_date` apparaissent **vides** alors que le membre a bien ces valeurs en base. Si le bibliothécaire enregistre sans les ressaisir, elles sont effacées (passent à `None` ou rejettent le form selon le champ).

## Reproduction steps

1. Ouvrir `/fr/members/21/edit/`
2. Observer les inputs « Date de naissance », « Date d'inscription », « Date d'expiration »
3. Tous sont visiblement vides, alors que la fiche `/fr/members/21/` affiche bien les dates.

## Root cause

Django formate par défaut les `DateField` rendus via `forms.DateInput` selon le format de la locale active (FR : `25 mai 2026`). Or, le widget HTML5 `<input type="date">` n'accepte que le format ISO `YYYY-MM-DD`. Conséquence : la valeur est rendue mais le navigateur la rejette et affiche un input vide.

## Fix applied

Ajouter `format="%Y-%m-%d"` aux widgets `DateInput` du `MemberForm` (et de tout autre formulaire qui sortirait une date au format ISO HTML5 — vérifié, seul `MemberForm` est concerné).

## Spec section impacted

`SPEC §6.2` — édition usager : la fiche d'édition pré-remplit fidèlement les dates existantes.
