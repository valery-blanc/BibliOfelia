"""Règles de caisse. FEAT-084.

Tout ce qui touche à l'argent passe par ici : les vues ne calculent pas de
montant elles-mêmes. C'est la même règle que `find_item` / `find_member` — une
règle appliquée à deux endroits finit par diverger.
"""
from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import ngettext

from .models import (
    CashDirection,
    CashMovement,
    EmailKind,
    EmailStatus,
    FeeKind,
    Invoice,
    InvoiceLine,
    InvoiceStatus,
    OutboundEmail,
    Payment,
    PaymentMethod,
)
from .money import config, format_amount

logger = logging.getLogger(__name__)

ZERO = Decimal("0")
# Une facture entre en relance **plus d'un jour** après l'échéance (demande Val
# : « 1j après leur date d'échéance »).
REMINDER_DELAY_DAYS = 1


# ----------------------------------------------------------------------
# Compte d'un usager
# ----------------------------------------------------------------------
@dataclass
class MemberAccount:
    """État du compte, tel qu'il s'affiche sur la fiche usager."""

    total_due: Decimal = ZERO
    overdue_due: Decimal = ZERO
    overdue_since: date | None = None
    next_due_date: date | None = None
    by_kind: dict = field(default_factory=dict)
    open_invoices: list = field(default_factory=list)

    @property
    def is_up_to_date(self) -> bool:
        return self.total_due <= ZERO

    @property
    def is_overdue(self) -> bool:
        return self.overdue_due > ZERO


def member_account(member) -> MemberAccount:
    invoices = list(
        Invoice.objects.filter(member=member, status=InvoiceStatus.OPEN)
        .prefetch_related("lines")
        .order_by("due_date")
    )
    account = MemberAccount(open_invoices=invoices)
    today = date.today()
    for invoice in invoices:
        balance = invoice.balance
        if balance <= ZERO:
            continue
        account.total_due += balance
        if invoice.due_date < today:
            account.overdue_due += balance
            if account.overdue_since is None or invoice.due_date < account.overdue_since:
                account.overdue_since = invoice.due_date
        elif account.next_due_date is None or invoice.due_date < account.next_due_date:
            account.next_due_date = invoice.due_date
        # Le détail « cotisation / amendes » demandé par Val : la ventilation se
        # fait sur les lignes, pas sur la facture — une même facture peut porter
        # une cotisation et une amende.
        for line in invoice.lines.all():
            account.by_kind[line.kind] = (
                account.by_kind.get(line.kind, ZERO) + line.line_total
            )
    return account


def members_with_overdue_balance():
    """Usagers ayant au moins une facture échue impayée."""
    from apps.members.models import Member

    return (
        Member.objects.filter(
            invoices__status=InvoiceStatus.OPEN,
            invoices__due_date__lt=date.today(),
        )
        .distinct()
        .order_by("last_name", "first_name")
    )


# ----------------------------------------------------------------------
# Émission de factures
# ----------------------------------------------------------------------
def default_due_date(issue_date: date | None = None) -> date:
    issue_date = issue_date or date.today()
    return issue_date + timedelta(days=config()["payment_terms_days"])


@transaction.atomic
def create_invoice(member, lines, *, issue_date=None, due_date=None, user=None,
                   note: str = "") -> Invoice:
    """Crée une facture et ses lignes. `lines` = itérable de dicts
    `{kind, label, amount, quantity}`."""
    issue_date = issue_date or date.today()
    invoice = Invoice(
        member=member,
        issue_date=issue_date,
        due_date=due_date or default_due_date(issue_date),
        created_by=user,
        note=note,
    )
    invoice.save()
    for line in lines:
        InvoiceLine.objects.create(
            invoice=invoice,
            kind=line.get("kind", FeeKind.OTHER),
            label=line["label"],
            amount=Decimal(line["amount"]),
            quantity=int(line.get("quantity") or 1),
        )
    invoice.recompute()
    return invoice


