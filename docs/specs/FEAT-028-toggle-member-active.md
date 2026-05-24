# FEAT-028 — Désactiver / réactiver un membre

**Status :** DONE
**Date :** 2026-05-23
**Sprint :** 9
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.2

---

## Contexte

Un membre peut avoir un comportement inadapté (livres jamais rendus,
réinscription douteuse) → le bibliothécaire veut le **suspendre**
temporairement sans le supprimer (pour conserver l'historique). Aujourd'hui
on doit passer par `/admin/`, ce qui contredit la règle « pas d'admin Django
pour les bibliothécaires » (cf. mémoire `admin_django_scope`).

La cible UI est : un bouton sur la fiche membre qui fait toggle entre
ACTIVE et SUSPENDED.

---

## Comportement

1. Sur `member_detail.html`, à côté de « Renouveler la carte » :
   - Si `member.status == ACTIVE` → bouton **« Désactiver »** (rouge clair).
   - Si `member.status == SUSPENDED` → bouton **« Réactiver »** (vert).
   - Si `member.status in (EXPIRED, CLOSED)` → bouton « Réactiver » qui
     repasse à ACTIVE et recalcule `expiration_date` via
     `relativedelta(months=category.card_validity_months)`. (Comportement
     similaire à `renew_card` mais sans changer `card_number`.)
2. POST vers `members:toggle_active` (action atomique, pas de page de
   confirmation — c'est réversible).
3. Le statut SUSPENDED bloque déjà les nouveaux prêts via
   `apps/loans/services.py:check_member_can_borrow` (vérifié).
4. La liste `member_list.html` affiche déjà la colonne statut (FEAT-007) :
   pas d'évolution UI nécessaire à part vérifier que SUSPENDED reste visible.

---

## Spec technique

### URL (`apps/members/urls.py`)

```python
path("<int:pk>/toggle-active/", views.member_toggle_active, name="toggle_active"),
```

### Vue (`apps/members/views.py`)

```python
@require_POST
@require_role(*WRITE_ROLES)
def member_toggle_active(request, pk):
    member = get_object_or_404(Member, pk=pk)
    if member.status == MemberStatus.ACTIVE:
        member.status = MemberStatus.SUSPENDED
        msg = _("Membre suspendu.")
    else:
        member.status = MemberStatus.ACTIVE
        # Si la carte est expirée, on relance la durée de validité
        if member.expiration_date and member.expiration_date < date.today():
            months = member.category.card_validity_months or 12
            member.expiration_date = date.today() + relativedelta(months=months)
        msg = _("Membre réactivé.")
    member.save(update_fields=["status", "expiration_date"])
    messages.success(request, msg)
    return redirect("members:detail", pk=member.pk)
```

### Template `member_detail.html`

```html
<form method="post" action="{% url 'members:toggle_active' member.pk %}"
      class="inline-form">
    {% csrf_token %}
    {% if member.status == 'active' %}
        <button type="submit" class="btn btn-warning">{% trans "Désactiver" %}</button>
    {% else %}
        <button type="submit" class="btn btn-success">{% trans "Réactiver" %}</button>
    {% endif %}
</form>
```

---

## Impact sur l'existant

- `apps/members/views.py` : +1 vue, +imports (`MemberStatus`,
  `relativedelta`, `date`).
- `apps/members/urls.py` : +1 route.
- `templates/members/member_detail.html` : +1 bouton.

Pas de migration (les statuts existent déjà depuis FEAT-002).

---

## Tests (`apps/members/tests/test_toggle_active.py`)

- `test_toggle_active_to_suspended` : ACTIVE → SUSPENDED, status persisté.
- `test_toggle_suspended_to_active` : SUSPENDED → ACTIVE.
- `test_toggle_expired_renews_expiration` : EXPIRED + expiration_date
  passée → ACTIVE, expiration_date recalculée à today + N mois.
- `test_suspended_blocks_new_loan` : tentative de prêt sur membre SUSPENDED
  → bloquée par `check_member_can_borrow`.
- `test_toggle_requires_write_role` : readonly → 403.

---

## Fix applied / Notes d'implémentation

À compléter après build/test.
