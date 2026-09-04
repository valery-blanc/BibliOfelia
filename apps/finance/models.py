"""Caisse et facturation. FEAT-084, SPEC §6.13.

Cinq objets et une file d'attente :

- `Tariff`      — référentiel administrable des montants usuels
- `Invoice`     — ce qu'un usager doit, numéroté et daté
- `InvoiceLine` — le détail (cotisation, animation, amende, autre)
- `Payment`     — ce qu'il a réglé
- `CashMovement`— le registre de caisse : entrées, sorties
- `OutboundEmail` — la file d'envoi, qui survit à une Box hors ligne

Une facture numérotée **ne se supprime pas** : elle s'annule. Un registre de
caisse troué n'est plus un registre.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.db.models import F, Sum
from django.utils.translation import gettext_lazy as _


class FeeKind(models.TextChoices):
    MEMBERSHIP = "membership", _("Cotisation")
    ACTIVITY = "activity", _("Animation")
    FINE = "fine", _("Amende")
    OTHER = "other", _("Autre")


class InvoiceStatus(models.TextChoices):
    OPEN = "open", _("À régler")
    PAID = "paid", _("Réglée")
    CANCELLED = "cancelled", _("Annulée")


class PaymentMethod(models.TextChoices):
    CASH = "cash", _("Espèces")
    TRANSFER = "transfer", _("Virement")
    OTHER = "other", _("Autre")


class CashDirection(models.TextChoices):
    IN = "in", _("Entrée")
    OUT = "out", _("Sortie")


class Tariff(models.Model):
    """Montant usuel, administrable. FEAT-084.

    Sert de liste de motifs pour les amendes (décision Val : amendes
    **manuelles**, motif choisi dans une liste, montant libre) et de raccourci
    pour les frais d'animation. La cotisation, elle, vient de
    `MemberCategory.membership_fee` — un tarif par catégorie d'usager.
    """

    kind = models.CharField(
        max_length=20,
        choices=FeeKind.choices,
        default=FeeKind.FINE,
        verbose_name=_("nature"),
    )
    label = models.CharField(max_length=120, verbose_name=_("libellé"))
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0"),
        verbose_name=_("montant proposé"),
    )
    is_active = models.BooleanField(default=True, verbose_name=_("actif"))
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_("ordre"))

    class Meta:
        verbose_name = _("tarif")
        verbose_name_plural = _("tarifs")
        ordering = ["kind", "order", "label"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} — {self.label}"


class Invoice(models.Model):
    number = models.CharField(
        max_length=20, unique=True, blank=True, verbose_name=_("n° de facture")
    )
    member = models.ForeignKey(
        "members.Member",
        related_name="invoices",
        on_delete=models.PROTECT,
        verbose_name=_("usager"),
    )
    issue_date = models.DateField(default=date.today, verbose_name=_("date d'émission"))
    due_date = models.DateField(verbose_name=_("échéance"))
    status = models.CharField(
        max_length=15,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.OPEN,
        verbose_name=_("statut"),
    )
    # Stockés plutôt que recalculés : le total dû de toute la bibliothèque doit
    # s'agréger en une requête, pas en parcourant les lignes de chaque facture.
    total_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0"), verbose_name=_("total")
    )
    amount_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0"), verbose_name=_("réglé")
    )
    note = models.TextField(blank=True, verbose_name=_("note"))
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="invoices_created",
        verbose_name=_("émise par"),
    )
    emailed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("envoyée le"))
    reminder_sent_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("relancée le")
    )

    class Meta:
        verbose_name = _("facture")
        verbose_name_plural = _("factures")
        ordering = ["-issue_date", "-id"]
        indexes = [
            models.Index(fields=["status", "due_date"], name="invoice_status_due_idx"),
        ]

    def __str__(self) -> str:
        return self.number or f"#{self.pk}"

    def save(self, *args, **kwargs):
        if self.number:
            return super().save(*args, **kwargs)
        # SQLite ne sait pas verrouiller une ligne (`select_for_update` y lève
        # NotSupportedError) : deux créations concurrentes peuvent lire la même
        # séquence. C'est la contrainte d'unicité qui tranche, et on réessaie.
        for _attempt in range(5):
            try:
                with transaction.atomic():
                    self.number = allocate_invoice_number(self.issue_date)
                    return super().save(*args, **kwargs)
            except IntegrityError:
                self.number = ""
        raise IntegrityError("Impossible d'allouer un numéro de facture unique.")

    @property
    def balance(self) -> Decimal:
        if self.status == InvoiceStatus.CANCELLED:
            return Decimal("0")
        return self.total_amount - self.amount_paid

    @property
    def is_overdue(self) -> bool:
        return self.status == InvoiceStatus.OPEN and self.due_date < date.today()

    @property
    def days_overdue(self) -> int:
        return max(0, (date.today() - self.due_date).days)

    def recompute(self, save: bool = True) -> None:
        """Recalcule total et solde à partir des lignes et des paiements."""
        lines = self.lines.aggregate(
            total=Sum(F("amount") * F("quantity"), output_field=models.DecimalField())
        )
        paid = self.payments.aggregate(total=Sum("amount"))
        self.total_amount = lines["total"] or Decimal("0")
        self.amount_paid = paid["total"] or Decimal("0")
        if self.status != InvoiceStatus.CANCELLED:
            self.status = (
                InvoiceStatus.PAID
                if self.amount_paid >= self.total_amount
                else InvoiceStatus.OPEN
            )
        if save:
            self.save(update_fields=["total_amount", "amount_paid", "status"])


def allocate_invoice_number(issue_date: date) -> str:
    """`F-2026-0001`. Séquence par année, dans `Setting`.

    À appeler dans une transaction : deux créations simultanées prendraient
    sinon le même numéro, et `number` est unique — la seconde échouerait.
    """
    from apps.core.models import Setting

    year = issue_date.year
    key = f"invoice_seq_{year}"
    obj, _created = Setting.objects.get_or_create(
        pk=key, defaults={"value": 0, "description": f"Séquence de facture {year}"}
    )
    seq = int(obj.value or 0) + 1
    obj.value = seq
    obj.save(update_fields=["value", "updated_at"])
    return f"F-{year}-{seq:04d}"


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name="lines", on_delete=models.CASCADE
    )
    kind = models.CharField(
        max_length=20,
        choices=FeeKind.choices,
        default=FeeKind.OTHER,
        verbose_name=_("nature"),
    )
    label = models.CharField(max_length=200, verbose_name=_("libellé"))
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("montant unitaire")
    )
    quantity = models.PositiveSmallIntegerField(default=1, verbose_name=_("quantité"))

    class Meta:
        verbose_name = _("ligne de facture")
        verbose_name_plural = _("lignes de facture")
        ordering = ["id"]

    def __str__(self) -> str:
        return self.label

    @property
    def line_total(self) -> Decimal:
        return self.amount * self.quantity


class Payment(models.Model):
    invoice = models.ForeignKey(
        Invoice, related_name="payments", on_delete=models.PROTECT,
        verbose_name=_("facture"),
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("montant")
    )
    method = models.CharField(
        max_length=15,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
        verbose_name=_("mode de paiement"),
    )
    paid_on = models.DateField(default=date.today, verbose_name=_("date"))
    note = models.CharField(max_length=200, blank=True, verbose_name=_("note"))
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="payments_received",
        verbose_name=_("encaissé par"),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("paiement")
        verbose_name_plural = _("paiements")
        ordering = ["-paid_on", "-id"]

    def __str__(self) -> str:
        return f"{self.amount} · {self.invoice}"


class CashMovement(models.Model):
    """Registre de caisse. Une entrée par encaissement en espèces, plus les
    sorties saisies à la main (dépenses)."""

    occurred_on = models.DateField(default=date.today, verbose_name=_("date"))
    direction = models.CharField(
        max_length=5, choices=CashDirection.choices, verbose_name=_("sens")
    )
    amount = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("montant")
    )
    label = models.CharField(max_length=200, verbose_name=_("libellé"))
    payment = models.OneToOneField(
        Payment,
        null=True, blank=True, on_delete=models.CASCADE,
        related_name="cash_movement",
        verbose_name=_("paiement"),
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, on_delete=models.SET_NULL,
        related_name="cash_movements",
        verbose_name=_("saisi par"),
    )

    class Meta:
        verbose_name = _("mouvement de caisse")
        verbose_name_plural = _("mouvements de caisse")
        ordering = ["-occurred_on", "-id"]
        indexes = [
            models.Index(fields=["occurred_on"], name="cash_date_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.get_direction_display()} {self.amount} — {self.label}"

    @property
    def signed_amount(self) -> Decimal:
        return self.amount if self.direction == CashDirection.IN else -self.amount


class EmailStatus(models.TextChoices):
    PENDING = "pending", _("En attente")
    SENT = "sent", _("Envoyé")
    FAILED = "failed", _("Échec")


class EmailKind(models.TextChoices):
    INVOICE = "invoice", _("Facture")
    REMINDER = "reminder", _("Relance")


class OutboundEmail(models.Model):
    """File d'envoi. FEAT-084 / FEAT-086.

    Tout email passe par ici, y compris quand la Box est en ligne : c'est la
    seule façon de garantir qu'un envoi raté laisse une trace consultable
    plutôt qu'une exception dans un journal que personne ne lit.
    """

    kind = models.CharField(
        max_length=15, choices=EmailKind.choices, verbose_name=_("nature")
    )
    to_address = models.EmailField(verbose_name=_("destinataire"))
    subject = models.CharField(max_length=250, verbose_name=_("objet"))
    body = models.TextField(verbose_name=_("message"))
    invoice = models.ForeignKey(
        Invoice, null=True, blank=True, on_delete=models.CASCADE,
        related_name="emails", verbose_name=_("facture"),
    )
    status = models.CharField(
        max_length=10,
        choices=EmailStatus.choices,
        default=EmailStatus.PENDING,
        verbose_name=_("statut"),
    )
    error = models.TextField(blank=True, verbose_name=_("erreur"))
    attempts = models.PositiveSmallIntegerField(default=0, verbose_name=_("tentatives"))
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name=_("envoyé le"))

    class Meta:
        verbose_name = _("email en file")
        verbose_name_plural = _("emails en file")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} → {self.to_address}"
