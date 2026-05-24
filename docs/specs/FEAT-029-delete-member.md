# FEAT-029 — Suppression d'un membre

**Status :** DONE
**Date :** 2026-05-23
**Sprint :** 9
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.2

---

## Contexte

Suppression d'un membre fantôme ou saisi par erreur. En exploitation
normale, on désactive (FEAT-028) plutôt que supprimer. Pour le nettoyage
massif des démos, `manage.py remove_demo` reste la voie royale.

Action **superadmin uniquement**. **Aucun blocage** : les prêts/réservations
actifs sont clôturés automatiquement (cf. petite bibliothèque, simplicité
> exhaustivité).

---

## Comportement

1. Bouton « Supprimer le membre » (rouge) sur `member_detail.html`,
   visible superadmin uniquement.
2. Page de confirmation listant les impacts :
   - N prêts en cours seront clôturés (RETURNED + items libérés).
   - N réservations actives seront annulées.
   - N prêts passés + N réservations passées + N consultations seront
     supprimés (CASCADE manuel).
   - N comptes rattachés (`parent_account`) auront leur lien rompu
     (parent_account=NULL via SET_NULL natif).
3. POST `members:delete` (transaction atomique) :
   - Réservations actives → CANCELLED (laisse trace auditlog).
   - Prêts actifs → RETURNED + items repassent en AVAILABLE.
   - Détache les dépendants : `member.dependents.update(parent_account=None)`
     (déjà SET_NULL natif).
   - `member.loans.all().delete()` puis `member.reservations.all().delete()`
     puis `member.consultations.all().delete()` (Loan.member et
     Reservation.member sont PROTECT, on cascade manuellement).
   - `member.delete()`.
4. Redirect `members:list` avec message succès.

---

## Spec technique

### URL

```python
path("<int:pk>/delete/", views.member_delete, name="delete"),
```

### Vue

```python
@require_role(Role.SUPERADMIN)
def member_delete(request, pk):
    member = get_object_or_404(Member, pk=pk)
    active_loans = member.loans.filter(status__in=(LoanStatus.ACTIVE, LoanStatus.OVERDUE))
    active_reservations = member.reservations.filter(
        status__in=(ReservationStatus.PENDING, ReservationStatus.READY_FOR_PICKUP)
    )
    past_loans_count = member.loans.exclude(
        status__in=(LoanStatus.ACTIVE, LoanStatus.OVERDUE)
    ).count()
    dependents = member.dependents.all()

    if request.method == "POST":
        with transaction.atomic():
            # 1. Annuler les réservations actives
            active_reservations.update(status=ReservationStatus.CANCELLED)
            # 2. Force-close les prêts actifs (libère les items)
            for loan in active_loans.select_related("item"):
                loan.status = LoanStatus.RETURNED
                loan.return_date = timezone.now()
                loan.save(update_fields=["status", "return_date"])
                if loan.item.status == ItemStatus.ON_LOAN:
                    loan.item.status = ItemStatus.AVAILABLE
                    loan.item.save(update_fields=["status"])
            # 3. Détacher dépendants
            dependents.update(parent_account=None)
            # 4. CASCADE manuel (Loan/Reservation.member=PROTECT)
            member.loans.all().delete()
            member.reservations.all().delete()
            member.consultations.all().delete()
            full_name = member.full_name
            member.delete()
        messages.success(request, _("Usager %(n)s supprimé.") % {"n": full_name})
        return redirect("members:list")

    return render(request, "members/member_confirm_delete.html", {
        "member": member,
        "active_loans": active_loans,
        "active_reservations_count": active_reservations.count(),
        "past_loans_count": past_loans_count,
        "dependents": dependents,
    })
```

### Template `member_confirm_delete.html` (nouveau)

Page de confirmation avec récap des impacts + boutons « Confirmer » /
« Annuler ».

### Template `member_detail.html`

```html
{% if request.user.is_superadmin %}
<a href="{% url 'members:delete' member.pk %}" class="btn btn-danger">
    {% trans "Supprimer le membre" %}
</a>
{% endif %}
```

---

## Impact sur l'existant

- `apps/members/views.py` : +1 vue, +imports (`transaction`, `timezone`,
  `LoanStatus`, `ReservationStatus`, `ItemStatus`).
- `apps/members/urls.py` : +1 route.
- `templates/members/member_detail.html` : +1 bouton (superadmin).
- `templates/members/member_confirm_delete.html` : nouveau.

**Pas de migration** (on garde Loan.member=PROTECT et on cascade
manuellement dans la vue — c'est explicite et localisé). `member.dependents`
est déjà SET_NULL natif.

---

## Tests (`apps/members/tests/test_member_delete.py`)

- `test_delete_requires_superadmin` : librarian → 403.
- `test_delete_simple_member` : pas de prêt → delete OK.
- `test_delete_with_active_loans` : 1 prêt ACTIVE → après delete,
  item.status=AVAILABLE, member et loan supprimés.
- `test_delete_cancels_active_reservations` : reservation PENDING avant
  cascade → status CANCELLED visible dans l'auditlog (puis supprimée).
- `test_delete_detaches_dependents` : parent + 2 dépendants → dépendants
  conservés avec parent_account=NULL.
- `test_delete_cascades_past_loans` : 5 prêts RETURNED → tous supprimés.
