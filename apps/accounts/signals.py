"""Signaux de l'app accounts.

`assign_role_group` : à chaque save User, synchronise :
- `role`         : forcé à SUPERADMIN si `is_superuser=True` (createsuperuser).
- `is_staff`     : True ⇔ role == SUPERADMIN (seul accès /admin/ Django).
- `groups`       : appartenance au Group Django nommé d'après le rôle.

SPEC §9.2.
"""
from __future__ import annotations

from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Role, User


@receiver(post_save, sender=User)
def assign_role_group(sender, instance: User, created, **kwargs):
    target_role = Role.SUPERADMIN if instance.is_superuser else instance.role
    expected_staff = target_role == Role.SUPERADMIN

    updates: dict = {}
    if instance.role != target_role:
        updates["role"] = target_role
    if instance.is_staff != expected_staff:
        updates["is_staff"] = expected_staff
    if updates:
        # `update()` évite la récursion sur post_save
        User.objects.filter(pk=instance.pk).update(**updates)
        for k, v in updates.items():
            setattr(instance, k, v)

    try:
        group = Group.objects.get(name=target_role)
    except Group.DoesNotExist:
        # `setup_roles` n'a pas encore tourné ; ré-essai au prochain save
        return

    # Sync : on enlève les autres groupes de rôle, ajoute le bon
    role_group_names = set(Role.values)
    current_role_groups = instance.groups.filter(name__in=role_group_names)
    if not (current_role_groups.count() == 1 and current_role_groups.first() == group):
        instance.groups.remove(*current_role_groups)
        instance.groups.add(group)
