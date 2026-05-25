# FEAT-037 — Ergonomie formulaire membre (photo + expiration auto)

**Status:** DONE
**Date:** 2026-05-25

## Context

Trois irritants sur le workflow membre (Val 2026-05-25) :

1. La **photo** existe en base (`Member.photo`, `FileField upload_to=member_photos/`) mais n'est affichée nulle part — ni sur la fiche membre, ni sur le formulaire d'édition.
2. À l'**édition**, on aimerait que la date d'expiration soit recalculée automatiquement quand on touche à la date d'inscription (cas du renouvellement « manuel » via edit) — +1 an par défaut.
3. À la **création**, `registration_date` doit déjà valoir aujourd'hui (cas le plus fréquent : inscription du jour). Déjà géré côté form (`initial=date.today`) mais masqué par BUG-015 — sera de fait résolu par le fix BUG-015.

## Behavior

### Photo

- Sur la **fiche membre** (`templates/members/member_detail.html`), afficher la photo si elle existe, dans le `pagehead` à gauche, à la place de l'icône `user` (la photo prend le carré 56×56 px existant).
- Sur le **formulaire d'édition** (`templates/members/member_form.html`), si une photo existe déjà, afficher une miniature (~80 px) au-dessus du widget `<input type="file">` avec le label « Photo actuelle ». Pas d'option « supprimer la photo » dans ce sprint (l'utilisateur peut uploader une nouvelle photo qui remplace l'ancienne).

### Expiration auto-calculée au change de registration_date

JS minimal sur `member_form.html` :
- À l'événement `change` sur `input[name=registration_date]`, mettre `input[name=expiration_date]` à `registration_date + 1 an` (date pure, fuseau ignoré).
- Si l'utilisateur a déjà saisi une valeur explicite après le change, elle est respectée tant qu'il ne retouche pas à `registration_date`.

Durée fixée à 12 mois côté JS (la valeur du modèle peut varier par `MemberCategory.card_validity_months`, mais 12 est le défaut et la valeur de toutes les catégories seed actuelles — la valeur côté serveur reste autorité, le JS sert d'aide à la saisie).

### Création

`Member.registration_date` est déjà initialisé à `date.today` côté form et model. Le fix BUG-015 fait apparaître la date dans l'input HTML5.

## Technical spec

1. **Widgets format ISO** (`apps/members/forms.py`) :
   ```python
   "birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
   ```
   pour les trois champs `birth_date`, `registration_date`, `expiration_date`. Cf. BUG-015.

2. **Template `member_detail.html`** : si `member.photo`, remplacer l'icône `user` du pagehead par un `<img>` rond 56×56 px.

3. **Template `member_form.html`** : ajouter un `<div>` avant `form.photo` avec la miniature courante si `form.instance.photo`.

4. **JS recalcul expiration** : bloc `<script>` en bas de `member_form.html`, idempotent (ajoute un seul listener) :
   ```js
   const reg = document.querySelector("input[name=registration_date]");
   const exp = document.querySelector("input[name=expiration_date]");
   if (reg && exp) {
       reg.addEventListener("change", function () {
           if (!reg.value) return;
           const d = new Date(reg.value + "T00:00:00");
           d.setFullYear(d.getFullYear() + 1);
           exp.value = d.toISOString().slice(0, 10);
       });
   }
   ```

## Impact on existing code

- `apps/members/forms.py` : widgets dates format ISO
- `templates/members/member_form.html` : preview photo + script JS
- `templates/members/member_detail.html` : affichage photo en pagehead
- `SPEC §6.2` : nouveau paragraphe « UI fiche & édition »
- Tests : `apps/members/tests/test_views.py` (round-trip dates) + `apps/members/tests/test_services.py` (round-trip photo)
