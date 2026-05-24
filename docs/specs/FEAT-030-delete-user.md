# FEAT-030 — Suppression d'un utilisateur

**Status :** DONE
**Date :** 2026-05-23
**Sprint :** 9
**Spec parent :** `SPEC_BIBLIOFELIA.md` §9.2

---

## Contexte

La gestion des comptes (FEAT-011, `/accounts/users/`) permet créer / éditer
/ reset password, mais pas supprimer. Pour un changement d'équipe
(bibliothécaire qui part, compte créé par erreur), il faut une action de
suppression — réservée superadmin.

Garde-fous validés par Val :
- Interdit de se supprimer soi-même.
- Interdit de supprimer le dernier SUPERADMIN actif (sinon box
  inadministrable).
- Auditlog préservé via `on_delete=SET_NULL` déjà en place sur :
  - `loans.librarian` (FK User)
  - `catalog.BibliographicRecord.created_by`
  - `catalog.ScanSession.created_by`
  - `api.ScanHandoff.completed_by` (à vérifier)

---

## Comportement

1. Bouton « Supprimer le compte » sur `user_list.html` et sur
   `user_form.html` (édition), visible uniquement superadmin.
2. Garde-fous au niveau vue :
   - Si `request.user.pk == user.pk` → erreur « Vous ne pouvez pas
     supprimer votre propre compte. »
   - Si `user.role == SUPERADMIN` et que c'est le dernier superadmin actif
     (`User.objects.filter(role=SUPERADMIN, is_active=True).count() <= 1`)
     → erreur « Il doit rester au moins un superadmin actif. »
3. Page de confirmation listant les références qui passeront à NULL (N
   prêts gérés, N notices créées, N sessions de scan…).
4. POST → `user.delete()`. L'auditlog (`apps.core.apps.ready`) garde la
   trace via `actor` qui devient NULL mais conserve l'action.
5. Redirection `accounts:user_list`.

---

## Spec technique

### URL (`apps/accounts/urls.py`)

```python
path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
```

### Vue (`apps/accounts/views.py`)

```python
@require_role(Role.SUPERADMIN)
def user_delete(request, pk: int):
    user = get_object_or_404(User, pk=pk)

    if request.user.pk == user.pk:
        messages.error(request, _("Vous ne pouvez pas supprimer votre propre compte."))
        return redirect("accounts:user_list")

    if user.role == Role.SUPERADMIN:
        active_supers = User.objects.filter(
            role=Role.SUPERADMIN, is_active=True
        ).exclude(pk=user.pk).count()
        if active_supers == 0:
            messages.error(
                request,
                _("Impossible : il doit rester au moins un superadmin actif."),
            )
            return redirect("accounts:user_list")

    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, _("Compte %(u)s supprimé.") % {"u": username})
        return redirect("accounts:user_list")

    # GET : page de confirmation
    impacts = {
        "loans_handled": user.loans_handled.count(),
        "records_created": user.records_created.count(),
        "scan_sessions": user.scan_sessions.count(),
    }
    return render(request, "accounts/user_confirm_delete.html", {
        "target": user,
        "impacts": impacts,
    })
```

### Template `user_confirm_delete.html` (nouveau)

Petit récap des impacts + bouton « Confirmer » + « Annuler ».

### Template `user_list.html`

Pour chaque ligne (sauf request.user.pk == user.pk) :
```html
<a href="{% url 'accounts:user_delete' user.pk %}" class="btn btn-danger btn-sm">
    {% trans "Supprimer" %}
</a>
```

---

## Impact sur l'existant

- `apps/accounts/views.py` : +1 vue.
- `apps/accounts/urls.py` : +1 route.
- `templates/accounts/user_list.html` : +1 bouton par ligne.
- `templates/accounts/user_confirm_delete.html` : nouveau.

Pas de migration : les champs `SET_NULL` existent déjà sur les FK qui
référencent User.

---

## Tests (`apps/accounts/tests/test_user_delete.py`)

- `test_delete_requires_superadmin` : librarian → 403.
- `test_cannot_delete_self` : superadmin tente de se supprimer → erreur,
  user toujours en base.
- `test_cannot_delete_last_superadmin` : seul superadmin → erreur.
- `test_can_delete_other_superadmin_if_another_active_exists` : 2
  superadmins → delete OK.
- `test_delete_librarian_succeeds` : suppression d'un librarian → OK.
- `test_delete_preserves_loan_history` : librarian avec 1 loan_handled →
  après delete, Loan.librarian=NULL, Loan reste.

---

## Fix applied / Notes d'implémentation

À compléter après build/test.
