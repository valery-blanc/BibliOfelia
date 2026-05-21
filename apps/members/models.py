"""Modèles usagers. SPEC §5.2.

MemberCategory, Member. card_number = EAN13 préfixe 291.
"""
from __future__ import annotations

from datetime import date
from dateutil.relativedelta import relativedelta

from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from apps.core.ean import build_ean13
from apps.catalog.models import DocumentType


MEMBER_EAN13_PREFIX = "291"


class MemberStatus(models.TextChoices):
    ACTIVE = "active", _("Actif")
    SUSPENDED = "suspended", _("Suspendu")
    EXPIRED = "expired", _("Expiré")
    CLOSED = "closed", _("Clôturé")


class MemberCategory(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=80)
    max_concurrent_loans = models.PositiveIntegerField(default=3)
    default_loan_duration_days = models.PositiveIntegerField(default=21)
    allowed_document_types = models.JSONField(
        default=list,
        blank=True,
        help_text=_("Liste de codes DocumentType ; vide = tous autorisés."),
    )
    card_validity_months = models.PositiveIntegerField(default=12)

    class Meta:
        verbose_name = _("catégorie d'usager")
        verbose_name_plural = _("catégories d'usager")
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"

    def allows_document_type(self, doc_type: str) -> bool:
        if not self.allowed_document_types:
            return True
        return doc_type in self.allowed_document_types


class Member(models.Model):
    card_number = models.CharField(max_length=13, unique=True, blank=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    birth_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey(
        MemberCategory, related_name="members", on_delete=models.PROTECT
    )
    contact_phone = models.CharField(max_length=40, blank=True)
    address = models.TextField(blank=True)
    registration_date = models.DateField(default=date.today)
    expiration_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=15, choices=MemberStatus.choices, default=MemberStatus.ACTIVE
    )
    notes = models.TextField(blank=True)
    preferred_language = models.CharField(max_length=10, blank=True, default="")
    replaces_card_number = models.CharField(max_length=13, blank=True)
    parent_account = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="dependents",
        on_delete=models.SET_NULL,
        help_text=_("Compte collectif parent (école/famille)."),
    )
    photo = models.FileField(upload_to="member_photos/", blank=True, null=True)

    class Meta:
        verbose_name = _("usager")
        verbose_name_plural = _("usagers")
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"], name="member_name_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.last_name} {self.first_name}".strip()

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating:
            if self.expiration_date is None and self.category_id:
                months = self.category.card_validity_months or 12
                self.expiration_date = self.registration_date + relativedelta(months=months)
            with transaction.atomic():
                super().save(*args, **kwargs)
                if not self.card_number:
                    self.card_number = build_ean13(MEMBER_EAN13_PREFIX, self.pk)
                    super().save(update_fields=["card_number"])
            return
        super().save(*args, **kwargs)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def is_active(self) -> bool:
        return self.status == MemberStatus.ACTIVE
