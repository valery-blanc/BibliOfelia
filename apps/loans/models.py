"""Prêts, retours, consultations sur place, réservations. SPEC §5.2, §6.3, §6.4."""
from __future__ import annotations

from datetime import date

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class LoanStatus(models.TextChoices):
    ACTIVE = "active", _("En cours")
    RETURNED = "returned", _("Retourné")
    OVERDUE = "overdue", _("En retard")
    LOST = "lost", _("Perdu")
    WRITTEN_OFF = "written_off", _("Radié")


class ReservationStatus(models.TextChoices):
    PENDING = "pending", _("En attente")
    READY_FOR_PICKUP = "ready_for_pickup", _("Prêt à retirer")
    FULFILLED = "fulfilled", _("Honorée")
    EXPIRED = "expired", _("Expirée")
    CANCELLED = "cancelled", _("Annulée")


class Loan(models.Model):
    item = models.ForeignKey(
        "catalog.Item", related_name="loans", on_delete=models.PROTECT
    )
    member = models.ForeignKey(
        "members.Member", related_name="loans", on_delete=models.PROTECT
    )
    loan_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    return_date = models.DateTimeField(null=True, blank=True)
    renewal_count = models.PositiveSmallIntegerField(default=0)
    librarian = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="loans_handled",
        on_delete=models.SET_NULL,
    )
    status = models.CharField(
        max_length=15, choices=LoanStatus.choices, default=LoanStatus.ACTIVE
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("prêt")
        verbose_name_plural = _("prêts")
        ordering = ["-loan_date"]
        indexes = [
            models.Index(fields=["member", "status"], name="loan_member_status_idx"),
            models.Index(fields=["due_date", "status"], name="loan_due_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Loan#{self.pk} {self.item_id}→{self.member_id}"

    @property
    def is_overdue(self) -> bool:
        if self.status not in {LoanStatus.ACTIVE, LoanStatus.OVERDUE}:
            return False
        return date.today() > self.due_date


class InHouseConsultation(models.Model):
    """Consultation sur place (§5.2). Item/Member optionnels pour saisie groupée."""

    item = models.ForeignKey(
        "catalog.Item",
        null=True,
        blank=True,
        related_name="consultations",
        on_delete=models.SET_NULL,
    )
    member = models.ForeignKey(
        "members.Member",
        null=True,
        blank=True,
        related_name="consultations",
        on_delete=models.SET_NULL,
    )
    date = models.DateField(default=date.today)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = _("consultation sur place")
        verbose_name_plural = _("consultations sur place")
        ordering = ["-date"]


class Reservation(models.Model):
    record = models.ForeignKey(
        "catalog.BibliographicRecord", related_name="reservations", on_delete=models.CASCADE
    )
    member = models.ForeignKey(
        "members.Member", related_name="reservations", on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField()
    status = models.CharField(
        max_length=20, choices=ReservationStatus.choices, default=ReservationStatus.PENDING
    )
    ready_since = models.DateField(null=True, blank=True)
    fulfilled_by_item = models.ForeignKey(
        "catalog.Item",
        null=True,
        blank=True,
        related_name="fulfilled_reservations",
        on_delete=models.SET_NULL,
    )
    fulfilled_by_loan = models.ForeignKey(
        Loan,
        null=True,
        blank=True,
        related_name="fulfilling_reservations",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("réservation")
        verbose_name_plural = _("réservations")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"], name="reservation_status_idx"),
        ]

    def __str__(self) -> str:
        return f"Reservation#{self.pk}"
