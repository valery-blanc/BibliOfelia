"""Tests des planifications django-q2. SPEC §4.4 / §8.

Ces tests couvrent BUG-045 : `setup_schedules` ne tournait pas dans l'entrypoint
de prod, et lorsqu'on l'y ajoute il tourne **à chaque démarrage du conteneur** —
ce qui rend le comportement de `install_schedules()` sur une planification
existante bien plus important qu'avant.
"""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone
from django_q.models import Schedule

from apps.tasks.scheduling import SCHEDULES, install_schedules


@pytest.mark.django_db
class TestInstallSchedules:
    def test_cree_les_trois_planifications(self):
        assert install_schedules() == len(SCHEDULES)
        noms = set(Schedule.objects.values_list("name", flat=True))
        assert noms == {s["name"] for s in SCHEDULES}

    def test_la_sauvegarde_horaire_est_installee(self):
        """Le cœur de BUG-045 : sans cette ligne, la Box ne sauvegarde jamais."""
        install_schedules()
        backup = Schedule.objects.get(name="bibliofelia.backup.hourly")
        assert backup.func == "apps.tasks.backup.run_backup"
        assert backup.schedule_type == Schedule.HOURLY
        assert backup.repeats == -1  # indéfiniment

    def test_idempotent_aucun_doublon(self):
        install_schedules()
        install_schedules()
        install_schedules()
        assert Schedule.objects.count() == len(SCHEDULES)

    def test_next_run_n_est_pas_repousse_a_chaque_appel(self):
        """Le piège de BUG-045.

        `setup_schedules` tourne désormais à chaque démarrage du conteneur. Si
        `install_schedules()` réécrivait `next_run = maintenant + 2 min`, une Box
        qui redémarre plus souvent que son intervalle de sauvegarde — c'est le
        cas nominal sur un site à coupures de courant — repousserait l'échéance
        indéfiniment et **ne sauvegarderait jamais**, tout en affichant trois
        planifications parfaitement saines.
        """
        install_schedules()
        backup = Schedule.objects.get(name="bibliofelia.backup.hourly")

        # Une échéance déjà due, comme après une coupure de courant.
        echeance = timezone.now() - timedelta(minutes=30)
        Schedule.objects.filter(pk=backup.pk).update(next_run=echeance)

        install_schedules()  # redémarrage du conteneur

        backup.refresh_from_db()
        assert backup.next_run == echeance, (
            "next_run a été repoussé : la sauvegarde due ne partira jamais"
        )

    def test_les_autres_champs_sont_bien_resynchronises(self):
        """Ne pas toucher `next_run` ne veut pas dire ne rien mettre à jour :
        si la définition d'une planification change (fonction, intervalle), le
        redémarrage doit la corriger."""
        install_schedules()
        Schedule.objects.filter(name="bibliofelia.backup.hourly").update(
            func="apps.tasks.backup.obsolete", minutes=1
        )

        install_schedules()

        backup = Schedule.objects.get(name="bibliofelia.backup.hourly")
        assert backup.func == "apps.tasks.backup.run_backup"
        assert backup.minutes == 60

    def test_next_run_pose_si_absent(self):
        """Cas limite : une planification sans échéance ne doit pas rester
        muette — on lui en pose une."""
        install_schedules()
        Schedule.objects.filter(name="bibliofelia.backup.hourly").update(next_run=None)

        install_schedules()

        backup = Schedule.objects.get(name="bibliofelia.backup.hourly")
        assert backup.next_run is not None
