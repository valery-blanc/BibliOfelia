"""Modèles du catalogue. SPEC §5.2.

Author, Category, Tag, Location, BibliographicRecord, Item.

Les champs `name` (Category, Tag) sont traduisibles ; modeltranslation est
enregistré dans `apps.catalog.translation` (Task #3) et générera les colonnes
`name_fr`, `name_en`, `name_es`, `name_mg` via migration additive.
"""
from __future__ import annotations

import uuid
from datetime import date

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.ean import build_ean13


class DocumentType(models.TextChoices):
    BOOK = "book", _("Livre")
    MAGAZINE_ISSUE = "magazine_issue", _("Numéro de magazine")
    NEWSPAPER = "newspaper", _("Journal")
    COMIC = "comic", _("BD / manga")
    AUDIO_CD = "audio_cd", _("CD audio")
    OTHER = "other", _("Autre")


class MetadataSource(models.TextChoices):
    MANUAL = "manual", _("Saisie manuelle")
    OPENLIBRARY = "openlibrary", _("OpenLibrary")
    SCAN_APP = "scan_app", _("OfeliaScan")
    IMPORT = "import", _("Import")


class MetadataQuality(models.TextChoices):
    VERIFIED = "verified", _("Vérifiée")
    AUTO = "auto", _("Automatique")
    PARTIAL = "partial", _("Partielle")


class ItemState(models.TextChoices):
    NEW = "new", _("Neuf")
    GOOD = "good", _("Bon")
    WORN = "worn", _("Usé")
    DAMAGED = "damaged", _("Abîmé")


class ItemStatus(models.TextChoices):
    AVAILABLE = "available", _("Disponible")
    ON_LOAN = "on_loan", _("Prêté")
    RESERVED_FOR_PICKUP = "reserved_for_pickup", _("Mis de côté")
    IN_REPAIR = "in_repair", _("En réparation")
    LOST = "lost", _("Perdu")
    DISCARDED = "discarded", _("Pilonné")


class AcquisitionSource(models.TextChoices):
    PURCHASE = "purchase", _("Achat")
    DONATION = "donation", _("Don")
    EXCHANGE = "exchange", _("Échange")
    UNKNOWN = "unknown", _("Inconnu")


ITEM_EAN13_PREFIX = "290"


class Author(models.Model):
    full_name = models.CharField(max_length=200, db_index=True)
    birth_year = models.IntegerField(null=True, blank=True)
    death_year = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("auteur")
        verbose_name_plural = _("auteurs")
        ordering = ["full_name"]

    def __str__(self) -> str:
        return self.full_name


class Category(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL
    )
    default_loan_duration_days = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = _("catégorie")
        verbose_name_plural = _("catégories")
        ordering = ["code"]

    def __str__(self) -> str:
        return f"{self.code} — {self.name}"


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)
    color = models.CharField(max_length=7, blank=True, help_text=_("Hex ex: #ff8800"))

    class Meta:
        verbose_name = _("tag")
        verbose_name_plural = _("tags")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Location(models.Model):
    code = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, related_name="children", on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _("emplacement")
        verbose_name_plural = _("emplacements")
        ordering = ["code"]
        constraints = [
            models.UniqueConstraint(fields=["code", "parent"], name="location_code_parent_unique"),
        ]

    def __str__(self) -> str:
        return self.code


class BibliographicRecord(models.Model):
    title = models.CharField(max_length=300, db_index=True)
    subtitle = models.CharField(max_length=300, blank=True)
    authors = models.ManyToManyField(Author, blank=True, related_name="records")
    publisher = models.CharField(max_length=200, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    language = models.CharField(max_length=10, blank=True, default="fr")
    isbn_13 = models.CharField(max_length=13, blank=True, null=True, db_index=True)
    isbn_10 = models.CharField(max_length=10, blank=True, null=True, db_index=True)
    summary = models.TextField(blank=True)
    cover_image = models.FileField(upload_to="covers/", blank=True, null=True)
    category = models.ForeignKey(
        Category, null=True, blank=True, related_name="records", on_delete=models.SET_NULL
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="records")
    series_name = models.CharField(max_length=200, blank=True)
    series_volume = models.CharField(max_length=20, blank=True)
    document_type = models.CharField(
        max_length=20, choices=DocumentType.choices, default=DocumentType.BOOK
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="records_created",
        on_delete=models.SET_NULL,
    )
    metadata_source = models.CharField(
        max_length=20, choices=MetadataSource.choices, default=MetadataSource.MANUAL
    )
    metadata_quality = models.CharField(
        max_length=20, choices=MetadataQuality.choices, default=MetadataQuality.VERIFIED
    )

    class Meta:
        verbose_name = _("notice bibliographique")
        verbose_name_plural = _("notices bibliographiques")
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                fields=["isbn_13"],
                condition=models.Q(isbn_13__isnull=False),
                name="record_isbn13_unique_not_null",
            ),
        ]

    def __str__(self) -> str:
        return self.title


