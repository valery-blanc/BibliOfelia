"""Crée/met à jour les Group Django pour les rôles BibliOfelia (idempotent).

À appeler après `migrate` (cf. `scripts/dev-entrypoint.sh`).
SPEC §9.2.
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.groups import ROLE_PERMS
from apps.accounts.models import Role, User


class Command(BaseCommand):
    help = "Crée les Group par rôle et assigne les permissions (idempotent)."

    @transaction.atomic
    def handle(self, *args, **opts):
        for role in Role.values:
            group, created = Group.objects.get_or_create(name=role)
            self._sync_perms(group, ROLE_PERMS.get(role, []))
            status = "créé" if created else "à jour"
            self.stdout.write(self.style.SUCCESS(f"  Group '{role}' {status}"))

        # Resynchronise les users existants (utile si setup_roles tourne
        # après un createsuperuser).
        for user in User.objects.all():
            user.save()
        self.stdout.write(self.style.SUCCESS(f"  {User.objects.count()} user(s) resync."))

    def _sync_perms(self, group: Group, perms_list: list[tuple[str, str]]) -> None:
        if not perms_list:
            group.permissions.clear()
            return
        # On résout (app_label, codename) en Permission via ContentType
        target_perms = set()
        for app_label, codename in perms_list:
            try:
                # Trouve le ContentType qui matche app_label + codename
                # codename est de la forme {action}_{model_name}
                model_name = codename.split("_", 1)[1]
                ct = ContentType.objects.get(app_label=app_label, model=model_name)
                perm = Permission.objects.get(content_type=ct, codename=codename)
                target_perms.add(perm)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                self.stderr.write(
                    self.style.WARNING(
                        f"    ⚠ permission introuvable : {app_label}.{codename}"
                    )
                )
        current = set(group.permissions.all())
        to_add = target_perms - current
        to_remove = current - target_perms
        if to_add:
            group.permissions.add(*to_add)
        if to_remove:
            group.permissions.remove(*to_remove)