def create_membership_invoice(member, *, user=None, issue_date=None) -> Invoice | None:
    """Facture de cotisation, à l'inscription et à chaque renouvellement.

    Décision Val (2026-08-31) : le montant vient de la **catégorie** de
    l'usager. Un montant nul n'émet rien — une bibliothèque gratuite ne doit
    pas crouler sous des factures à zéro.
    """
    category = member.category
    fee = getattr(category, "membership_fee", ZERO) or ZERO
    if fee <= ZERO:
        return None
    issue_date = issue_date or date.today()
    label = _("Cotisation %(cat)s — %(year)s") % {
        "cat": category.name,
        "year": issue_date.year,
    }
    return create_invoice(
        member,
        [{"kind": FeeKind.MEMBERSHIP, "label": label, "amount": fee, "quantity": 1}],
        issue_date=issue_date,
        user=user,
    )


def _unpaid_membership_only_invoices(member):
    """Factures ouvertes qui ne portent qu'une cotisation, encore intactes.

    Une facture déjà encaissée (même partiellement) ou qui mélange cotisation
    et amende n'est pas un levier : l'annuler ferait disparaître autre chose
    que la cotisation de l'ancienne catégorie.
    """
    invoices = (
        Invoice.objects.filter(member=member, status=InvoiceStatus.OPEN)
        .prefetch_related("lines", "payments")
    )
    kept = []
    for invoice in invoices:
        lines = list(invoice.lines.all())
        if not lines or any(line.kind != FeeKind.MEMBERSHIP for line in lines):
            continue
        if invoice.payments.exists():
            continue
        kept.append(invoice)
    return kept


@transaction.atomic
def reconcile_membership_invoices(member, *, user=None, emit_new: bool = True,
                                  reason: str = "") -> dict:
    """Aligne les factures de cotisation ouvertes sur la catégorie actuelle.

    BUG-042 : changer un usager d'Adulte (20 CHF) à Employé (0) laissait la
    facture d'Adulte ouverte, et l'encadré Compte continuait d'afficher
    « Cotisation 20 CHF ».
    """
    fee = getattr(member.category, "membership_fee", ZERO) or ZERO
    open_ones = _unpaid_membership_only_invoices(member)
    outstanding = sum((invoice.total_amount for invoice in open_ones), ZERO)

    if emit_new and fee > ZERO and outstanding == fee and len(open_ones) == 1:
        return {"cancelled": [], "created": None}

    cancelled = []
    note = reason or _("Changement de catégorie : cotisation recalculée.")
    if fee <= ZERO:
        note = reason or _("Changement de catégorie : plus de cotisation.")
    for invoice in open_ones:
        cancel_invoice(invoice, reason=note)
        cancelled.append(invoice)

    created = None
    if emit_new and fee > ZERO:
        created = create_membership_invoice(member, user=user)
    return {"cancelled": cancelled, "created": created}


@transaction.atomic
def cancel_invoice(invoice: Invoice, *, reason: str = "") -> Invoice:
    """Annule au lieu de supprimer : une numérotation trouée n'est plus un
    registre de caisse."""
    invoice.status = InvoiceStatus.CANCELLED
    if reason:
        invoice.note = (invoice.note + "\n" if invoice.note else "") + reason
    invoice.save(update_fields=["status", "note"])
    return invoice


# ----------------------------------------------------------------------
# Encaissement
# ----------------------------------------------------------------------
@transaction.atomic
def register_payment(invoice: Invoice, amount, *, method=PaymentMethod.CASH,
                     paid_on=None, note: str = "", user=None) -> Payment:
    """Encaisse `amount` sur `invoice`. Un règlement **en espèces** crée aussi
    une entrée de caisse — c'est ce qui fait tenir le registre."""
    payment = Payment.objects.create(
        invoice=invoice,
        amount=Decimal(amount),
        method=method,
        paid_on=paid_on or date.today(),
        note=note,
        received_by=user,
    )
    if method == PaymentMethod.CASH:
        CashMovement.objects.create(
            occurred_on=payment.paid_on,
            direction=CashDirection.IN,
            amount=payment.amount,
            label=_("Facture %(num)s — %(member)s") % {
                "num": invoice.number,
                "member": invoice.member.full_name,
            },
            payment=payment,
            created_by=user,
        )
    invoice.recompute()
    return payment