class Item(models.Model):
    internal_id = models.CharField(max_length=20, unique=True, blank=True)
    ean13 = models.CharField(max_length=13, unique=True, blank=True)
    record = models.ForeignKey(
        BibliographicRecord, related_name="items", on_delete=models.CASCADE
    )
    location = models.ForeignKey(
        Location, null=True, blank=True, related_name="items", on_delete=models.SET_NULL
    )
    state = models.CharField(max_length=10, choices=ItemState.choices, default=ItemState.GOOD)
    acquisition_date = models.DateField(default=date.today)
    acquisition_source = models.CharField(
        max_length=15, choices=AcquisitionSource.choices, default=AcquisitionSource.UNKNOWN
    )
    donor = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=25, choices=ItemStatus.choices, default=ItemStatus.AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("exemplaire")
        verbose_name_plural = _("exemplaires")
        ordering = ["internal_id"]
        indexes = [
            models.Index(fields=["status", "location"], name="item_status_location_idx"),
        ]

    def __str__(self) -> str:
        return self.internal_id or f"Item#{self.pk}"

    def save(self, *args, **kwargs):
        creating = self.pk is None
        if creating:
            with transaction.atomic():
                super().save(*args, **kwargs)
                self._assign_codes()
                super().save(update_fields=["internal_id", "ean13"])
            return
        super().save(*args, **kwargs)

    def _assign_codes(self) -> None:
        """Génère internal_id (OFL-YYYYMMDD-NNNN) et ean13 (290 + seq + checksum)."""
        if not self.internal_id:
            today = timezone.localdate()
            day_str = today.strftime("%Y%m%d")
            seq_today = (
                Item.objects.filter(internal_id__startswith=f"OFL-{day_str}-")
                .exclude(pk=self.pk)
                .count()
                + 1
            )
            self.internal_id = f"OFL-{day_str}-{seq_today:04d}"
        if not self.ean13:
            self.ean13 = build_ean13(ITEM_EAN13_PREFIX, self.pk)


# ─── Sessions de scan OfeliaScan ───────────────────────────────────────────
# FEAT-021 / Task #20 (Sprint 5). OfeliaScan crée une session, envoie des
# batchs d'items, puis demande la finalisation : la session est alors
# transformée en BibliographicRecord + Item (matching ISBN si possible).


class ScanKind(models.TextChoices):
    EAN13 = "ean13", _("EAN13")
    ISBN = "isbn", _("ISBN")
    MANUAL = "manual", _("Saisie manuelle")


class ScanSessionState(models.TextChoices):
    OPEN = "open", _("Ouverte")
    FINALIZED = "finalized", _("Validée")


class ScanSession(models.Model):
    """Une campagne de catalogage envoyée depuis OfeliaScan. SPEC §6.10."""

    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    label = models.CharField(max_length=120, blank=True)
    state = models.CharField(
        max_length=10, choices=ScanSessionState.choices, default=ScanSessionState.OPEN
    )
    started_at = models.DateTimeField(default=timezone.now)
    finalized_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="scan_sessions",
        on_delete=models.SET_NULL,
    )
    # Résultat agrégé de la finalisation (items_processed, records_created, ...).
    processing_summary = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("session de scan")
        verbose_name_plural = _("sessions de scan")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return self.label or f"ScanSession {self.session_id}"

    @property
    def is_open(self) -> bool:
        return self.state == ScanSessionState.OPEN


class ScanItem(models.Model):
    """Un item envoyé par OfeliaScan dans une session de scan.

    `local_id` permet à OfeliaScan de rejouer un POST sans créer de doublon
    (contrainte UNIQUE `(session, local_id)`). `processed` passe à True
    après la finalisation, et `processing_result` mémorise l'action prise
    (record créé / matché / erreur).
    """

    session = models.ForeignKey(
        ScanSession, related_name="items", on_delete=models.CASCADE
    )
    local_id = models.CharField(max_length=120)
    scan_kind = models.CharField(max_length=10, choices=ScanKind.choices)
    scanned_value = models.CharField(max_length=32, blank=True)
    metadata_title = models.CharField(max_length=300, blank=True)
    metadata_authors = models.JSONField(default=list, blank=True)
    metadata_language = models.CharField(max_length=10, blank=True)
    metadata_publisher = models.CharField(max_length=200, blank=True)
    metadata_year = models.IntegerField(null=True, blank=True)
    location_code = models.CharField(max_length=20, blank=True)
    item_state = models.CharField(max_length=10, blank=True)
    copy_count = models.PositiveIntegerField(default=1)
    scanned_at = models.DateTimeField()
    notes = models.TextField(blank=True)
    processed = models.BooleanField(default=False)
    processing_result = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("item scanné")
        verbose_name_plural = _("items scannés")
        ordering = ["session", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "local_id"],
                name="scanitem_unique_local",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.local_id} ({self.scan_kind}={self.scanned_value or '∅'})"
