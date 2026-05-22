"""Enregistrement des planifications django-q2 (§7.2 / §8).

Appelé par `manage.py setup_schedules`. Idempotent : Schedule.objects.update_or_create
sur le nom.
"""
from __future__ import annotations

from datetime import timedelta

from django.utils import timezone


SCHEDULES = [
    {
        "name": "bibliofelia.backup.hourly",
        "func": "apps.tasks.backup.run_backup",
        "schedule_type": "H",  # Hourly
        "minutes": 60,
    },
    {
        "name": "bibliofelia.members.expire_cards",
        "func": "apps.members.services.mark_expired_members",
        "schedule_type": "D",  # Daily
        "minutes": 24 * 60,
    },
    {
        "name": "bibliofelia.reservations.expire",
        "func": "apps.loans.services.expire_stale_reservations",
        "schedule_type": "D",
        "minutes": 24 * 60,
    },
]


def install_schedules() -> int:
    """Crée ou met à jour les Schedule django-q2. Retourne le nombre installé."""
    from django_q.models import Schedule

    installed = 0
    now = timezone.now()
    for spec in SCHEDULES:
        Schedule.objects.update_or_create(
            name=spec["name"],
            defaults={
                "func": spec["func"],
                "schedule_type": spec["schedule_type"],
                "minutes": spec["minutes"],
                "next_run": now + timedelta(minutes=2),
                "repeats": -1,
            },
        )
        installed += 1
    return installed
