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
    # FEAT-052 : périodiques (revues/magazines). ISSN normalisé 8 caractères
    # (7 chiffres + clé 0-9/X), stocké sans tiret. L'ISSN identifie le titre
    # de la revue, pas le numéro : contrainte unique → « 1 notice par ISSN ».
    issn = models.CharField(max_length=8, blank=True, null=True, db_index=True)
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
            models.UniqueConstraint(
                fields=["issn"],
                condition=models.Q(issn__isnull=False),
                name="record_issn_unique_not_null",
            ),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def issn_display(self) -> str:
        """FEAT-052 : ISSN au format lisible ``1234-5679`` (vide si absent)."""
        from apps.core.issn import format_issn

        return format_issn(self.issn) if self.issn else ""


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
    # FEAT-046 : session de catalogage qui a créé cet exemplaire (caméra ou
    # OfeliaScan). Permet de réimprimer uniquement les étiquettes d'un lot.
    # SET_NULL : supprimer une session ne doit jamais supprimer les exemplaires.
    catalog_session = models.ForeignKey(
        "ScanSession",
        null=True,
        blank=True,
        related_name="created_items",
        on_delete=models.SET_NULL,
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
        """Génère internal_id (OFL-YYYYMMDD-NNNN) et ean13 (290 + seq + checksum).

        BUG 2026-05-24 : on utilisait `count()+1`, mais en présence de trous
        dans la séquence (suppressions, rollbacks de sessions échouées) le
        count produisait une seq déjà prise → UNIQUE constraint. On prend
        désormais `MAX(internal_id)+1` (zero-padding 4 chiffres → max
        alphabétique = max numérique).

        FEAT-043 : pour éviter qu'un code Ofelia déjà imprimé sur une
        étiquette physique soit réattribué à un nouveau livre après une
        suppression, le MAX inclut désormais les codes retirés
        (RetiredItemCode). Les codes supprimés ne sont jamais réutilisés.
        """
        from django.db.models import Max

        if not self.internal_id:
            today = timezone.localdate()
            day_str = today.strftime("%Y%m%d")
            prefix = f"OFL-{day_str}-"
            max_item = (
                Item.objects.filter(internal_id__startswith=prefix)
                .exclude(pk=self.pk)
                .aggregate(m=Max("internal_id"))["m"]
            )
            max_retired = (
                RetiredItemCode.objects.filter(internal_id__startswith=prefix)
                .aggregate(m=Max("internal_id"))["m"]
            )
            candidates = [v for v in (max_item, max_retired) if v]
            max_seq = 0
            if candidates:
                top = max(candidates)
                try:
                    max_seq = int(top.rsplit("-", 1)[-1])
                except (ValueError, IndexError):
                    max_seq = 0
            self.internal_id = f"OFL-{day_str}-{max_seq + 1:04d}"
        if not self.ean13:
            self.ean13 = build_ean13(ITEM_EAN13_PREFIX, self.pk)


class RetiredItemCode(models.Model):
    """FEAT-043 : tombstone d'un code Ofelia (internal_id) supprimé.

    Les étiquettes pouvant être imprimées et collées sur un livre, un code
    retiré ne doit jamais être réattribué à un nouvel exemplaire. Un
    signal `pre_delete` sur Item insère ici une ligne avant la suppression.
    """

    REASON_BULK_DELETE = "bulk_delete"
    REASON_ITEM_DELETE = "item_delete"
    REASON_CHOICES = [
        (REASON_BULK_DELETE, _("Suppression en masse de notices")),
        (REASON_ITEM_DELETE, _("Suppression d'exemplaire")),
    ]

    internal_id = models.CharField(max_length=20, primary_key=True)
    ean13 = models.CharField(max_length=13, blank=True)
    record_title_snapshot = models.CharField(max_length=255, blank=True)
    retired_at = models.DateTimeField(auto_now_add=True)
    retired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="retired_item_codes",
    )
    reason = models.CharField(max_length=20, choices=REASON_CHOICES, default=REASON_ITEM_DELETE)

    class Meta:
        verbose_name = _("code Ofelia retiré")
        verbose_name_plural = _("codes Ofelia retirés")
        ordering = ["-retired_at"]
        indexes = [
            models.Index(fields=["internal_id"], name="retired_internal_id_idx"),
        ]

    def __str__(self) -> str:
        return self.internal_id


# ─── Sessions de scan OfeliaScan ───────────────────────────────────────────
# FEAT-021 / Task #20 (Sprint 5). OfeliaScan crée une session, envoie des
# batchs d'items, puis demande la finalisation : la session est alors
# transformée en BibliographicRecord + Item (matching ISBN si possible).