# ----------------------------------------------------------------------
# État de la caisse
# ----------------------------------------------------------------------
@dataclass
class CashSummary:
    start: date
    end: date
    total_in: Decimal = ZERO
    total_out: Decimal = ZERO
    movements: list = field(default_factory=list)

    @property
    def balance(self) -> Decimal:
        return self.total_in - self.total_out


def cash_summary(start: date, end: date) -> CashSummary:
    movements = list(
        CashMovement.objects.filter(occurred_on__gte=start, occurred_on__lte=end)
        .select_related("payment__invoice__member", "created_by")
        .order_by("-occurred_on", "-id")
    )
    totals = CashMovement.objects.filter(
        occurred_on__gte=start, occurred_on__lte=end
    ).values("direction").annotate(total=Sum("amount"))
    summary = CashSummary(start=start, end=end, movements=movements)
    for row in totals:
        if row["direction"] == CashDirection.IN:
            summary.total_in = row["total"] or ZERO
        else:
            summary.total_out = row["total"] or ZERO
    return summary


def total_outstanding() -> Decimal:
    """Total dû par l'ensemble des usagers."""
    rows = Invoice.objects.filter(status=InvoiceStatus.OPEN).aggregate(
        total=Sum("total_amount"), paid=Sum("amount_paid")
    )
    return (rows["total"] or ZERO) - (rows["paid"] or ZERO)


def cash_balance_all_time() -> Decimal:
    rows = CashMovement.objects.values("direction").annotate(total=Sum("amount"))
    balance = ZERO
    for row in rows:
        if row["direction"] == CashDirection.IN:
            balance += row["total"] or ZERO
        else:
            balance -= row["total"] or ZERO
    return balance


# ----------------------------------------------------------------------
# Emails : file d'attente, envoi, relances
# ----------------------------------------------------------------------
def email_config() -> dict:
    from apps.core.models import Setting

    data = Setting.get("email_config", {}) or {}
    return {
        "enabled": bool(data.get("enabled")),
        "host": data.get("host", ""),
        "port": int(data.get("port") or 587),
        "user": data.get("user", ""),
        "password": data.get("password", ""),
        "use_tls": bool(data.get("use_tls", True)),
        "from_address": data.get("from_address", ""),
    }


_ONLINE_CACHE: dict = {"at": 0.0, "value": False}
_ONLINE_TTL_SECONDS = 60


def smtp_configured() -> bool:
    cfg = email_config()
    return bool(cfg["enabled"] and cfg["host"])


def running_on_the_box() -> bool:
    from apps.closing.services import is_box

    return is_box()


def email_ui_context() -> dict:
    """Drapeaux d'écran pour la file, la caisse et le bouclement. BUG-043."""
    return {
        "is_online": is_online(),
        "is_box": running_on_the_box(),
        "smtp_configured": smtp_configured(),
        "can_send_email": can_send_email(),
    }


def can_send_email(force: bool = False) -> bool:
    """Peut-on tenter un envoi SMTP maintenant ? BUG-043.

    Une instance hébergée (Grand-Saconnex, Sanjuan) est en ligne par
    construction : dès que le relais est configuré, on envoie. La file
    d'attente « Box hors ligne » n'existe que sur la Ofelia Box.
    """
    if not smtp_configured():
        return False
    if not running_on_the_box():
        return True
    return is_online(force=force)


