"""Activités, animations et bouclement. FEAT-085 / FEAT-086, SPEC §6.14–§6.15.

Ce que BibliOfelia ignorait jusqu'ici : le travail des employés. Sans ces
tables, impossible de répondre en fin d'année à « combien d'animations, et qui
est venu ? » — la question que pose tout bailleur.
"""
from __future__ import annotations

from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class ActivityType(models.Model):
    """Nature d'activité — administrable. FEAT-085.

    Une nature désactivée disparaît du formulaire mais reste dans les saisies
    passées et dans les statistiques : désactiver une ligne ne doit pas
    réécrire l'histoire.
    """

    label = models.CharField(max_length=120, unique=True, verbose_name=_("libellé"))
    is_active = models.BooleanField(default=True, verbose_name=_("actif"))
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_("ordre"))

    class Meta:
        verbose_name = _("nature d'activité")
        verbose_name_plural = _("natures d'activité")
        ordering = ["order", "label"]

    def __str__(self) -> str:
        return self.label


class ActivityEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="activity_entries",
        # PROTECT : un employé supprimé emporterait les statistiques de
        # l'année avec lui.
        on_delete=models.PROTECT,
        verbose_name=_("employé"),
    )
    occurred_on = models.DateField(default=date.today, verbose_name=_("date"))
    activity_type = models.ForeignKey(
        ActivityType,
        related_name="entries",
        on_delete=models.PROTECT,
        verbose_name=_("activité"),
    )
    minutes = models.PositiveIntegerField(verbose_name=_("temps passé (minutes)"))
    note = models.CharField(max_length=250, blank=True, verbose_name=_("note"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("activité")
        verbose_name_plural = _("activités")
        ordering = ["-occurred_on", "-id"]
        indexes = [
            models.Index(fields=["occurred_on"], name="activity_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.occurred_on} — {self.activity_type}"

    @property
    def duration_display(self) -> str:
        hours, minutes = divmod(self.minutes, 60)
        if hours and minutes:
            return _("%(h)s h %(m)02d") % {"h": hours, "m": minutes}
        if hours:
            return _("%(h)s h") % {"h": hours}
        return _("%(m)s min") % {"m": minutes}


class AnimationType(models.Model):
    """Intitulé d'animation. Administrable, mais **l'animateur peut en ajouter**
    depuis son formulaire : une animation s'invente le jour même."""

    label = models.CharField(max_length=150, unique=True, verbose_name=_("intitulé"))
    is_active = models.BooleanField(default=True, verbose_name=_("actif"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="animation_types_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("type d'animation")
        verbose_name_plural = _("types d'animation")
        ordering = ["label"]

    def __str__(self) -> str:
        return self.label

    @classmethod
    def get_or_create_by_label(cls, label: str, user=None) -> AnimationType:
        """Recherche insensible à la casse avant création.

        Sans elle, « Heure du conte » et « heure du conte » compteraient
        séparément dans les statistiques de fin d'année.
        """
        label = (label or "").strip()
        existing = cls.objects.filter(label__iexact=label).first()
        if existing:
            return existing
        return cls.objects.create(label=label, created_by=user)


class AnimationSession(models.Model):
    occurred_on = models.DateField(default=date.today, verbose_name=_("date"))
    animation_type = models.ForeignKey(
        AnimationType,
        related_name="sessions",
        on_delete=models.PROTECT,
        verbose_name=_("animation"),
    )
    presenter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="animations_presented",
        on_delete=models.PROTECT,
        verbose_name=_("animateur"),
    )
    minutes = models.PositiveIntegerField(verbose_name=_("temps passé (minutes)"))
    non_member_adults = models.PositiveIntegerField(
        default=0, verbose_name=_("non-membres adultes")
    )
    non_member_children = models.PositiveIntegerField(
        default=0, verbose_name=_("non-membres enfants")
    )
    note = models.CharField(max_length=250, blank=True, verbose_name=_("note"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("animation")
        verbose_name_plural = _("animations")
        ordering = ["-occurred_on", "-id"]
        indexes = [
            models.Index(fields=["occurred_on"], name="animation_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.occurred_on} — {self.animation_type}"

    @property
    def member_count(self) -> int:
        return self.attendances.count()

    @property
    def non_member_count(self) -> int:
        return self.non_member_adults + self.non_member_children

    @property
    def total_attendance(self) -> int:
        return self.member_count + self.non_member_count

    @property
    def duration_display(self) -> str:
        hours, minutes = divmod(self.minutes, 60)
        if hours and minutes:
            return _("%(h)s h %(m)02d") % {"h": hours, "m": minutes}
        if hours:
            return _("%(h)s h") % {"h": hours}
        return _("%(m)s min") % {"m": minutes}


class AnimationAttendance(models.Model):
    session = models.ForeignKey(
        AnimationSession, related_name="attendances", on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        "members.Member", related_name="animation_attendances", on_delete=models.CASCADE
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("présence")
        verbose_name_plural = _("présences")
        unique_together = [("session", "member")]
        ordering = ["member__last_name", "member__first_name"]

    def __str__(self) -> str:
        return f"{self.member} @ {self.session}"


class DayClosing(models.Model):
    """Trace du bouclement. FEAT-086.

    Un enregistrement par jour **et par employé** : un employé qui finit son
    service à midi boucle, un autre reboucle le soir. Ce n'est pas un verrou,
    c'est un journal.
    """

    closing_date = models.DateField(default=date.today, verbose_name=_("date"))
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="day_closings",
        on_delete=models.PROTECT,
        verbose_name=_("employé"),
    )
    closed_at = models.DateTimeField(auto_now=True)
    activities_done = models.BooleanField(default=False)
    cash_reviewed = models.BooleanField(default=False)
    emails_sent = models.PositiveIntegerField(default=0)
    emails_queued = models.PositiveIntegerField(default=0)
    backup_status = models.CharField(max_length=20, blank=True)
    backup_detail = models.CharField(max_length=250, blank=True)
    shutdown_requested = models.BooleanField(default=False)
    note = models.CharField(max_length=250, blank=True, verbose_name=_("note"))

    class Meta:
        verbose_name = _("bouclement")
        verbose_name_plural = _("bouclements")
        unique_together = [("closing_date", "user")]
        ordering = ["-closing_date", "-id"]

    def __str__(self) -> str:
        return f"{self.closing_date} — {self.user}"