class ScanKind(models.TextChoices):
    EAN13 = "ean13", _("EAN13")
    ISBN = "isbn", _("ISBN")
    ISSN = "issn", _("ISSN")  # FEAT-052 : périodique (EAN-13 préfixe 977)
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
    # FEAT-046 : défauts appliqués aux items scannés en catalogage caméra
    # (surchargeables par ligne sur le hub).
    default_location = models.ForeignKey(
        "Location",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )
    default_category = models.ForeignKey(
        "Category",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

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
    # FEAT-046 : catégorie de la notice (catalogage caméra ; OfeliaScan ne la
    # renseigne pas → None, comportement inchangé).
    category = models.ForeignKey(
        "Category",
        null=True,
        blank=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )
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


# ─── Enrichissement métadonnées (FEAT-031, Sprint 9) ───────────────────────


class EnrichmentJobState(models.TextChoices):
    PENDING = "pending", _("En attente")
    RUNNING = "running", _("En cours")
    FINISHED = "finished", _("Terminé")
    FAILED = "failed", _("Échec")


class EnrichmentMode(models.TextChoices):
    FILL_MISSING = "fill_missing", _("Compléter les champs vides uniquement")
    OVERWRITE = "overwrite", _("Écraser avec les données externes")


class EnrichmentJob(models.Model):
    """Travail d'enrichissement multi-sources des métadonnées du catalogue."""

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    state = models.CharField(
        max_length=12,
        choices=EnrichmentJobState.choices,
        default=EnrichmentJobState.PENDING,
    )
    mode = models.CharField(
        max_length=20,
        choices=EnrichmentMode.choices,
        default=EnrichmentMode.FILL_MISSING,
    )
    sources = models.JSONField(default=list)
    scope_filter = models.JSONField(default=dict)
    total = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    updated = models.PositiveIntegerField(default=0)
    skipped = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    # BUG-019 : notices non complétées car une source a atteint son quota (429).
    # Un re-run ultérieur (quota disponible) pourra les compléter.
    rate_limited = models.PositiveIntegerField(default=0)
    report = models.JSONField(default=list)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="enrichment_jobs",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("enrichissement métadonnées")
        verbose_name_plural = _("enrichissements métadonnées")
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"EnrichmentJob#{self.pk} {self.state}"


# ─── Catalogage Excel (FEAT-050, Sprint 20) ────────────────────────────────


class ExcelJobMode(models.TextChoices):
    VERIFY = "verify", _("Vérification")
    IMPORT = "import", _("Import")


class ExcelJobState(models.TextChoices):
    PENDING = "pending", _("En attente")
    RUNNING = "running", _("En cours")
    FINISHED = "finished", _("Terminé")
    FAILED = "failed", _("Échec")


class ExcelCatalogJob(models.Model):
    """Travail de catalogage à partir d'un fichier Excel (FEAT-050).

    Deux modes :
    - VERIFY : annote l'Excel (titre/auteur trouvés par ISBN puis par
      titre+auteur fuzzy) et produit un fichier téléchargeable. Aucun effet
      de bord sur le catalogue.
    - IMPORT : matérialise une liste d'ISBN en notices + exemplaires via une
      ScanSession virtuelle (réutilise `finalize_scan_session`).
    """

    mode = models.CharField(max_length=10, choices=ExcelJobMode.choices)
    state = models.CharField(
        max_length=10, choices=ExcelJobState.choices, default=ExcelJobState.PENDING
    )
    uploaded_file = models.FileField(upload_to="excel_jobs/%Y/%m/")
    result_file = models.FileField(upload_to="excel_jobs/%Y/%m/", null=True, blank=True)
    # IMPORT uniquement : la session de scan virtuelle créée.
    scan_session = models.ForeignKey(
        ScanSession,
        null=True,
        blank=True,
        related_name="excel_jobs",
        on_delete=models.SET_NULL,
    )
    total = models.PositiveIntegerField(default=0)
    processed = models.PositiveIntegerField(default=0)
    matched_by_isbn = models.PositiveIntegerField(default=0)
    matched_by_ta = models.PositiveIntegerField(default=0)
    not_found = models.PositiveIntegerField(default=0)
    errors = models.PositiveIntegerField(default=0)
    # BUG-019 : lignes où une source a atteint son quota (429) pendant la
    # vérification → résultat potentiellement incomplet, à relancer plus tard.
    rate_limited = models.PositiveIntegerField(default=0)
    # Avertissements par ligne (emplacement/catégorie inconnu, ISBN invalide…).
    report = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="excel_catalog_jobs",
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("catalogage Excel")
        verbose_name_plural = _("catalogages Excel")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"ExcelCatalogJob#{self.pk} {self.mode} {self.state}"