def is_online(force: bool = False) -> bool:
    """Le relais SMTP répond-il ? Pertinent **sur la Box**.

    Une Box qui voit Internet mais pas son relais n'enverra rien. Le résultat
    est gardé une minute — l'écran de bouclement le consulte plusieurs fois
    d'affilée, et ouvrir une socket à chaque fois ferait ramer la page hors
    ligne.
    """
    cfg = email_config()
    if not (cfg["enabled"] and cfg["host"]):
        return False
    now = time.monotonic()
    if not force and now - _ONLINE_CACHE["at"] < _ONLINE_TTL_SECONDS:
        return bool(_ONLINE_CACHE["value"])
    try:
        with socket.create_connection((cfg["host"], cfg["port"]), timeout=3):
            value = True
    except OSError:
        value = False
    _ONLINE_CACHE.update({"at": now, "value": value})
    return value


def queue_invoice_email(invoice: Invoice, *, kind=EmailKind.INVOICE) -> OutboundEmail | None:
    """Met une facture (ou sa relance) en file. Renvoie None sans email."""
    address = (invoice.member.email or "").strip()
    if not address:
        return None
    library = _library_name()
    if kind == EmailKind.REMINDER:
        subject = _("Rappel — facture %(num)s") % {"num": invoice.number}
        body = _(
            "Bonjour %(name)s,\n\n"
            "La facture %(num)s d'un montant de %(amount)s, échue le %(due)s, "
            "n'a pas encore été réglée.\n"
            "Merci de passer à la bibliothèque pour la régler.\n\n"
            "%(library)s"
        ) % {
            "name": invoice.member.full_name,
            "num": invoice.number,
            "amount": format_amount(invoice.balance),
            "due": invoice.due_date.isoformat(),
            "library": library,
        }
    else:
        subject = _("Facture %(num)s") % {"num": invoice.number}
        body = _(
            "Bonjour %(name)s,\n\n"
            "Vous trouverez ci-joint la facture %(num)s d'un montant de "
            "%(amount)s, à régler avant le %(due)s.\n\n"
            "%(library)s"
        ) % {
            "name": invoice.member.full_name,
            "num": invoice.number,
            "amount": format_amount(invoice.total_amount),
            "due": invoice.due_date.isoformat(),
            "library": library,
        }
    return OutboundEmail.objects.create(
        kind=kind,
        to_address=address,
        subject=subject,
        body=body,
        invoice=invoice,
    )


def _library_name() -> str:
    from apps.core.models import Setting

    return Setting.get("library_name", "BibliOfelia") or "BibliOfelia"


def invoices_to_send():
    """Factures ouvertes jamais envoyées, dont l'usager a un email."""
    return (
        Invoice.objects.filter(status=InvoiceStatus.OPEN, emailed_at__isnull=True)
        .exclude(member__email="")
        .select_related("member")
        .order_by("issue_date")
    )


def reminders_to_send():
    """Factures échues depuis plus d'un jour et jamais relancées."""
    cutoff = date.today() - timedelta(days=REMINDER_DELAY_DAYS)
    return (
        Invoice.objects.filter(
            status=InvoiceStatus.OPEN,
            due_date__lt=cutoff,
            reminder_sent_at__isnull=True,
        )
        .exclude(member__email="")
        .select_related("member")
        .order_by("due_date")
    )


def queue_pending_invoice_emails() -> dict:
    """Met en file tout ce qui doit partir. Renvoie les compteurs."""
    queued_invoices = 0
    queued_reminders = 0
    now = timezone.now()
    for invoice in invoices_to_send():
        if queue_invoice_email(invoice, kind=EmailKind.INVOICE):
            Invoice.objects.filter(pk=invoice.pk).update(emailed_at=now)
            queued_invoices += 1
    for invoice in reminders_to_send():
        if queue_invoice_email(invoice, kind=EmailKind.REMINDER):
            Invoice.objects.filter(pk=invoice.pk).update(reminder_sent_at=now)
            queued_reminders += 1
    return {"invoices": queued_invoices, "reminders": queued_reminders}


def pending_emails():
    return OutboundEmail.objects.filter(
        status__in=(EmailStatus.PENDING, EmailStatus.FAILED)
    ).select_related("invoice__member")


def flush_outbox(limit: int = 50) -> dict:
    """Tente de vider la file. Ne lève jamais : un envoi raté reste en file
    avec son message d'erreur, visible à l'écran."""
    from django.core.mail import EmailMessage, get_connection

    cfg = email_config()
    result = {"sent": 0, "failed": 0, "skipped": 0, "skip_reason": ""}
    queue = list(pending_emails().order_by("created_at")[:limit])
    if not queue:
        return result
    if not smtp_configured():
        result["skipped"] = len(queue)
        result["skip_reason"] = "not_configured"
        return result
    if running_on_the_box() and not is_online(force=True):
        result["skipped"] = len(queue)
        result["skip_reason"] = "offline"
        return result
    try:
        connection = get_connection(
            backend="django.core.mail.backends.smtp.EmailBackend",
            host=cfg["host"], port=cfg["port"], username=cfg["user"],
            password=cfg["password"], use_tls=cfg["use_tls"], fail_silently=False,
        )
    except Exception as exc:  # pragma: no cover — configuration invalide
        logger.warning("SMTP inutilisable : %s", exc)
        result["skipped"] = len(queue)
        result["skip_reason"] = "not_configured"
        return result

    from .pdf import render_invoice_pdf

    for item in queue:
        try:
            message = EmailMessage(
                subject=item.subject,
                body=item.body,
                from_email=cfg["from_address"] or None,
                to=[item.to_address],
                connection=connection,
            )
            if item.invoice_id and item.kind == EmailKind.INVOICE:
                message.attach(
                    f"{item.invoice.number}.pdf",
                    render_invoice_pdf(item.invoice),
                    "application/pdf",
                )
            message.send()
            item.status = EmailStatus.SENT
            item.sent_at = timezone.now()
            item.error = ""
            result["sent"] += 1
        except Exception as exc:
            item.status = EmailStatus.FAILED
            item.error = str(exc)[:2000]
            result["failed"] += 1
        item.attempts += 1
        item.save(update_fields=["status", "sent_at", "error", "attempts"])
    return result


def flush_user_messages(result: dict) -> list[tuple[str, str]]:
    """Messages d'interface après un `flush_outbox`. BUG-043 : jamais « Box »
    sur une instance hébergée."""
    notes: list[tuple[str, str]] = []
    sent = result.get("sent") or 0
    failed = result.get("failed") or 0
    skipped = result.get("skipped") or 0
    reason = result.get("skip_reason") or ""
    if sent:
        notes.append((
            "success",
            ngettext(
                "%(n)s email envoyé.",
                "%(n)s emails envoyés.",
                sent,
            )
            % {"n": sent},
        ))
    if failed:
        notes.append((
            "error",
            ngettext(
                "%(n)s échec d'envoi.",
                "%(n)s échecs d'envoi.",
                failed,
            )
            % {"n": failed},
        ))
    if skipped:
        if reason == "not_configured":
            notes.append((
                "warning",
                ngettext(
                    "%(n)s email reste en file : l'envoi n'est pas configuré "
                    "(Avancé → Paramètres → Email).",
                    "%(n)s emails restent en file : l'envoi n'est pas configuré "
                    "(Avancé → Paramètres → Email).",
                    skipped,
                )
                % {"n": skipped},
            ))
        elif reason == "offline":
            notes.append((
                "warning",
                ngettext(
                    "%(n)s email reste en file : la Box n'est pas en ligne. "
                    "Prévenez la personne par téléphone, ou renvoyez quand "
                    "la Box le sera.",
                    "%(n)s emails restent en file : la Box n'est pas en ligne. "
                    "Prévenez les personnes par téléphone, ou renvoyez quand "
                    "la Box le sera.",
                    skipped,
                )
                % {"n": skipped},
            ))
        else:
            notes.append((
                "warning",
                ngettext(
                    "%(n)s email laissé en file.",
                    "%(n)s emails laissés en file.",
                    skipped,
                )
                % {"n": skipped},
            ))
    if not notes:
        notes.append(("info", _("Aucun email en attente.")))
    return notes
